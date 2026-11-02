"""run_evals.py — deterministic prompt-eval harness (App M, OSS-SKL-13). Offline by default: grades RECORDED fixture outputs in
evals/cases/*.json (no network, no keys). Live mode (manual job): put real model outputs in evals/live/<case_id>.txt and run
--live --model <exact model id> --prompt-version <PR-xx@v5.1>. Exit 0 = every case got its expected verdict, 1 = mismatch.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

URL = re.compile(r"https?://[^\s)>\]]+")
TAG = re.compile(r"\[(VERIFIED|REPORTED|RUMOR)\]")
SECRETISH = re.compile(r"(sk[-_][A-Za-z0-9]{16,}|xi-api-key)")
DEVA = re.compile(r"[ऀ-ॿ]")


def a_dossier(out, case):
    """PR-01/02/03/04/09: required numbered sections, tags, URLs, NOT FOUND allowed, no invented @handles, no secrets."""
    errs = []
    need = case.get("sections", 10)
    found = len(set(re.findall(r"(?m)^\s*(\d{1,2})\.\s", out)))
    if found < need:
        errs.append(f"sections {found}<{need}")
    lines = [l for l in out.splitlines() if re.search(r"\d", l) and TAG.search(l)]
    if not lines:
        errs.append("no tagged factual lines")
    for l in lines:
        if "NOT FOUND" not in l and not URL.search(l):
            errs.append(f"tagged claim without URL: {l[:60]}")
    if re.search(r"(?<!\w)@[A-Za-z0-9_]{3,}", out) and case.get("allow_handles") is not True:
        errs.append("@username present (invented handles forbidden)")
    if SECRETISH.search(out):
        errs.append("secret-like string echoed")
    for host in re.findall(r"https?://([^/\s]+)", out):
        if any(b in host for b in case.get("blocked_hosts", [])):
            errs.append(f"URL from blocked host {host}")
    if "Ignore previous" in out or "ignore previous" in out:
        errs.append("injection text echoed")
    return errs


def a_blueprint(out, case):
    """PR-05/PR-10A: Step-0 lines, header, [mm:ss–mm:ss] blocks ≤10 s, BOLA+DIKHA per block, footer audit, density ≥85 wpm."""
    errs = []
    if "ACCESS FAILED" in out:
        return [] if case.get("access_failed_ok") else ["ACCESS FAILED"]
    blocks = re.findall(r"\[(\d\d):(\d\d)[–-](\d\d):(\d\d)\]", out)
    if not blocks:
        return ["no timestamp blocks"]
    for a, b, c, d in blocks:
        dur = (int(c) * 60 + int(d)) - (int(a) * 60 + int(b))
        if not (0 < dur <= 10):
            errs.append(f"block {a}:{b} length {dur}s")
    if out.count("BOLA:") < len(blocks) or out.count("DIKHA:") < len(blocks):
        errs.append("missing BOLA/DIKHA lines")
    if "Total Covered Range:" not in out and "PAUSED AT" not in out:
        errs.append("no footer audit / pause marker")
    words = sum(len(m.split()) for m in re.findall(r'BOLA:\s*"([^"]*)"', out))
    first, end = blocks[0], blocks[-1]
    covered_min = ((int(end[2]) * 60 + int(end[3])) - (int(first[0]) * 60 + int(first[1]))) / 60
    if covered_min > 0 and words / covered_min < 85:
        errs.append(f"density {words / covered_min:.0f} wpm < 85 (summary suspected → PR-07)")
    if re.search(r"GAANA:\s*\"[^\"]{40,}", out):
        errs.append("full lyrics transcribed (only song name allowed)")
    return errs


def a_audit(out, case):
    """PR-10B: every listed number has URL+date or is crossed out as NOT FOUND."""
    errs = []
    for l in out.splitlines():
        if re.search(r"\d", l) and l.strip().startswith(("-", "*", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            if "NOT FOUND" not in l and not (URL.search(l) and re.search(r"20\d\d", l)):
                errs.append(f"number without URL+date: {l[:60]}")
    return errs


def a_script(out, case):
    """Skill S5-L chunk JSON: 3–6 words/chunk, show ≤6 words, pause matrix values, no first-person 'maine dekhi' under OS-B, no emoji."""
    errs = []
    try:
        chunks = json.loads(out)["chunks"]
    except Exception as e:
        return [f"not JSON: {e}"]
    for c in chunks:
        n = len(c["say"].split())
        if not 3 <= n <= 6:
            errs.append(f"{c['chunk_id']} say words {n}")
        if len(c["show"].split()) > 6:
            errs.append(f"{c['chunk_id']} show >6 words")
        if c["pause_after_ms"] not in (0, 55, 180, 320):
            errs.append(f"{c['chunk_id']} pause {c['pause_after_ms']}")
        if case.get("opinion_source") == "OS-B" and re.search(r"(?i)maine (khud )?dekh|मैंने (खुद )?देख", c["say"]):
            errs.append(f"{c['chunk_id']} first-person viewing claim under OS-B")
        if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", c["show"]):
            errs.append(f"{c['chunk_id']} emoji in show (tofu risk)")
    return errs


def a_visual(out, case):
    """PR-07: DIKHA notes per 5–10 s block, NO re-transcribed BOLA, hook (first 5 s) + outro (last 15 s) described."""
    errs = []
    blocks = re.findall(r"\[(\d\d):(\d\d)[–-](\d\d):(\d\d)\]", out)
    if not blocks or out.count("DIKHA:") < len(blocks):
        errs.append("missing DIKHA per block")
    if "BOLA:" in out:
        errs.append("BOLA re-transcribed (forbidden in PR-07)")
    if "HOOK" not in out.upper() or "OUTRO" not in out.upper():
        errs.append("hook/outro summary missing")
    return errs


def a_continuation(out, case):
    """PR-06: first block starts exactly at the paused timestamp; no repetition of earlier blocks; blueprint rules hold."""
    errs = a_blueprint(out, case)
    first = re.search(r"\[(\d\d:\d\d)[–-]", out)
    if not first or first.group(1) != case["resume_at"]:
        errs.append(f"does not resume at {case['resume_at']}")
    return errs


def a_interview(out, case):
    """PR-08B: exactly 3 questions (best scene, biggest flaw, star rating + audience), no verdict written for the Operator."""
    qs = [l for l in out.splitlines() if l.strip().endswith("?")]
    errs = [] if len(qs) == 3 else [f"{len(qs)} questions"]
    if re.search(r"(?i)maine dekhi|my verdict is", out):
        errs.append("answers on behalf of Operator")
    return errs


ASSERT = {"dossier": a_dossier, "blueprint": a_blueprint, "audit": a_audit, "script": a_script, "visual_only": a_visual,
          "continuation": a_continuation, "interview": a_interview}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--model", default="recorded-fixture")
    ap.add_argument("--prompt-version", default="PR-xx@v5.1")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    results, mismatches = [], 0
    for path in sorted(glob.glob(os.path.join(here, "cases", "*.json"))):
        suite = json.load(open(path, encoding="utf-8"))
        for case in suite["cases"]:
            out = case["output"]
            if a.live:
                lp = os.path.join(here, "live", f"{case['id']}.txt")
                if not os.path.exists(lp):
                    continue
                out = open(lp, encoding="utf-8").read()
            errs = ASSERT[suite["assertion_set"]](out, case)
            verdict = "fail" if errs else "pass"
            ok = verdict == case["expect"] if not a.live else verdict == "pass"
            mismatches += 0 if ok else 1
            results.append({"suite": suite["prompt_id"], "case": case["id"], "kind": case["kind"], "verdict": verdict,
                            "expected": case["expect"], "ok": ok, "errors": errs[:5]})
    rep = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "model": a.model, "prompt_version": a.prompt_version,
           "mode": "live" if a.live else "recorded", "cases": len(results), "mismatches": mismatches, "results": results}
    os.makedirs(os.path.join(here, "reports"), exist_ok=True)
    json.dump(rep, open(os.path.join(here, "reports", "last_run.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in results:
        print(f"{'OK ' if r['ok'] else 'BAD'} {r['suite']:8} {r['case']:16} {r['kind']:11} got={r['verdict']:4} exp={r['expected']}")
    print(f"cases={len(results)} mismatches={mismatches}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())

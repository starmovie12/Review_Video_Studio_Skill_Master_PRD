"""similarity_check.py — S3 sanitizer + S5-L/S13 originality guard (File 21, PRD v5.1 App G.6, OSS-SKL-08).
Exact ≥7-gram (raw + Devanagari↔Roman phonetic skeleton) = HARD FAIL (RVS_ERR_080, exit 60). 5–6-gram exact or RapidFuzz
fuzz.ratio ≥ 90 on 7-gram windows (optional rapidfuzz/RapidFuzz) = warning (RVS_WARN_081).
CLI: python scripts/similarity_check.py --script script_say_show.txt --transcripts DIR [--json out.json]
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvs_common import RvsError, log_event, main_wrapper, warn  # noqa: E402

DEVA_TO_ROMAN_MAP = {
    "अ": "a", "आ": "a", "इ": "i", "ई": "i", "उ": "u", "ऊ": "u", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v",
    "श": "sh", "ष": "sh", "स": "s", "ह": "h", "ड़": "r", "ढ़": "rh", "ज़": "z", "फ़": "f",
    "ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    "ं": "n", "ँ": "n", "्": "", "ृ": "ri",
}

def strip_lyrics_and_sponsors(raw_transcript: str) -> str:
    """Removes [GAANA ...]/[SPONSOR_AD ...] blocks (nested [unclear mm:ss] allowed) AND whole 'GAANA/SFX:' lines (PR-05 format)."""
    pattern = r"\[(?:GAANA|SPONSOR_AD)(?:[^\[\]]|\[[^\]]*\])*\]"
    out, n1 = re.subn(pattern, " ", raw_transcript, flags=re.IGNORECASE | re.DOTALL)
    out, n2 = re.subn(r"(?im)^\s*GAANA\s*/\s*SFX\s*:.*$", " ", out)
    if n1 or n2:
        warn("RVS_WARN_085", "S3", f"stripped {n1} tagged blocks + {n2} GAANA/SFX lines")
    return out

INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+|any\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|rules|prompts?)[^\n]*",
    r"disregard\s+(?:all\s+|the\s+)?(?:previous|prior|above)[^\n]*",
    r"(?:^|\n)\s*(?:system|assistant)\s*:\s*[^\n]*",
    r"you\s+are\s+now\s+[^\n]*",
    r"new\s+instructions?\s*:[^\n]*",
    r"</?\s*untrusted_evidence\s*>",
]


def sanitize_untrusted_text(raw_text: str) -> str:
    """Defence-in-depth only (D-144): the PRIMARY control is that untrusted text is wrapped in <untrusted_evidence> and is
    never followed as instructions. Removes common override phrases and escapes ASS braces before captions."""
    cleaned, hits = raw_text, 0
    for p in INJECTION_PATTERNS:
        cleaned, n = re.subn(p, " ", cleaned, flags=re.IGNORECASE)
        hits += n
    if hits:
        warn("RVS_WARN_084", "S3", f"{hits} instruction-like phrases removed from untrusted input")
    return cleaned.replace("{", r"\{").replace("}", r"\}")


def wrap_untrusted(source: str, text: str) -> str:
    return f'<untrusted_evidence source="{source}">\n{sanitize_untrusted_text(text)}\n</untrusted_evidence>'


def tokenize_norm(text: str) -> list[str]:
    cleaned = re.sub(r"[^\w\u0900-\u097F]+", " ", text.lower())
    return [w for w in cleaned.split() if len(w) >= 1]

def to_phonetic_skeleton(token: str) -> str:
    """Maps both Devanagari and Roman Hinglish tokens into a shared consonant-skeleton ASCII representation."""
    if re.search(r"[\u0900-\u097F]", token):
        roman = "".join(DEVA_TO_ROMAN_MAP.get(ch, "") for ch in token)
    else:
        roman = token.lower()
    roman = (
        roman.replace("tion", "shn")
        .replace("sion", "shn")
        .replace("chh", "ch")
        .replace("w", "v")
        .replace("f", "ph")
        .replace("z", "j")
        .replace("q", "k")
        .replace("c", "k")
    )
    # Normalize any leading vowel cluster to "a", strip non-initial vowels, and collapse duplicate consonants
    roman = re.sub(r"^[aeiou]+", "a", roman)
    if len(roman) > 1:
        roman = roman[0] + re.sub(r"[aeiou]+", "", roman[1:])
    roman = re.sub(r"(.)\1+", r"\1", roman)
    return roman or token

def check_ngram_overlap(script_text: str, transcripts: dict[str, str], fail_n: int = 7, warn_n: int = 5) -> dict:
    """Checks script against all benchmark transcripts in both raw and cross-script phonetic token spaces."""
    s_raw = tokenize_norm(script_text)
    s_phon = [to_phonetic_skeleton(t) for t in s_raw]
    fails, warnings = [], []

    for t_name, raw_t in transcripts.items():
        t_raw = tokenize_norm(strip_lyrics_and_sponsors(raw_t))
        t_phon = [to_phonetic_skeleton(t) for t in t_raw]

        raw_fail_set = {" ".join(t_raw[i:i + fail_n]) for i in range(max(0, len(t_raw) - fail_n + 1))}
        phon_fail_set = {" ".join(t_phon[i:i + fail_n]) for i in range(max(0, len(t_phon) - fail_n + 1))}
        raw_warn_set = {" ".join(t_raw[i:i + warn_n]) for i in range(max(0, len(t_raw) - warn_n + 1))}

        for i in range(max(0, len(s_raw) - fail_n + 1)):
            g_raw = " ".join(s_raw[i:i + fail_n])
            g_phon = " ".join(s_phon[i:i + fail_n])
            if g_raw in raw_fail_set or (len(g_phon.replace(" ", "")) >= 8 and g_phon in phon_fail_set):
                fails.append({"transcript": t_name, "match": g_raw, "phonetic": g_phon, "length": fail_n})
        for i in range(max(0, len(s_raw) - warn_n + 1)):
            g5 = " ".join(s_raw[i:i + warn_n])
            if g5 in raw_warn_set:
                warnings.append({"transcript": t_name, "match": g5, "length": warn_n})
        try:  # optional fuzzy tier (rapidfuzz/RapidFuzz, MIT): near-copies with small edits
            from rapidfuzz import fuzz, process
            t7 = list(raw_fail_set)
            for i in range(0, max(0, len(s_raw) - fail_n + 1)):
                g = " ".join(s_raw[i:i + fail_n])
                if t7 and g not in raw_fail_set:
                    best = process.extractOne(g, t7, scorer=fuzz.ratio, score_cutoff=90)
                    if best:
                        warnings.append({"transcript": t_name, "match": g, "near": best[0], "score": round(best[1], 1), "length": fail_n})
        except ImportError:
            pass

    return {"passed": len(fails) == 0, "hard_fails": fails, "warnings": warnings[:10]}


def main():
    ap = argparse.ArgumentParser(description="originality guard")
    ap.add_argument("--script", required=True, help="text file with all say+show lines")
    ap.add_argument("--transcripts", required=True, help="directory of benchmark transcript .txt files")
    ap.add_argument("--json", default=None)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    script = open(a.script, encoding="utf-8").read()
    trs = {os.path.basename(p): open(p, encoding="utf-8").read() for p in sorted(glob.glob(os.path.join(a.transcripts, "*.txt")))}
    res = check_ngram_overlap(script, trs)
    if a.json:
        json.dump(res, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if res["warnings"]:
        warn("RVS_WARN_081", "S5-L", f"{len(res['warnings'])} near/partial matches")
    if not res["passed"]:
        raise RvsError("RVS_ERR_080", "; ".join(f"{f['transcript']}: '{f['match']}'" for f in res["hard_fails"][:5]))
    log_event("INFO", "S5-L", "originality_ok", None, f"{len(trs)} transcripts checked")
    return None


if __name__ == "__main__":
    sys.exit(main_wrapper(main, "S5-L"))

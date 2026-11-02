#!/usr/bin/env python3
"""edit.py — apply exact-once targeted replacements to PRD_UPDATED.md, then run integrity and append patches.log.
Usage (as module): from edit import apply; apply(batch_name, [(old, new, "D-001,DEC-02"), ...], allow_multi=set())"""
import datetime, hashlib, os, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
PRD = os.path.join(ROOT, 'PRD_UPDATED.md')
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'patches.log')


def apply(batch, edits, allow_multi=()):
    text = open(PRD, encoding='utf-8').read()
    for i, (old, new, ids) in enumerate(edits):
        n = text.count(old)
        if n == 0 or (n > 1 and i not in allow_multi):
            raise SystemExit(f'[{batch}] edit #{i} ({ids}) matched {n} times: {old[:90]!r}')
        text = text.replace(old, new) if i in allow_multi else text.replace(old, new, 1)
    open(PRD, 'w', encoding='utf-8').write(text)
    h = hashlib.sha256(text.encode('utf-8')).hexdigest()
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'integrity.py'), PRD, '--quiet'], capture_output=True, text=True)
    ids = sorted({x.strip() for _, _, s in edits for x in s.split(',') if x.strip()})
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')} | {batch} | edits={len(edits)} | ids={','.join(ids)} | sha256={h[:16]} | {r.stdout.strip()}\n")
    print(r.stdout.strip())
    return h


def replace_block_after_heading(heading_substr, new_code, lang, ids, batch):
    """Replace the first fenced code block after the heading containing heading_substr."""
    text = open(PRD, encoding='utf-8').read()
    hi = text.index(heading_substr)
    fence = '```' + lang
    s = text.index(fence, hi)
    e = text.index('\n```', s + len(fence)) + 4
    old = text[s:e]
    apply(batch, [(old, f'```{lang}\n{new_code.rstrip()}\n```', ids)])

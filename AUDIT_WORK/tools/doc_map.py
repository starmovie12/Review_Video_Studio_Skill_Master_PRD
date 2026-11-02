#!/usr/bin/env python3
"""doc_map: headings, ID families, tables, code blocks. Usage: doc_map.py FILE [--out doc_map.md]"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import mdlib

path = sys.argv[1]
out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
_, text, L = mdlib.load(path)
blocks, inf, unb = mdlib.scan(L)
hs = mdlib.headings(L, inf)
tbs = mdlib.tables(L, inf)
ID_PATTERNS = {
    'S-stage': r'\bS(?:1[0-3]|[0-9])(?:-[A-C])?\b',
    'TC': r'\bTC-\d{2,3}\b', 'PR': r'\bPR-\d{2}[A-Z]?\b', 'TPL': r'\bTPL-\d{2}\b',
    'D-locked': r'(?<![\w-])D\d{1,2}(?![\w-])', 'Q': r'(?<![\w-])Q\d(?![\w-])', 'R-risk': r'(?<![\w-])R\d{1,2}(?![\w.-])',
    'RP': r'\bRP-\d\b', 'OSS-SKL': r'\bOSS-SKL-\d{2}\b', 'DEF': r'\bDEF-\d{2}\b', 'CAT': r'\bCAT-[A-Z]+\b',
    'MODE': r'\bMODE-[A-Z]+\b', 'OS': r'\bOS-[ABC]\b', 'HK': r'\bHK-[A-Z0-9]+\b', 'STL': r'\bSTL-[A-Z0-9]+\b',
    'CHK': r'\bCHK-\d{2}\b', 'CH': r'\bCH-\d{2}\b', 'AST': r'\bAST-[A-Z]\d\b', 'M-roadmap': r'(?<![\w-])M[0-4](?![\w-])',
    'STAGE': r'\bSTAGE-\d[A-Z]?\b', 'EC-edge': r'\bEC-\d{2}\b', 'E-audit': r'\b[A-E]-\d{2}\b', 'CN': r'\bCN-\d{3}\b',
    'RVS-ERR': r'\bRVS_(?:ERR|WARN)_\d{3}\b', 'Flaw#': r'#\d{1,2}\b',
}
res = []
res.append(f'# Document map of {os.path.basename(path)} ({len(L)} lines)\n')
res.append('## Headings (outside fences)\n')
res.append('| # | line | end | lvl | heading |\n|---|---|---|---|---|')
for k, h in enumerate(hs, 1):
    res.append(f"| {k} | {h['line']} | {h['next_line']} | H{h['level']} | {h['text'][:160].replace('|','/')} |")
res.append('\n## ID families (whole file incl. code)\n')
res.append('| family | distinct | occurrences | sample |\n|---|---|---|---|')
for fam, pat in ID_PATTERNS.items():
    found = re.findall(pat, text)
    c = collections.Counter(found)
    sample = ', '.join(sorted(c)[:25])
    res.append(f'| {fam} | {len(c)} | {sum(c.values())} | {sample} |')
res.append('\n## Tables\n')
res.append('| # | start | end | header cols | rows | col-mismatch rows |\n|---|---|---|---|---|---|')
for k, t in enumerate(tbs, 1):
    bad = [ln for ln, r in t['rows'] if len(r) != len(t['header'])]
    res.append(f"| {k} | {t['start']} | {t['end']} | {len(t['header'])} | {len(t['rows'])} | {bad if bad else '-'} |")
res.append('\n## Code blocks\n')
res.append('| # | start | end | lang | lines |\n|---|---|---|---|---|')
for k, b in enumerate(blocks, 1):
    res.append(f"| {k} | {b['start']} | {b['end']} | {b['lang'] or '(none)'} | {b['end']-b['start']-1} |")
s = '\n'.join(res) + '\n'
if out:
    open(out, 'w').write(s)
    print(f'wrote {out}: {len(hs)} headings, {len(tbs)} tables, {len(blocks)} code blocks')
else:
    print(s)

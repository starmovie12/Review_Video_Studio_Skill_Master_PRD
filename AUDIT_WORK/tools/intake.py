#!/usr/bin/env python3
"""Integrity intake report (integrity_rule). Usage: intake.py FILE"""
import hashlib, re, sys, collections, os
sys.path.insert(0, os.path.dirname(__file__))
import mdlib

path = sys.argv[1]
data = open(path, 'rb').read()
try:
    text = data.decode('utf-8'); utf8 = True
except UnicodeDecodeError as e:
    text = data.decode('utf-8', 'replace'); utf8 = f'NO ({e})'
lines = text.split('\n')
if lines and lines[-1] == '':
    lines = lines[:-1]
blocks, in_fence, unb = mdlib.scan(lines)
hs = mdlib.headings(lines, in_fence)
tbs = mdlib.tables(lines, in_fence)
lvl = collections.Counter(h['level'] for h in hs)
title = next((h['text'] for h in hs if h['level'] == 1), None)
ver = None
for l in lines[:80]:
    m = re.search(r'\b[Vv]ersion\b[^0-9vV]{0,20}(v?\d+(?:\.\d+)+)', l) or re.search(r'\b(v\d+(?:\.\d+)+)\b', l)
    if m:
        ver = m.group(1); break
fences_total = sum(1 for i, l in enumerate(lines) if mdlib.FENCE_RE.match(l))
print(f'file           : {os.path.abspath(path)}')
print(f'size_bytes     : {len(data)}')
print(f'sha256         : {hashlib.sha256(data).hexdigest()}')
print(f'utf8_valid     : {utf8}')
print(f'title          : {title}')
print(f'version        : {ver}')
print(f'total_lines    : {len(lines)}  (ends_with_newline={data.endswith(b"\n")})')
print(f'headings       : {len(hs)}  per_level=' + ', '.join(f'H{k}:{lvl[k]}' for k in sorted(lvl)))
print(f'tables         : {len(tbs)}')
print(f'code_blocks    : {len(blocks)}  (fence-looking lines={fences_total})')
print(f'fences_balanced: {unb is None}' + ('' if unb is None else f'  UNCLOSED fence opened at line {unb["start"]}'))
print(f'last_section   : {hs[-1]["text"] if hs else None} (line {hs[-1]["line"] if hs else "-"})')
print('last_5_lines   :')
for i in range(max(0, len(lines) - 5), len(lines)):
    print(f'  {i+1:>5}| {lines[i]}')

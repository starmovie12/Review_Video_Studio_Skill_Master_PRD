#!/usr/bin/env python3
"""integrity: UTF-8, fences, table column consistency, heading jumps, duplicate headings,
zero-width / bidi / look-alike chars, NBSP, smart quotes in code, mixed EOL, trailing junk.
Usage: integrity.py FILE [--quiet]   exit 0 = PASS (no hard failures)"""
import sys, os, collections, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
import mdlib

path = sys.argv[1]
quiet = '--quiet' in sys.argv
raw = open(path, 'rb').read()
hard, soft = [], []
try:
    text = raw.decode('utf-8')
except UnicodeDecodeError as e:
    print('FAIL utf8', e); sys.exit(2)
if b'\r\n' in raw:
    (hard if b'\n' in raw.replace(b'\r\n', b'') else soft).append('CRLF line endings present')
L = text.split('\n')
if L and L[-1] == '':
    L = L[:-1]
blocks, inf, unb = mdlib.scan(L)
if unb:
    hard.append(f'unclosed fence at line {unb["start"]}')
hs = mdlib.headings(L, inf)
prev = 0
for h in hs:
    if prev and h['level'] > prev + 1:
        soft.append(f"heading level jump H{prev}->H{h['level']} at line {h['line']}")
    prev = h['level']
dup = collections.Counter(h['text'] for h in hs)
for t, c in dup.items():
    if c > 1:
        soft.append(f'duplicate heading x{c}: {t[:80]}')
for t in mdlib.tables(L, inf):
    n = len(t['header'])
    if t['sep_cols'] != n:
        hard.append(f"table@{t['start']}: separator cols {t['sep_cols']} != header {n}")
    for ln, r in t['rows']:
        if len(r) != n:
            hard.append(f'table@{t["start"]}: row line {ln} has {len(r)} cols, header {n}')
BAD = {'​': 'ZWSP', '‌': 'ZWNJ-outside-indic?', '‍': 'ZWJ', '⁠': 'WJ', '﻿': 'BOM',
       '‪': 'LRE', '‫': 'RLE', '‬': 'PDF', '‭': 'LRO', '‮': 'RLO',
       '⁦': 'LRI', '⁧': 'RLI', '⁨': 'FSI', '⁩': 'PDI', '­': 'SHY'}
SMART = '‘’“”'
for i, l in enumerate(L, 1):
    for ch in l:
        if ch in BAD:
            # ZWJ/ZWNJ legit inside Devanagari conjuncts: only flag when neighbours are not Devanagari
            hard.append(f'line {i}: invisible char {BAD[ch]} U+{ord(ch):04X}')
        elif ch == ' ':
            soft.append(f'line {i}: NBSP')
        elif unicodedata.category(ch) == 'Cc' and ch != '\t':
            hard.append(f'line {i}: C0/C1 control char U+{ord(ch):04X}')
        elif unicodedata.category(ch) == 'Co':
            hard.append(f'line {i}: private-use char U+{ord(ch):04X}')
        elif ch in 'аеорсухΑΒΕΟ':
            hard.append(f'line {i}: look-alike Cyrillic/Greek char U+{ord(ch):04X}')
    if inf[i - 1] and any(c in l for c in SMART):
        soft.append(f'line {i}: smart quote inside code block')
    if l != l.rstrip() and not inf[i - 1] and l.rstrip() != '' and not l.endswith('  '):
        pass  # trailing spaces outside code are harmless in md
if not text.endswith('\n'):
    soft.append('file does not end with newline')
if text.rstrip('\n') != text[:-1] if text.endswith('\n') else False:
    soft.append('multiple trailing blank lines')
print(f'integrity {os.path.basename(path)}: lines={len(L)} headings={len(hs)} code_blocks={len(blocks)} '
      f'HARD={len(hard)} SOFT={len(soft)} -> {"PASS" if not hard else "FAIL"}')
if not quiet:
    for x in hard: print('  HARD', x)
    sc = collections.Counter(s.split(':')[0] if s.startswith('line') else s for s in soft)
    for x in soft[:200]: print('  soft', x)
sys.exit(0 if not hard else 1)

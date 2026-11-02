#!/usr/bin/env python3
"""Append defects to defects.csv with auto IDs.
Input on stdin: one defect per line, fields separated by ' ;; ':
type ;; location ;; lens ;; severity ;; what ;; evidence ;; planned_fix
"""
import csv, sys, os
p = os.path.join(os.path.dirname(__file__), '..', 'defects.csv')
rows = list(csv.reader(open(p)))
n = len(rows) - 1
w = csv.writer(open(p, 'a', newline=''))
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    f = [x.strip() for x in line.split(' ;; ')]
    if len(f) != 7:
        print('BAD FIELD COUNT', len(f), line[:80]); continue
    n += 1
    w.writerow([f'D-{n:03d}'] + f + ['OPEN', ''])
    print(f'D-{n:03d}', f[3], f[4][:90])

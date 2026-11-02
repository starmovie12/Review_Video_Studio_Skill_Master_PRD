#!/usr/bin/env python3
"""Shared Markdown parsing helpers for audit tools (stdlib only).

Fence rule (CommonMark): opening fence = up to 3 spaces + >=3 backticks or tildes.
Closing fence = same char, length >= opening length, no info string.
"""
import re

FENCE_RE = re.compile(r'^( {0,3})(`{3,}|~{3,})(.*)$')
HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
TABLE_SEP_RE = re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$')


def scan(lines):
    """Return (blocks, in_fence_flags, unbalanced).

    blocks: list of dict(start, end, lang, fence) 1-based inclusive line numbers.
    in_fence: list[bool] per line (True for fence lines and content inside).
    unbalanced: dict or None for an unclosed fence.
    """
    blocks = []
    in_fence = [False] * len(lines)
    cur = None
    for i, raw in enumerate(lines):
        line = raw.rstrip('\n')
        m = FENCE_RE.match(line)
        if cur is None:
            if m:
                ch, ln = m.group(2)[0], len(m.group(2))
                info = m.group(3).strip()
                if ch == '`' and '`' in info:
                    pass  # not a fence per CommonMark
                else:
                    cur = dict(start=i + 1, lang=(info.split()[0] if info else ''), char=ch, n=ln)
                    in_fence[i] = True
                    continue
        else:
            in_fence[i] = True
            if m and m.group(2)[0] == cur['char'] and len(m.group(2)) >= cur['n'] and m.group(3).strip() == '':
                cur['end'] = i + 1
                blocks.append(cur)
                cur = None
    unbalanced = cur
    return blocks, in_fence, unbalanced


def headings(lines, in_fence):
    out = []
    for i, raw in enumerate(lines):
        if in_fence[i]:
            continue
        m = HEADING_RE.match(raw.rstrip('\n'))
        if m:
            out.append(dict(line=i + 1, level=len(m.group(1)), text=m.group(2).strip()))
    # compute end lines
    for k, h in enumerate(out):
        end = len(lines)
        for h2 in out[k + 1:]:
            if h2['level'] <= h['level']:
                end = h2['line'] - 1
                break
        h['end'] = end
        h['next_line'] = out[k + 1]['line'] - 1 if k + 1 < len(out) else len(lines)
    return out


def split_row(line):
    """GFM: cells split on every unescaped pipe, even inside code spans."""
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|') and not s.endswith('\\|'):
        s = s[:-1]
    cells = re.split(r'(?<!\\)\|', s)
    return [x.strip() for x in cells]


def tables(lines, in_fence):
    """Find GFM tables outside fences: header row + separator row + body rows."""
    out = []
    i = 0
    n = len(lines)
    while i < n - 1:
        if not in_fence[i] and '|' in lines[i] and not in_fence[i + 1] and TABLE_SEP_RE.match(lines[i + 1].rstrip('\n')):
            hdr = split_row(lines[i])
            sep = split_row(lines[i + 1])
            start = i + 1
            rows = []
            j = i + 2
            while j < n and not in_fence[j] and lines[j].strip() != '' and '|' in lines[j]:
                rows.append((j + 1, split_row(lines[j])))
                j += 1
            out.append(dict(start=start, end=j, header=hdr, sep_cols=len(sep), rows=rows))
            i = j
        else:
            i += 1
    return out


def load(path):
    with open(path, 'rb') as f:
        data = f.read()
    text = data.decode('utf-8')
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]
    return data, text, lines

#!/usr/bin/env python3
"""checks.py — Phase 5 Pass B mechanical checks on PRD_UPDATED.md (read-only). Usage: checks.py [ids|xref|codes|scaffold|secrets|budgets|all]
Each check prints PASS/FAIL lines; exit 1 if any FAIL."""
import json, os, re, sys, glob, subprocess, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import mdlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PRD = os.path.join(ROOT, 'PRD_UPDATED.md')
SCAF = os.path.join(ROOT, 'AUDIT_WORK', '_scaffold', 'review-video-studio')
_, TEXT, L = mdlib.load(PRD)
BLOCKS, INF, _u = mdlib.scan(L)
HS = mdlib.headings(L, INF)
FAILS = []


def fail(check, msg):
    FAILS.append((check, msg)); print(f'FAIL [{check}] {msg}')


def ok(check, msg):
    print(f'PASS [{check}] {msg}')


def section(title_prefix):
    h = next(h for h in HS if h['text'].startswith(title_prefix))
    return '\n'.join(L[h['line'] - 1:h['end']])


def table_first_col(sec_text, pat):
    return [m.group(1) for m in re.finditer(pat, sec_text)]


def check_ids():
    s11 = section('11. Metrics')
    tcs = table_first_col(s11, r'^\| \*\*`(TC-\d\d)`\*\*', ) or re.findall(r'(?m)^\| \*\*`(TC-\d\d)`\*\*', s11)
    tcs = re.findall(r'(?m)^\| \*\*`(TC-\d\d)`\*\*', s11)
    exp = [f'TC-{i:02d}' for i in range(1, 39)]
    (ok if tcs == exp else fail)('ids', f'TC rows in §11: {len(tcs)} defined, sequence {"ok" if tcs == exp else "BROKEN"}; dupes={len(tcs)-len(set(tcs))}')
    used = set(re.findall(r'\bTC-(\d\d)\b', TEXT))
    bad = sorted(u for u in used if not 1 <= int(u) <= 38)
    (ok if not bad else fail)('ids', f'TC references out of range: {bad}')
    s10 = section('10. Comprehensive Edge Cases')
    rows = [int(x) for x in re.findall(r'(?m)^\| (\d+) \| \*\*', s10)]
    (ok if rows == list(range(1, 55)) else fail)('ids', f'§10 rows: {len(rows)} (expect 1..54)')
    for fam, lo, hi, pat in (('OSS-SKL', 1, 13, r'OSS-SKL-(\d\d)'), ('PCP', 1, 7, r'\bPCP-(\d)\b'), ('D-locked', 1, 18, r'`D(\d{1,2})`'), ('Q', 1, 7, r'`Q(\d)`')):
        used = {int(x) for x in re.findall(pat, TEXT)}
        out = sorted(x for x in used if not lo <= x <= hi)
        miss = sorted(set(range(lo, hi + 1)) - used)
        (ok if not out and not miss else fail)('ids', f'{fam}: out-of-range={out} never-mentioned={miss}')
    decs = set(re.findall(r'\bDEC-(\d\d)\b', TEXT))
    defined = set(re.findall(r'(?m)^\| `?DEC-(\d\d)`? \|', TEXT))
    und = sorted(decs - defined)
    (ok if not und else fail)('ids', f'DEC-nn referenced but not defined in a PRD table: {["DEC-"+u for u in und]}')
    for d in sorted(set(re.findall(r'\bR(\d{1,2})\b', section('13. Technical Risk')))):
        pass
    risks = re.findall(r'(?m)^\| \*\*R(\d{1,2})\*\* \|', section('13. Technical Risk'))
    (ok if [int(r) for r in risks] == list(range(1, 19)) else fail)('ids', f'Risk rows R1..R18: {risks}')


def heading_numbers():
    nums = set()
    for h in HS:
        m = re.match(r'(?:Appendix\s+)?([A-Z]\d?(?:\.\d+)*|\d+(?:\.\d+)*)[\s.:—-]', h['text'])
        if m:
            nums.add(m.group(1).rstrip('.'))
        m2 = re.match(r'([A-Z])\.(\d+(?:\.\d+)*)', h['text'])
        if m2:
            nums.add(f'{m2.group(1)}.{m2.group(2)}')
        m3 = re.match(r'Appendix ([A-Z]\d?)', h['text'])
        if m3:
            nums.add(m3.group(1))
        m4 = re.match(r'(C\.\d)–(C\.\d)', h['text'])
        if m4:
            for i in range(int(m4.group(1)[2]), int(m4.group(2)[2]) + 1):
                nums.add(f'C.{i}')
    return nums


def check_xref():
    nums = heading_numbers()
    bad = set()
    for m in re.finditer(r'§\s?(\d+(?:\.\d+)*[A-Z]?)', TEXT):
        n = m.group(1)
        base = re.sub(r'[A-Z]$', '', n)
        if n not in nums and base not in nums and n.split('.')[0] not in nums:
            bad.add(n)
    (ok if not bad else fail)('xref', f'§ references not resolving to a heading: {sorted(bad)}')
    bad = set()
    for m in re.finditer(r'(?:App(?:endix)?\.?\s)([A-R]\d?(?:\.\d+)*)', TEXT):
        n = m.group(1).rstrip('.')
        if n not in nums and n.split('.')[0] not in nums:
            bad.add(n)
    (ok if not bad else fail)('xref', f'Appendix references not resolving: {sorted(bad)}')
    # files named in prose vs tree/inventory (A.1 + A.2 + A.5)
    inv = section('Appendix A') + section('A.5')
    known = set(re.findall(r'`([\w./-]+\.(?:py|md|json|sh|txt|ttf|yml))`', inv)) | set(re.findall(r'([\w-]+\.(?:py|md|json|sh|txt|ttf))', inv))
    named = set(re.findall(r'`((?:scripts|schemas|references|assets|tests|evals|cost)/[\w./-]+\.(?:py|md|json|sh|txt|ttf))`', TEXT))
    missing = sorted(n for n in named if n not in known and os.path.basename(n) not in known and '*' not in n)
    (ok if not missing else fail)('xref', f'files named in prose but absent from Appendix A tree/inventory: {missing}')


def code_blocks_after(heading_prefix, lang):
    h = next(h for h in HS if h['text'].startswith(heading_prefix))
    return ['\n'.join(L[b['start']:b['end'] - 1]) for b in BLOCKS if h['line'] < b['start'] < h['end'] and b['lang'] == lang]


def check_codes():
    j = section('Appendix J')
    table = re.findall(r'(?m)^\| `(RVS_(?:ERR|WARN)_\d{3})` \|', j)
    reg_txt = code_blocks_after('J.4', 'json')[0]
    reg = json.loads(reg_txt)
    rc = [c['code'] for c in reg['codes']]
    (ok if table == rc else fail)('codes', f'J.2 table ({len(table)}) == J.4 registry ({len(rc)}): {table == rc}')
    (ok if len(rc) == len(set(rc)) else fail)('codes', 'no duplicate codes')
    used = set(re.findall(r'RVS_(?:ERR|WARN)_\d{3}', TEXT))
    und = sorted(used - set(rc))
    (ok if not und else fail)('codes', f'codes used in PRD but not in registry: {und}')
    gcode = '\n'.join(code_blocks_after('Appendix G', 'python'))
    ev_ids = set(re.findall(r'"id": "([A-Z0-9-]+)"', '\n'.join(code_blocks_after('Appendix M', 'python'))))
    notraised = [c['code'] for c in reg['codes'] if c['code'] not in gcode and 'SKILL.md' not in c['raised_by'] and 'Builder' not in c['raised_by']]
    (ok if not notraised else fail)('codes', f'script-raised codes missing from Appendix G code: {notraised}')
    tcs = set(re.findall(r'(?m)^\| \*\*`(TC-\d\d)`\*\*', section('11. Metrics')))
    badtest = [c['code'] + ':' + c['test_id'] for c in reg['codes'] if c['test_id'].startswith('TC') and c['test_id'] not in tcs]
    (ok if not badtest else fail)('codes', f'registry test ids not defined in §11: {badtest}')
    ecs = {e for c in reg['codes'] for e in c['edge_case_ids']}
    miss = [f'EC-{i:02d}' for i in range(1, 55) if f'EC-{i:02d}' not in ecs]
    (ok if not miss else fail)('codes', f'§10 rows without a code: {miss}')


SCAF_MAP = [('G.1 `scripts/preflight.py`', 'python', 'scripts/preflight.py'), ('G.2 `scripts/voice_pack.py`', 'python', 'scripts/voice_pack.py'),
            ('G.3 `scripts/build_video.py`', 'python', 'scripts/build_video.py'), ('G.4 `scripts/make_cover.py`', 'python', 'scripts/make_cover.py'),
            ('G.5 `scripts/qa_contact_sheet.py`', 'python', 'scripts/qa_contact_sheet.py'), ('G.6 `scripts/similarity_check.py`', 'python', 'scripts/similarity_check.py'),
            ('G.7 `scripts/character_overlay.py`', 'python', 'scripts/character_overlay.py'), ('G.8 `scripts/repurpose_shorts.py`', 'python', 'scripts/repurpose_shorts.py'),
            ('G.9 `scripts/rvs_common.py`', 'python', 'scripts/rvs_common.py'), ('G.10 `scripts/voice_engines.py`', 'python', 'scripts/voice_engines.py'),
            ('C.7 Upgraded JSON Schema 1', 'json', 'schemas/spec.schema.json'), ('C.8 Upgraded JSON Schema 2', 'json', 'schemas/words.schema.json'),
            ('C.9 Validated Sample Blueprint', 'json', 'assets/fonts/sample_spec_smoke.json'), ('J.4 Registry file', 'json', 'schemas/error_codes.json'),
            ('J.5 Registry schema', 'json', 'schemas/error_codes.schema.json'), ('M.5 Harness', 'python', 'evals/run_evals.py'),
            ('M.6 Golden dataset generator', 'python', 'evals/make_cases.py'), ('L.6 Cost script', 'python', 'cost/cost_model.py'),
            ('N.4 CI workflow', 'yaml', '.github/workflows/ci.yml'), ('H.3 `.env.example`', 'text', '.env.example')]


def check_scaffold():
    for head, lang, rel in SCAF_MAP:
        try:
            blk = code_blocks_after(head, lang)[0]
        except (StopIteration, IndexError):
            fail('scaffold', f'no {lang} block under heading {head}'); continue
        disk = open(os.path.join(SCAF, rel), encoding='utf-8').read().rstrip('\n')
        same = blk.rstrip('\n') == disk if lang != 'json' else json.loads(blk) == json.loads(disk)
        (ok if same else fail)('scaffold', f'{rel} == PRD block under "{head[:30]}": {same}')
    for b in [b for b in BLOCKS if b['lang'] == 'python' and b['start'] > next(h for h in HS if h['text'].startswith('Appendix G'))['line']]:
        src = '\n'.join(L[b['start']:b['end'] - 1])
        try:
            compile(src, f'PRD:L{b["start"]}', 'exec')
        except SyntaxError as e:
            fail('scaffold', f'python block at L{b["start"]} does not compile: {e}')
    for b in [b for b in BLOCKS if b['lang'] == 'json']:
        try:
            json.loads('\n'.join(L[b['start']:b['end'] - 1]))
        except ValueError as e:
            fail('scaffold', f'json block at L{b["start"]} invalid: {e}')
    code = '\n'.join(open(f, encoding='utf-8').read() for f in glob.glob(SCAF + '/scripts/*.py') + glob.glob(SCAF + '/cost/*.py'))
    reads = set(re.findall(r'os\.environ(?:\.get)?\(\s*"([A-Z_]+)"', code)) | set(re.findall(r'os\.environ\["([A-Z_]+)"\]', code)) | {'ELEVENLABS_API_KEY'}
    env = set(re.findall(r'(?m)^([A-Z_]+)=', open(os.path.join(SCAF, '.env.example')).read()))
    a, b2 = sorted(reads - env - {'PREFIX'}), sorted(env - reads)
    (ok if not a and not b2 else fail)('scaffold', f'.env.example parity: read-not-documented={a} documented-not-read={b2}')
    nfiles = len([p for p in glob.glob(SCAF + '/**/*', recursive=True) if os.path.isfile(p) and '__pycache__' not in p and '/logs/' not in p and '/evals/reports/' not in p])
    ok('scaffold', f'scaffold files on disk: {nfiles} (A.5 counts 48 build items incl. 31 original + grouped items)')


def check_secrets():
    pats = [r'sk_[A-Za-z0-9]{20,}', r'sk-[A-Za-z0-9_-]{20,}', r'AKIA[0-9A-Z]{16}', r'xi-api-key:\s*[A-Za-z0-9]{16,}', r'(?i)api_key\s*=\s*["\'][A-Za-z0-9_-]{16,}["\']']
    hits = [(i + 1, re.search(p, l).group(0)[:24]) for i, l in enumerate(L) for p in pats if re.search(p, l)]
    (ok if not hits else fail)('secrets', f'secret-like literals in PRD: {hits}')
    gi = open(os.path.join(SCAF, '.gitignore')).read()
    (ok if '.env' in gi and '*.key' in gi else fail)('secrets', '.gitignore covers .env and *.key')
    logs_env = re.findall(r'(?m)^.*(?:print|log_event|warn)\(.*os\.environ\[.*$', '\n'.join(code_blocks_after('Appendix G', 'python')))
    (ok if not logs_env else fail)('secrets', f'code printing env values: {len(logs_env)}')


def check_budgets():
    k = section('K.2 Budget table')
    rows = [r for r in k.split('\n') if r.startswith('| `S')]
    lab = [r for r in rows if not re.search(r'MEASURED|ESTIMATE|TARGET', r)]
    (ok if rows and not lab else fail)('budgets', f'{len(rows)} budget rows; unlabeled: {len(lab)}')
    stages = {re.match(r'\| `([^`]+)`', r).group(1) for r in rows}
    need = {'S7-L', 'S8-L', 'S9-L', 'S10-L', 'S11–S12'}
    miss = [s for s in need if not any(x.startswith(s) for x in stages)]
    (ok if not miss else fail)('budgets', f'major stages without a budget row: {miss}')
    for r in rows:
        c = [x.strip() for x in r.strip('|').split('|')]
        s = re.match(r'(\d+) s$', c[3]); h = re.match(r'(\d+) s', c[4])
        if s and h and int(s.group(1)) >= int(h.group(1)):
            fail('budgets', f'soft >= hard: {c[0]} {c[1]} {c[2]}')
    b1 = [r for r in rows if '| B1' in r or 'B1/B2' in r]; b2 = [r for r in rows if '| B2' in r or 'B1/B2' in r]
    (ok if b1 and b2 else fail)('budgets', f'baseline rows B1={len(b1)} B2={len(b2)}')


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    for name, fn in (('ids', check_ids), ('xref', check_xref), ('codes', check_codes), ('scaffold', check_scaffold), ('secrets', check_secrets), ('budgets', check_budgets)):
        if which in ('all', name):
            try:
                fn()
            except Exception as e:  # a crashing check is a FAIL, never silent
                fail(name, f'check crashed: {type(e).__name__}: {e}')
    print(f'TOTAL FAIL: {len(FAILS)}')
    sys.exit(1 if FAILS else 0)

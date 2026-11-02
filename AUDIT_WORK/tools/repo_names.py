#!/usr/bin/env python3
"""repo_names: list owner/name repo tokens, package names and model tokens with line numbers.
Usage: repo_names.py FILE [--banned name1,name2] [--changelog-start LINE --changelog-end LINE]
Exit 1 if a banned (replaced) name occurs outside the changelog range."""
import re, sys, collections
path = sys.argv[1]
lines = open(path, encoding='utf-8').read().split('\n')
banned = []
if '--banned' in sys.argv:
    banned = [b for b in sys.argv[sys.argv.index('--banned') + 1].split(',') if b]
cl = (0, 0)
if '--changelog-start' in sys.argv:
    cl = (int(sys.argv[sys.argv.index('--changelog-start') + 1]), int(sys.argv[sys.argv.index('--changelog-end') + 1]))
# owner/name: GitHub-like, avoid paths like scripts/x.py, assets/fonts, file extensions, units
OWNER_RE = re.compile(r'(?<![\w./-])([A-Za-z0-9][A-Za-z0-9-]{1,38})/([A-Za-z0-9][A-Za-z0-9._-]{1,99})(?![\w/])')
SKIP_OWNERS = {'scripts', 'assets', 'schemas', 'references', 'fonts', 'usr', 'share', 'system', 'tmp', 'data', 'sdcard',
               'src', 'app', 'docs', 'render_kit', 'review-video-studio', 'AUDIT_WORK', 'evals', 'tests', 'logs', 'character',
               'gojo_rig', 'custom', 'examples', 'shorts_generator', 'truetype', 'TTF', 'noto', 'dejavu', 'liberation',
               'liberation2', 'files', 'com.termux', 'UI', 'v', 'a', 'Pros', 'cons', 'Download', 'bin', 'ffmpeg_normalize',
               'edge_tts', 'answer', 'video', 'youtube', 'blog', 'news-2', 'technology', 'publications', 'article', 'thought-leaderships',
               'wiki', 'ticket', 'project', 'articles', 'en', 'en-us', 'releases', 'models', 'api', 'v1', 'v3', 'packages', 'pypi', 'npm',
               'X', 'Day-1', 'Theatre', 'Price', 'Movie', 'Software', 'Gadget', 'Spec', 'Theatre-vs-OTT', 'Movies', 'BookMyShow', 'Hindi',
               'Critics', 'Instagram', 'Gemini', 'Perplexity', 'Pro', 'Steam', 'Metacritic', 'Play', 'Amazon.in', 'Reddit', 'mid-roll'}
found = collections.defaultdict(list)
for i, l in enumerate(lines, 1):
    for m in OWNER_RE.finditer(l):
        owner, name = m.group(1), m.group(2)
        if owner in SKIP_OWNERS or name.endswith(('.py', '.md', '.json', '.ttf', '.txt', '.sh', '.png', '.jpg', '.wav', '.mp4', '.ass')):
            continue
        if not re.search(r'[A-Za-z]', owner) or not re.search(r'[A-Za-z]', name):
            continue
        # heuristics: require it to look like a repo (appears in backticks or github URL)
        ctx = l[max(0, m.start() - 25):m.end() + 2]
        if '`' in ctx or 'github.com' in ctx or 'huggingface.co' in ctx:
            found[f'{owner}/{name}'.rstrip('.)')].append(i)
for k in sorted(found, key=str.lower):
    v = found[k]
    print(f'{k:55} n={len(v):3} lines={v[:12]}{"..." if len(v) > 12 else ""}')
bad = 0
for b in banned:
    for i, l in enumerate(lines, 1):
        if b in l and not (cl[0] <= i <= cl[1]):
            print(f'BANNED-NAME-OUTSIDE-CHANGELOG {b} line {i}')
            bad += 1
print(f'repo tokens: {len(found)}; banned occurrences outside changelog: {bad}')
sys.exit(1 if bad else 0)

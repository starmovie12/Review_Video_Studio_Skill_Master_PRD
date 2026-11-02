#!/usr/bin/env python3
"""repo_stats: fetch live adoption/maintenance/license evidence for GitHub repos.
Sources (public APIs reachable from this session; github.com/api.github.com blocked by session policy):
  - repos.ecosyste.ms API (stars, forks, pushed_at, archived, fork, license, default branch, dependents)
  - api.deps.dev v3 projects (stars, forks, license, OpenSSF scorecard)
  - raw.githubusercontent.com LICENSE file (first 400 chars) at default branch
Saves one JSON per repo into evidence/repo_<owner>__<name>.json with access timestamp + URLs.
Usage: repo_stats.py owner/name [owner/name ...]"""
import json, sys, os, urllib.request, urllib.parse, datetime, ssl

EVD = os.path.join(os.path.dirname(__file__), '..', 'evidence')
os.makedirs(EVD, exist_ok=True)
ctx = ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE') or '/root/.ccr/ca-bundle.crt')


def get(url, raw=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'prd-audit/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            data = r.read()
            return (r.status, data.decode('utf-8', 'replace') if raw else json.loads(data))
    except urllib.error.HTTPError as e:
        return (e.code, None)
    except Exception as e:  # network error
        return (str(e)[:80], None)


def one(repo):
    owner, name = repo.split('/', 1)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    eco_url = f'https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/{urllib.parse.quote(repo, safe="")}'
    dd_url = f'https://api.deps.dev/v3/projects/{urllib.parse.quote("github.com/" + repo, safe="")}'
    s1, eco = get(eco_url)
    s2, dd = get(dd_url)
    out = {'repo': repo, 'accessed_utc': now, 'method': 'public API (ecosyste.ms + deps.dev) + raw LICENSE',
           'sources': {'ecosystems': [eco_url, s1], 'depsdev': [dd_url, s2]}}
    if eco:
        keys = ['full_name', 'html_url', 'stargazers_count', 'forks_count', 'open_issues_count', 'pushed_at', 'updated_at',
                'archived', 'fork', 'license', 'default_branch', 'dependent_repos_count', 'latest_tag_name',
                'latest_tag_published_at', 'size', 'created_at', 'description', 'commit_stats']
        out['ecosystems'] = {k: eco.get(k) for k in keys}
    if dd:
        out['depsdev'] = {'starsCount': dd.get('starsCount'), 'forksCount': dd.get('forksCount'),
                          'license': dd.get('license'), 'openIssuesCount': dd.get('openIssuesCount'),
                          'scorecard_date': (dd.get('scorecard') or {}).get('date'),
                          'scorecard_overall': (dd.get('scorecard') or {}).get('overallScore'),
                          'maintained': next((c.get('score') for c in (dd.get('scorecard') or {}).get('checks', []) if c.get('name') == 'Maintained'), None)}
    br = (out.get('ecosystems') or {}).get('default_branch') or 'main'
    full = (out.get('ecosystems') or {}).get('full_name') or repo
    for fn in ('LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING', 'LICENSE-MIT'):
        u = f'https://raw.githubusercontent.com/{full}/{br}/{fn}'
        st, txt = get(u, raw=True)
        if st == 200 and txt:
            out['license_file'] = {'url': u, 'head': txt[:400]}
            break
    with open(os.path.join(EVD, f'repo_{owner}__{name}.json'), 'w') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    e = out.get('ecosystems') or {}
    d = out.get('depsdev') or {}
    lic = (out.get('license_file') or {}).get('head', '')[:60].replace('\n', ' ')
    print(f"{repo:48} eco={s1} dd={s2} stars={e.get('stargazers_count')}/{d.get('starsCount')} forks={e.get('forks_count')} "
          f"pushed={str(e.get('pushed_at'))[:10]} arch={e.get('archived')} fork={e.get('fork')} lic={e.get('license')}/{d.get('license')} "
          f"deps={e.get('dependent_repos_count')} tag={e.get('latest_tag_name')}@{str(e.get('latest_tag_published_at'))[:10]} LICENSEFILE='{lic}'")


if __name__ == '__main__':
    for r in sys.argv[1:]:
        one(r)

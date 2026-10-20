"""Checks every built page: one <h1>, title/description length, canonical, OG image,
image alt + dimensions, valid JSON-LD and that every local link/asset exists."""
import json, re, sys
from pathlib import Path
from urllib.parse import unquote

PUB = Path(__file__).resolve().parent.parent / 'public'
issues, titles, descs = [], {}, {}
for f in sorted(PUB.rglob('*.html')):
    rel = f.relative_to(PUB).as_posix()
    s = f.read_text(encoding='utf-8')
    head = s.split('</head>')[0]
    t = re.search(r'<title>(.*?)</title>', head).group(1)
    d = re.search(r'<meta name="description" content="(.*?)"', head).group(1)
    titles.setdefault(t, []).append(rel)
    descs.setdefault(d, []).append(rel)
    if not 15 <= len(t) <= 70:
        issues.append((rel, f'title length {len(t)}'))
    if not 70 <= len(d) <= 160:
        issues.append((rel, f'description length {len(d)}'))
    if len(re.findall(r'<h1[\s>]', s)) != 1:
        issues.append((rel, 'h1 count %d' % len(re.findall(r'<h1[\s>]', s))))
    for tag in ('rel="canonical"', 'og:image"', 'og:title"', 'twitter:card"'):
        if tag not in head:
            issues.append((rel, 'missing ' + tag))
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(m.group(1))
        except ValueError as e:
            issues.append((rel, f'bad JSON-LD {e}'))
    for im in re.findall(r'<img [^>]*>', s):
        if 'src=' not in im:
            continue
        if not re.search(r'alt="[^"]+"', im) and 'aria-hidden' not in im and 'alt=""' not in im:
            issues.append((rel, 'img without alt: ' + im[:80]))
        if 'width=' not in im:
            issues.append((rel, 'img without size: ' + im[:80]))
    for u in re.findall(r'(?:href|src|poster|data-zoom)="([^"#:?]+)', s) + re.findall(r"url\('([^']+)'\)", s):
        if u.startswith(('http', 'mailto', '//')) or not u:
            continue
        u = unquote(u)
        if u.startswith('/'):  # --deploy build: clean root URLs served as /page -> page.html
            base = PUB / u.strip('/')
            ok = u == '/' or base.is_file() or base.with_name(base.name + '.html').is_file()
        else:
            ok = (f.parent / u).resolve().exists()
        if not ok:
            issues.append((rel, 'broken link ' + u))
for t, fs in titles.items():
    if len(fs) > 1:
        issues.append((fs[0], f'duplicate title on {len(fs)} pages: {t}'))
for d, fs in descs.items():
    if len(fs) > 1:
        issues.append((fs[0], f'duplicate description on {len(fs)} pages'))
pages = len(list(PUB.rglob('*.html')))
print(f'{pages} pages audited, {len(issues)} issues')
for i in issues[:40]:
    print(' ', *i)
sys.exit(1 if issues else 0)

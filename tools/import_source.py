"""One-time import: turns the scraped breetwilson.com posts (source/rendered/posts)
into clean data (src/data/posts.json) and downloads the post images."""
import json, re, sys, html, urllib.request, urllib.parse
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'source' / 'rendered' / 'posts'
IMG_DIR = ROOT / 'source' / 'media' / 'blog'
IMG_DIR.mkdir(parents=True, exist_ok=True)

KEEP = {'p', 'h2', 'h3', 'h4', 'strong', 'em', 'b', 'i', 'a', 'ul', 'ol', 'li', 'blockquote', 'br', 'img'}
SKIP_SLUGS = {'blog-post-template'}


class Clean(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.imgs, self.skip = [], [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('script', 'style', 'noscript', 'svg', 'button'):
            self.skip += 1
            return
        if self.skip:
            return
        if tag == 'img':
            src = (a.get('data-src') or a.get('src') or '').split('?')[0]
            if 'squarespace-cdn.com/content/v1' in src and src not in self.imgs:
                self.imgs.append(src)
                self.out.append(f'<img src="{{IMG:{src}}}" alt="{html.escape(a.get("alt") or "")}">')
            return
        if tag == 'h1':
            tag = 'h2'
        if tag not in KEEP:
            return
        if tag == 'a':
            href = a.get('href', '')
            if href.startswith('/'):
                href = 'https://www.breetwilson.com' + href
            self.out.append(f'<a href="{html.escape(href)}">')
        else:
            self.out.append(f'<{tag}>')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript', 'svg', 'button'):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag == 'h1':
            tag = 'h2'
        if tag in KEEP and tag not in ('img', 'br'):
            self.out.append(f'</{tag}>')

    def handle_data(self, d):
        if not self.skip:
            self.out.append(html.escape(d, quote=False))


def tidy(s):
    s = s.replace('\xa0', ' ').replace('​', '')
    s = re.sub(r'<(strong|em|b|i)>\s*</\1>', '', s)
    s = re.sub(r'<p>\s*(<br>\s*)*</p>', '', s)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s*(</?(p|h2|h3|h4|ul|ol|li|blockquote)>)\s*', r'\1', s)
    s = s.replace('</p>', '</p>\n').replace('</h2>', '</h2>\n').replace('</h3>', '</h3>\n')
    return s.strip()


def fetch(url):
    name = urllib.parse.unquote(url.split('/')[-1]).replace('+', '-').replace(' ', '-')
    name = re.sub(r'[^A-Za-z0-9._()-]', '', name) or 'image.jpg'
    dest = IMG_DIR / name
    if not dest.exists():
        req = urllib.request.Request(url + '?format=1500w', headers={'User-Agent': 'Mozilla/5.0'})
        dest.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    return name


posts = []
for f in sorted(SRC.glob('*.json')):
    slug = f.stem
    if slug in SKIP_SLUGS:
        continue
    d = json.loads(f.read_text(encoding='utf-8'))
    if 'Service Unavailable' in d['title']:
        print('skip (unavailable):', slug)
        continue
    c = Clean()
    c.feed(d['html'])
    body = tidy(''.join(c.out))
    for src in c.imgs:
        body = body.replace('{IMG:' + src + '}', 'IMG/' + fetch(src))
    text = re.sub(r'<[^>]+>', ' ', body)
    text = html.unescape(re.sub(r'\s+', ' ', text)).strip()
    posts.append({
        'slug': slug,
        'title': d['title'].strip(),
        'date': (d['date'] or '')[:10],
        'excerpt': text[:220].rsplit(' ', 1)[0] + '…' if len(text) > 220 else text,
        'images': [fetch(s) for s in c.imgs],
        'html': body,
    })
    print(slug, len(body), len(c.imgs))

posts.sort(key=lambda p: p['date'], reverse=True)
out = ROOT / 'src' / 'data' / 'posts.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(posts, indent=1, ensure_ascii=False), encoding='utf-8')
print(len(posts), 'posts ->', out)

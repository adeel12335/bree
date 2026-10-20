"""Makes self-contained copies of built pages (CSS inlined, images as data URIs,
animations frozen) in figma-export/, ready for Figma's html_to_figma import."""
import base64, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / 'public'
OUT = ROOT / 'figma-export'
OUT.mkdir(exist_ok=True)

PAGES = {
    'home': 'index.html', 'about': 'about.html', 'books': 'books.html',
    'book-deadly-college-murders': 'deadly-college-murders.html',
    'book-paris-noir': 'paris-noir-deadly-obsession.html',
    'awards': 'awards.html', 'blog': 'blog.html',
    'blog-post': 'blog/rafael-poisoned.html', 'contact': 'contact.html',
    'newsletter': 'newsletter.html',
}
MIME = {'.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml'}
FREEZE = '''<style>
.reveal{opacity:1!important;transform:none!important}
.site-header{position:absolute!important;background:rgba(12,11,9,.6)!important}
*{animation:none!important;transition:none!important}
.hero__bg,.page-hero__bg,.book-hero__bg{transform:scale(1.04)!important}
.scroll-cue{display:none}
html,body{width:1440px}
</style>'''


def data_uri(path):
    f = PUB / re.sub(r'^(?:\.\./|/)*', '', path)
    return f'data:{MIME[f.suffix]};base64,' + base64.b64encode(f.read_bytes()).decode()


def inline_assets(text):
    return re.sub(r'(?:\.\./|/)*(?<![\w-])assets/img/[\w.()-]+\.(?:webp|jpg|png|svg)', lambda m: data_uri(m.group(0)), text)


css = inline_assets((PUB / 'assets/css/style.css').read_text(encoding='utf-8').replace("url('../img/", "url('/assets/img/"))
fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Lato:wght@300;400;700&family=Pinyon+Script&display=swap">'
only = sys.argv[1:] or PAGES
for name in only:
    html = (PUB / PAGES[name]).read_text(encoding='utf-8')
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S)
    html = re.sub(r'<link rel="(?:preconnect|icon|stylesheet)"[^>]*>\n?', '', html)
    html = re.sub(r'<div class="lightbox".*?</div>', '', html, flags=re.S)
    html = re.sub(r'<video[^>]*poster="([^"]+)"[^>]*>.*?</video>', r'<img src="\1" alt="Trailer" style="width:100%;aspect-ratio:4/3;object-fit:cover">', html, flags=re.S)
    html = html.replace('loading="lazy"', 'loading="eager"')
    html = html.replace('</head>', f'{fonts}<style>{css}</style>{FREEZE}</head>')
    html = inline_assets(html)
    (OUT / f'{name}.html').write_text(html, encoding='utf-8')
    print(name, len(html) // 1024, 'KB')

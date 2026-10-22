"""Builds the Bree T. Wilson site into public/.

Content lives in src/data (books.json, posts.json, pages.json); page bodies are
rendered here so every page shares one header, footer and design system.
Run:  python tools/build.py
"""
import json, html, math, os, re, shutil, sys
from datetime import date
from functools import lru_cache
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
OUT = ROOT / 'public'
# Default: every page is a plain .html file with relative links, so the site opens
# straight from disk and works on any host. --deploy writes root-relative clean
# links (/about) for a host that maps /about -> about.html (.htaccess / Netlify).
DEPLOY = '--deploy' in sys.argv
SITE_URL = 'https://www.breetwilson.com'
SITE_NAME = 'Bree T. Wilson'
EMAIL = 'breetwilson25@gmail.com'
FORM_ENDPOINT = f'https://formsubmit.co/ajax/{EMAIL}'
INSTAGRAM = 'https://www.instagram.com/bree_twilson/'
TIKTOK = 'https://www.tiktok.com/@bree_twilson'
PRESS_RELEASE = 'https://brightkeydiscover.com/author/bree-t-wilson'
POSTS_PER_PAGE = 12

BOOKS = json.loads((SRC / 'data' / 'books.json').read_text(encoding='utf-8'))
POSTS = json.loads((SRC / 'data' / 'posts.json').read_text(encoding='utf-8'))
PAGES = json.loads((SRC / 'data' / 'pages.json').read_text(encoding='utf-8'))
BOOK_BY_SLUG = {b['slug']: b for b in BOOKS}
esc = html.escape

# ---------------------------------------------------------------- helpers

ICONS = {
    'instagram': '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="17.4" cy="6.6" r="1.1" fill="currentColor"/></svg>',
    'tiktok': '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M16.6 3c.3 2.2 1.6 3.7 3.9 3.9v3.1c-1.4.1-2.7-.3-3.9-1.1v6.2c0 3.6-2.6 5.9-5.8 5.9a5.6 5.6 0 0 1-5.6-5.7c0-3.5 3-6 6.5-5.5v3.2c-1.6-.4-3.3.6-3.3 2.3 0 1.4 1.1 2.4 2.4 2.4 1.5 0 2.5-.9 2.5-2.9V3h3.3z"/></svg>',
    'arrow': '<svg class="i-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-5-5 5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'mail': '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="m3.5 6 8.5 7 8.5-7" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>',
    'book': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5C6.5 4 9.5 4 12 5.8 14.5 4 17.5 4 20 5.5V19c-2.5-1.4-5.5-1.4-8 .4-2.5-1.8-5.5-1.8-8-.4V5.5z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M12 5.8v13.6" stroke="currentColor" stroke-width="1.6"/></svg>',
    'play': '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z" fill="currentColor"/></svg>',
    'star': '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="m12 2.8 2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4-4.7-4.4 6.4-.8z"/></svg>',
    'quote': '<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="currentColor" d="M20 12C11 15 6 21 6 30c0 5 3 8 7 8s7-3 7-7-3-7-7-7c1-5 4-8 9-10l-2-2zm22 0c-9 3-14 9-14 18 0 5 3 8 7 8s7-3 7-7-3-7-7-7c1-5 4-8 9-10l-2-2z"/></svg>',
}

LAUREL = '''<svg class="laurel" viewBox="0 0 240 240" aria-hidden="true">
 <defs><linearGradient id="lg-gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f3d68f"/><stop offset=".5" stop-color="#c99a45"/><stop offset="1" stop-color="#8e6524"/></linearGradient></defs>
 <g fill="url(#lg-gold)">{leaves}</g>
</svg>'''


def laurel_svg():
    # One branch of leaves along a circular arc (right side), mirrored for the left.
    branch = ['<path d="M154 218 A 100 100 0 0 0 170 37" fill="none" stroke="url(#lg-gold)" stroke-width="2.6"/>']
    for i in range(10):
        a = math.radians(-70 + i * 15)           # from bottom (-70°) up to the top (+65°)
        cx, cy = 120 + 100 * math.cos(a), 124 - 100 * math.sin(a)
        tangent = math.degrees(-a)                # leaf follows the arc
        for off, tilt in ((-11, -38), (11, 38)):   # inner and outer leaf
            lx = cx + off * math.cos(a)
            ly = cy - off * math.sin(a)
            branch.append(f'<ellipse cx="{lx:.1f}" cy="{ly:.1f}" rx="5.5" ry="13" '
                          f'transform="rotate({tangent + tilt:.1f} {lx:.1f} {ly:.1f})"/>')
    g = ''.join(branch)
    return LAUREL.format(leaves=f'{g}<g transform="translate(240 0) scale(-1 1)">{g}</g>')


@lru_cache(None)
def img_size(name):
    with Image.open(OUT / 'assets' / 'img' / f'{name}.webp') as im:
        return im.size


def img(name, alt, cls='', w=None, h=None, eager=False):
    attrs = [f'src="/assets/img/{name}.webp"', f'alt="{esc(alt)}"']
    if cls:
        attrs.append(f'class="{cls}"')
    w, h = img_size(name)  # intrinsic size on every image avoids layout shift
    attrs.append(f'width="{w}" height="{h}"')
    attrs.append('loading="eager" fetchpriority="high"' if eager else 'loading="lazy"')
    attrs.append('decoding="async"')
    return '<img ' + ' '.join(attrs) + '>'


def btn(label, href, style='gold', ext=False, arrow=True):
    target = ' target="_blank" rel="noopener"' if ext else ''
    return f'<a class="btn btn-{style}" href="{esc(href)}"{target}><span>{label}</span>{ICONS["arrow"] if arrow else ""}</a>'


def eyebrow(text, cls=''):
    return f'<p class="eyebrow {cls}">{text}</p>'


def book_url(b):
    return f'/{b["slug"]}/'


def full_title(b):
    return b['title'] + (f': {b["subtitle"]}' if b['subtitle'] else '')


def series_ids():
    ids = []
    for b in BOOKS:
        if b['series'] not in ids:
            ids.append(b['series'])
    return ids


def books_in(series):
    return [b for b in BOOKS if b['series'] == series]


def series_short(series):
    return books_in(series)[0]['series_name'].replace(' Mystery Series', '')


def series_kicker(b):
    return f'{b["series_name"].removesuffix(" Series")} · Book {b["series_no"]}'


def status_label(b):
    return b.get('status_label') or 'Coming Soon'


def cover_class(b, base):
    if b.get('cover_fit') == 'contain':
        return base + ' is-poster'
    if b['status'] == 'coming-soon':
        return base + ' is-flat'
    return base


def award_html(b):
    if not b.get('award'):
        return ''
    return f'<p class="award-line">{ICONS["star"]} {esc(b["award"])}</p>'


def fmt_date(d):
    if not d:
        return ''
    dt = date(*map(int, d.split('-')))
    return f'{dt:%B} {dt.day}, {dt.year}'


def social_links(cls='social'):
    return (f'<ul class="{cls}">'
            f'<li><a href="{INSTAGRAM}" target="_blank" rel="noopener" aria-label="Instagram">{ICONS["instagram"]}</a></li>'
            f'<li><a href="{TIKTOK}" target="_blank" rel="noopener" aria-label="TikTok">{ICONS["tiktok"]}</a></li>'
            '</ul>')


def page_hero(title, eyebrow_text='', bg='bg-library', intro='', small=False):
    return f'''<section class="page-hero{' page-hero--sm' if small else ''}">
  <div class="page-hero__bg" style="background-image:url('/assets/img/{bg}.webp')"></div>
  <div class="container page-hero__inner reveal">
    {eyebrow(eyebrow_text) if eyebrow_text else ''}
    <h1 class="display">{title}</h1>
    {f'<p class="page-hero__intro">{intro}</p>' if intro else ''}
    <span class="rule" aria-hidden="true"></span>
  </div>
</section>'''


# ---------------------------------------------------------------- shared sections

def newsletter_strip():
    return f'''<section class="newsletter-strip" id="newsletter">
  <div class="newsletter-strip__bg" aria-hidden="true"></div>
  <div class="container newsletter-strip__inner reveal">
    <div>
      {eyebrow('Newsletter')}
      <h2 class="h-serif">Join my mailing list for new books and updates.</h2>
    </div>
    {newsletter_form('strip')}
  </div>
</section>'''


def newsletter_form(variant):
    return f'''<form class="nl-form nl-form--{variant}" data-form="newsletter" action="{FORM_ENDPOINT}" method="POST" novalidate>
      <input type="hidden" name="_subject" value="New newsletter sign-up — breetwilson.com">
      <input type="hidden" name="_template" value="table">
      <input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
      <label class="sr-only" for="nl-{variant}">Email Address</label>
      <input id="nl-{variant}" type="email" name="email" placeholder="Email Address" required autocomplete="email">
      <button type="submit" class="btn btn-gold"><span>Sign Up</span></button>
      <p class="form-note" role="status" aria-live="polite">We respect your privacy.</p>
    </form>'''


def contact_strip():
    return f'''<section class="contact-strip">
  <div class="contact-strip__leaf" aria-hidden="true"></div>
  <div class="container contact-strip__inner reveal">
    <div>{eyebrow('Contact')}<h2 class="h-serif">Contact Bree T. Wilson</h2></div>
    <span class="vrule" aria-hidden="true"></span>
    <p>Have a question or just want to say hello?<br>I’d love to hear from you!</p>
    {btn('Get in Touch', '/contact/')}
  </div>
</section>'''


def book_card(b, i=0):
    soon = b['status'] == 'coming-soon'
    flag = f'<span class="book-card__flag">{esc(status_label(b))}</span>' if soon else ''
    cover_cls = cover_class(b, 'book-card__cover')
    label = status_label(b) if soon else 'Learn More'
    sub = f'<span>{esc(b["subtitle"])}</span>' if b['subtitle'] else ''
    return f'''<article class="book-card reveal" style="--d:{i * 90}ms">
  <a class="book-card__link" href="{book_url(b)}" aria-label="{esc(full_title(b))}">
    <div class="{cover_cls}">{flag}{img(b['cover'], full_title(b) + ' book cover')}</div>
    <h3 class="book-card__title">{esc(b['title'])}{':' if sub else ''}{sub}</h3>
    <span class="btn btn-outline btn-sm"><span>{label}</span>{ICONS['arrow']}</span>
  </a>
</article>'''


def post_card(p, big=False):
    image = ''
    if p['images']:
        image = f'<div class="post-card__img">{img("blog-" + Path(p["images"][0]).stem, p["title"])}</div>'
    return f'''<article class="post-card{' post-card--big' if big else ''} reveal">
  <a href="/blog/{p['slug']}/">
    {image}
    <div class="post-card__body">
      <time datetime="{p['date']}">{fmt_date(p['date'])}</time>
      <h3>{esc(p['title'])}</h3>
      <p>{esc(p['excerpt'])}</p>
      <span class="link-arrow">Read More {ICONS['arrow']}</span>
    </div>
  </a>
</article>'''


# ---------------------------------------------------------------- layout

NAV = [('Home', '/'), ('About', '/about/'), ('Books', '/books/'), ('Awards', '/awards/'),
       ('Blog', '/blog/'), ('Newsletter', '/newsletter/'), ('Contact', '/contact/')]


def header(active):
    items = []
    for label, href in NAV:
        cur = ' aria-current="page"' if active == href else ''
        if label == 'Books':
            sub = ['<li><a href="/books/">All Books</a></li>']
            for series in series_ids():
                sub.append(f'<li class="sub__label">{esc(series_short(series))}</li>')
                sub.extend(f'<li><a href="{book_url(b)}">{esc(full_title(b))}</a></li>' for b in books_in(series))
            items.append(f'''<li class="has-sub"><a href="{href}"{cur}>{label}</a>
          <button class="sub-toggle" aria-label="Show books" aria-expanded="false"><svg viewBox="0 0 24 24"><path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="1.8"/></svg></button>
          <ul class="sub">{''.join(sub)}</ul></li>''')
        else:
            items.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    return f'''<header class="site-header" data-header>
  <div class="container site-header__inner">
    <a class="brand" href="/" aria-label="Bree T. Wilson — home">Bree T. Wilson</a>
    <nav class="main-nav" aria-label="Main" data-nav>
      <ul>{''.join(items)}</ul>
      <div class="main-nav__extra">{social_links()}<a class="press-link" href="{PRESS_RELEASE}" target="_blank" rel="noopener">Author Press Release</a></div>
    </nav>
    <div class="site-header__icons">{social_links()}</div>
    <button class="menu-toggle" aria-label="Open menu" aria-expanded="false" data-menu><span></span><span></span><span></span></button>
  </div>
</header>'''


def footer():
    books = []
    for series in series_ids():
        items = ''.join(
            f'<li><a href="{book_url(b)}">{f"<em>{esc(status_label(b))}:</em> " if b["status"] == "coming-soon" else ""}{esc(full_title(b))}</a></li>'
            for b in books_in(series))
        books.append(f'<p class="footer-series">{esc(series_short(series))}</p><ul>{items}</ul>')
    books = ''.join(books)
    return f'''<footer class="site-footer">
  <div class="container site-footer__grid">
    <div class="site-footer__brand">
      <a class="brand" href="/">Bree T. Wilson</a>
      <p>4-time International Impact Book Award Distinguished Author Winner.</p>
      {social_links()}
    </div>
    <div><h2 class="mini-h">Books</h2>{books}</div>
    <div><h2 class="mini-h">Explore</h2><ul>
      <li><a href="/about/">About</a></li><li><a href="/awards/">Awards</a></li><li><a href="/blog/">Blog</a></li>
      <li><a href="/welcome/">Welcome!</a></li><li><a href="{PRESS_RELEASE}" target="_blank" rel="noopener">Author Press Release</a></li>
    </ul></div>
    <div><h2 class="mini-h">Stay in Touch</h2><ul>
      <li><a href="/newsletter/">Newsletter</a></li><li><a href="/contact/">Contact</a></li>
      <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
    </ul></div>
  </div>
  <div class="container site-footer__bottom">
    <p>© 2026 Bree T. Wilson. All Rights Reserved.</p>
    <p><a href="/privacy-policy/">Privacy Policy</a><span aria-hidden="true">|</span><a href="/terms-and-conditions/">Terms &amp; Conditions</a></p>
  </div>
</footer>'''


def clean_url(path):
    """Public URL for a page: matches the old Squarespace URLs (/about, /blog/slug)."""
    if path in ('/', '/404.html'):
        return SITE_URL + path
    return SITE_URL + path.rstrip('/')


def meta_desc(text, limit=158):
    text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', text)).strip()
    if len(text) <= limit:
        return text
    return text[:limit - 1].rsplit(' ', 1)[0].rstrip(',;:—-') + '…'


PERSON = {'@type': 'Person', '@id': SITE_URL + '/#author', 'name': 'Bree T. Wilson', 'url': SITE_URL + '/',
          'image': SITE_URL + '/assets/img/iiba-deadly-vows-award.webp', 'jobTitle': 'Murder Mystery Author',
          'email': 'mailto:' + EMAIL, 'sameAs': [INSTAGRAM, TIKTOK, PRESS_RELEASE],
          'award': ['International Impact Book Awards — Paris Noir: Deadly Obsession (2025)',
                    'International Impact Book Awards — Deadly Vows: Echoes of College Crimes (2026)',
                    'International Impact Book Awards — Deadly College Murders (2026)',
                    'International Impact Book Awards — The Thirteenth Riddle: A Poisoned Silence (2026)']}


def layout(path, title, desc, body, active=None, og_image='og.jpg', schema=None, body_cls='',
           crumbs=None, og_type='website', preload=None, noindex=False, extra_meta=''):
    if title == SITE_NAME:
        full = f'{SITE_NAME} | Award-Winning Murder Mystery Author'
    elif len(title) + len(SITE_NAME) + 3 <= 65:
        full = f'{title} | {SITE_NAME}'
    else:
        full = title
    desc = meta_desc(desc)
    canonical = clean_url(path)
    graph = list(schema or [])
    if crumbs:
        trail = [('Home', '/')] + crumbs
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': clean_url(u)} for i, (n, u) in enumerate(trail)]})
    ld = (f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)}</script>'
          if graph else '')
    og_path = OUT / 'assets' / 'img' / og_image
    ow, oh = Image.open(og_path).size if og_path.suffix != '.webp' else img_size(og_path.stem)
    pre = ''.join(f'<link rel="preload" as="image" href="/assets/img/{p}.webp" fetchpriority="high">' for p in (preload or []))
    robots = 'noindex, follow' if noindex else 'index, follow, max-image-preview:large'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="Bree T. Wilson">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/assets/img/{og_image}">
<meta property="og:image:width" content="{ow}">
<meta property="og:image:height" content="{oh}">
<meta property="og:image:alt" content="{esc(title if title != SITE_NAME else 'Bree T. Wilson, murder mystery author')}">
{extra_meta}<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(full)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE_URL}/assets/img/{og_image}">
<meta name="theme-color" content="#0f0d0b">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="sitemap" type="application/xml" href="/sitemap.xml">
{pre}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Lato:wght@300;400;700&family=Pinyon+Script&display=swap">
<link rel="stylesheet" href="/assets/css/style.css">
<script>document.documentElement.classList.add('js')</script>
{ld}
</head>
<body class="{body_cls}">
<a class="skip" href="#main">Skip to content</a>
{header(active)}
<main id="main">
{body}
</main>
{footer()}
<div class="lightbox" data-lightbox hidden><button class="lightbox__close" aria-label="Close">×</button><button class="lightbox__nav lightbox__prev" aria-label="Previous">‹</button><figure><img alt=""><figcaption></figcaption></figure><button class="lightbox__nav lightbox__next" aria-label="Next">›</button></div>
<script src="/assets/js/main.js" defer></script>
</body>
</html>'''


# ---------------------------------------------------------------- structured data

def book_schema(b, full=False):
    d = {'@type': 'Book', '@id': clean_url(book_url(b)) + '#book', 'name': full_title(b), 'url': clean_url(book_url(b)),
         'author': {'@id': SITE_URL + '/#author'}, 'image': f'{SITE_URL}/assets/img/{b["flat"]}.webp',
         'bookFormat': 'https://schema.org/EBook', 'inLanguage': 'en', 'genre': ['Mystery', 'Thriller', 'Crime Fiction'],
         'position': b['series_no'], 'isPartOf': {'@id': SITE_URL + '/books#' + b['series']}}
    if b.get('isbn'):
        d['isbn'] = b['isbn']
    if b.get('published'):
        d['datePublished'] = b['published']
    if b['shop']:
        d['sameAs'] = [u for _, u in b['shop']]
    if full:
        d['description'] = re.sub(r'<[^>]+>', '', ' '.join(b['blurb'][:3]))
        if b.get('award'):
            d['award'] = b['award']
        d['author'] = PERSON
        d['isPartOf'] = {'@type': 'BookSeries', 'name': b['series_name'], 'url': clean_url('/books/')}
    return d


def series_schemas():
    schemas = []
    for series in series_ids():
        schemas.append({'@type': 'BookSeries', '@id': SITE_URL + '/books#' + series, 'name': books_in(series)[0]['series_name'],
                        'url': clean_url('/books/'), 'author': {'@id': SITE_URL + '/#author'},
                        'hasPart': [book_schema(b) for b in books_in(series)]})
    return schemas


# ---------------------------------------------------------------- pages

def home():
    hannah = ''.join(book_card(b, i) for i, b in enumerate(books_in('hannah-walker')))
    astrid = ''.join(book_card(b, i) for i, b in enumerate(books_in('astrid-fitzgerald')))
    latest = ''.join(post_card(p) for p in POSTS[:3])
    body = f'''
<section class="hero">
  <div class="hero__bg" aria-hidden="true"></div>
  <div class="container hero__grid">
    <div class="hero__copy">
      {eyebrow('4-Time Award-Winning Author', 'reveal')}
      <h1 class="display hero__title reveal" style="--d:80ms"><span class="hero__name">Bree T. Wilson</span>Renowned Murder<br>Mystery Author</h1>
      <p class="hero__lead reveal" style="--d:160ms">Bree’s storytelling blends the cerebral thrill of riddles with the raw humanity of resilience, memory, and emotional depth.</p>
      <div class="hero__actions reveal" style="--d:240ms">{btn('Explore the Books', '/books/')}{btn('Watch the Intro', '#intro', 'ghost', arrow=False)}</div>
    </div>
    <div class="hero__portrait reveal" style="--d:200ms">
      <div class="arch">{img('bree-iiba-deadly-vows-hero', 'Bree T. Wilson receiving her International Impact Book Award for Deadly Vows: Echoes of College Crimes', eager=True)}</div>
      {img('distinguished-author-seal', 'International Impact Book Awards — Distinguished Author seal', 'hero__seal', w=600, h=600)}
    </div>
  </div>
  <a class="scroll-cue" href="#intro" aria-label="Scroll to the introduction"><span></span></a>
</section>

<section class="intro-film" id="intro">
  <div class="container">
    <div class="section-head reveal">
      <div>{eyebrow('Introduction')}<h2 class="display h2">A Short Film</h2></div>
    </div>
    <div class="intro-film__frame reveal" style="--d:80ms">
      <video controls playsinline preload="metadata" poster="/assets/img/site-intro-poster.jpg">
        <source src="/assets/video/site-intro.mp4" type="video/mp4">
      </video>
    </div>
  </div>
</section>

<section class="books-shelf" id="books">
  <div class="books-shelf__bg" aria-hidden="true"></div>
  <div class="container">
    <div class="section-head reveal">
      <div>{eyebrow('The Books')}<h2 class="display h2">The Hannah Walker<br>Mystery Series</h2></div>
      <a class="link-arrow" href="/books/">View All Books {ICONS['arrow']}</a>
    </div>
    <div class="book-grid">{hannah}</div>
    <div class="section-head series-follow reveal">
      <div>{eyebrow('In Development')}<h2 class="display h2">The Astrid Fitzgerald<br>Mystery Series</h2></div>
      <a class="link-arrow" href="/books/#astrid-fitzgerald">View the Series {ICONS['arrow']}</a>
    </div>
    <div class="book-grid book-grid--3">{astrid}</div>
  </div>
</section>

<section class="about-band">
  <div class="about-band__sketch" aria-hidden="true"></div>
  <div class="container about-band__grid">
    <figure class="about-band__photo reveal">{img('bree-iiba-backdrop', 'Bree T. Wilson at the International Impact Book Awards', w=610, h=814)}</figure>
    <div class="about-band__copy reveal" style="--d:120ms">
      {eyebrow('About Bree T. Wilson')}
      <h2 class="display h2 ink">A Passion for<br>Unraveling Truths</h2>
      <p>Bree T. Wilson is a four-time International Impact Book Awards Distinguished Author winner. Wilson began her writing journey in 2019 while studying Administration of Justice. Fueled by a deep fascination with mysteries and moral complexities, she found inspiration in her sharp-minded professor, R.G., whose quiet strength and intellect later became the blueprint for Rafael, a central figure in her debut novel.</p>
      <p>Her passion for unraveling truths—both hidden and haunting—guides her pursuit of modern mystery, echoing her dream of becoming a contemporary Sherlock Holmes.</p>
      {btn('Read More About Bree', '/about/')}
    </div>
    <p class="script-words reveal" style="--d:240ms" aria-hidden="true"><span>Riddles,</span><span>Resilience,</span><span>Memory,</span><span>Emotional Depth</span></p>
  </div>
</section>

<section class="awards-band">
  <div class="container awards-band__grid">
    <div class="reveal">
      {eyebrow('Awards')}
      <h2 class="display h2">International<br>Recognition</h2>
      <span class="rule rule--left" aria-hidden="true"></span>
      <p>Bree T. Wilson is a four-time International Impact Book Awards Distinguished Author winner, honored for <em>Paris Noir: Deadly Obsession</em> (2025), <em>Deadly Vows: Echoes of College Crimes</em>, <em>Deadly College Murders</em> and <em>The Thirteenth Riddle: A Poisoned Silence</em> (2026).</p>
      {btn('View Awards', '/awards/')}
    </div>
    <div class="award-badge reveal" style="--d:120ms">
      {laurel_svg()}
      <div class="award-badge__text"><small>International</small><strong>Impact</strong><small>Book Awards</small><em>4-Time</em><small>Award Winner</small>{ICONS['star']}</div>
    </div>
    <div class="awards-band__photos reveal" style="--d:220ms">
      <figure>{img('gala-red-carpet', 'Bree T. Wilson at the IIBA Gala 2026', w=1024, h=1536)}</figure>
      <figure>{img('cert-2025-paris-noir', '2025 International Impact Book Awards winner certificate for Paris Noir: Deadly Obsession', w=1079, h=760)}</figure>
    </div>
  </div>
</section>

<section class="latest">
  <div class="container">
    <div class="section-head reveal">
      <div>{eyebrow('From the Blog')}<h2 class="display h2">Behind the Riddles</h2></div>
      <a class="link-arrow" href="/blog/">All Posts {ICONS['arrow']}</a>
    </div>
    <div class="post-grid">{latest}</div>
  </div>
</section>

{newsletter_strip()}
{contact_strip()}'''
    schema = [{'@type': 'WebSite', '@id': SITE_URL + '/#website', 'url': SITE_URL + '/', 'name': SITE_NAME,
               'description': 'Official website of murder mystery author Bree T. Wilson', 'publisher': {'@id': SITE_URL + '/#author'}},
              PERSON, *series_schemas()]
    return layout('/', SITE_NAME, 'Official site of Bree T. Wilson, four-time International Impact Book Awards winner and author of the Hannah Walker and Astrid Fitzgerald mystery series.', body, '/', schema=schema, body_cls='is-home',
                  preload=['bree-iiba-deadly-vows-hero', 'bg-library'])


def about():
    paras = ''.join(f'<p>{p}</p>' for p in PAGES['about']['bio'])
    timeline = ''.join(f'<li class="reveal"><span class="tl-year">{esc(y)}</span><p>{t}</p></li>' for y, t in PAGES['about']['timeline'])
    body = f'''{page_hero('About Bree T. Wilson', 'The Author', 'bg-library', 'Renowned murder mystery author and creator of the Hannah Walker Mystery Series.')}
<section class="section about-main">
  <div class="container about-main__grid">
    <aside class="about-main__side reveal">
      <figure class="framed">{img('bree-iiba-backdrop', 'Bree T. Wilson at the International Impact Book Awards', w=610, h=814)}</figure>
      {img('distinguished-author-seal', 'Distinguished Author seal', 'about-main__seal', w=600, h=600)}
    </aside>
    <div class="prose prose--lead reveal" style="--d:120ms">{paras}<p class="signature"><img src="/assets/img/signature.png" alt="Bree T. Wilson’s signature" width="501" height="76" loading="lazy"></p></div>
  </div>
</section>
<section class="quote-band">
  <div class="container reveal">
    {ICONS['quote']}
    <blockquote>Now, she welcomes readers into a world where mystery pulses beneath every memory, love anchors every clue, and the power of family turns every page.</blockquote>
  </div>
</section>
<section class="section journey">
  <div class="container">
    <div class="section-head section-head--center reveal">{eyebrow('Milestones')}<h2 class="display h2">The Writing Journey</h2></div>
    <ol class="timeline">{timeline}</ol>
  </div>
</section>
<section class="section gallery-teaser">
  <div class="container gallery-teaser__grid">
    <figure class="reveal">{img('bree-nustant', 'Bree T. Wilson with her novel', w=1100, h=1467)}</figure>
    <figure class="reveal" style="--d:100ms">{img('gala-podium', 'Bree T. Wilson speaking at the IIBA gala', w=1024, h=1536)}</figure>
    <figure class="reveal" style="--d:200ms">{img('bree-impact-wall', 'Bree T. Wilson on the red carpet', w=1100, h=1467)}</figure>
  </div>
</section>
{newsletter_strip()}'''
    return layout('/about/', 'About the Author', 'Meet Bree T. Wilson, the four-time International Impact Book Awards winner who began writing in 2019 and created the Hannah Walker Mystery Series.', body, '/about/',
                  schema=[{'@type': 'ProfilePage', 'mainEntity': PERSON}], crumbs=[('About', '/about/')], og_type='profile', preload=['bg-library'])


def books_index():
    sections = []
    for series in series_ids():
        rows = []
        for i, b in enumerate(books_in(series)):
            soon = b['status'] == 'coming-soon'
            actions = btn('Learn More', book_url(b))
            if b['shop']:
                actions += btn(f'Buy on {b["shop"][0][0]}', b['shop'][0][1], 'ghost', ext=True)
            flag = f'<span class="book-card__flag">{esc(status_label(b))}</span>' if soon else ''
            rows.append(f'''<article class="book-row{' book-row--rev' if i % 2 else ''}">
  <a class="{cover_class(b, 'book-row__cover')} reveal" href="{book_url(b)}">{flag}{img(b['cover'], full_title(b) + ' book cover')}</a>
  <div class="book-row__copy reveal" style="--d:120ms">
    {eyebrow(series_kicker(b))}
    <h3 class="display h2">{esc(b['title'])}{f'<span class="subtitle">{esc(b["subtitle"])}</span>' if b['subtitle'] else ''}</h3>
    <p class="tagline">{esc(b['tagline'])}</p>
    <p>{b['blurb'][0]}</p>
    {award_html(b)}
    <div class="actions">{actions}</div>
  </div>
</article>''')
        note = '<p class="series-banner__note">Prospective titles. These books are still in development, and further titles will follow.</p>' if series == 'astrid-fitzgerald' else ''
        sections.append(f'''<header class="series-banner reveal" id="{series}">
  {eyebrow('In Development' if series == 'astrid-fitzgerald' else 'Series')}
  <h2 class="display h2">{esc(books_in(series)[0]['series_name'])}</h2>
  {note}
</header>
{''.join(rows)}''')
    body = f'''{page_hero('The Books', 'Riveting Mysteries', 'bg-tabletop', 'The Hannah Walker Mystery Series, and the Astrid Fitzgerald Mystery Series now in development.')}
<section class="section books-list"><div class="container">{''.join(sections)}</div></section>
{newsletter_strip()}'''
    return layout('/books/', 'Books: Hannah Walker and Astrid Fitzgerald', 'The Hannah Walker mysteries, plus the Astrid Fitzgerald series: six books still in development.', body, '/books/',
                  schema=series_schemas(), crumbs=[('Books', '/books/')], preload=['bg-tabletop'])


def book_page(b):
    sibs = books_in(b['series'])
    idx = sibs.index(b)
    soon = b['status'] == 'coming-soon'
    shop = ''.join(f'<a class="shop-btn" href="{esc(u)}" target="_blank" rel="noopener">{ICONS["book"]}<span>{esc(n)}</span></a>' for n, u in b['shop'])
    shop_block = (f'<div class="shop"><h2 class="mini-h">Shop Now</h2><div class="shop__grid">{shop}</div></div>' if shop
                  else f'<div class="shop"><h2 class="mini-h">{esc(status_label(b))}</h2><p class="muted">Join the newsletter to hear the moment it’s released.</p>' + btn('Join the Newsletter', '/newsletter/') + '</div>')
    blurb = ''.join(f'<p>{p}</p>' for p in b['blurb'])
    sections = []
    if b['teaser']:
        lines = '<br>'.join(b['teaser']['lines'])
        sections.append(f'''<section class="teaser"><div class="container reveal">
  {eyebrow(b['teaser']['title'])}
  <p class="teaser__verse">{lines}</p>
</div></section>''')
    if b['trailer'] or b['reviews']:
        trailer = ''
        if b['trailer']:
            trailer = f'''<div class="trailer reveal">
      {eyebrow('Watch the Trailer')}
      <div class="trailer__frame"><video controls preload="none" playsinline poster="/assets/img/{b['trailer']}-poster.jpg"><source src="/assets/video/{b['trailer']}.mp4" type="video/mp4"></video></div>
    </div>'''
        reviews = ''.join(f'''<figure class="review reveal" style="--d:120ms">
      {eyebrow('Reviews')}
      <div class="stars" aria-label="5 out of 5 stars">{ICONS['star'] * 5}</div>
      <blockquote>“{esc(q)}”</blockquote><figcaption>{esc(who)}</figcaption>
    </figure>''' for q, who in b['reviews'])
        sections.append(f'<section class="section media-band"><div class="container media-band__grid">{trailer}{reviews}</div></section>')
    if b['characters']:
        chars = ''.join(f'''<article class="char-card reveal" style="--d:{(i % 3) * 90}ms">
      <span class="char-card__no">{i + 1:02d}</span><h3>{esc(n)}</h3><p>{t}</p></article>''' for i, (n, t) in enumerate(b['characters']))
        sections.append(f'''<section class="section characters"><div class="container">
  <div class="section-head section-head--center reveal">{eyebrow('The Cast')}<h2 class="display h2">Meet the Characters</h2></div>
  <div class="char-grid">{chars}</div></div></section>''')
    prev_b, next_b = sibs[idx - 1] if idx else None, sibs[idx + 1] if idx + 1 < len(sibs) else None
    pager = '<nav class="book-pager container" aria-label="More books">'
    pager += f'<a class="prev" href="{book_url(prev_b)}"><small>Previous Book</small>{esc(full_title(prev_b))}</a>' if prev_b else '<span></span>'
    pager += f'<a class="next" href="{book_url(next_b)}"><small>Next Book</small>{esc(full_title(next_b))}</a>' if next_b else '<span></span>'
    pager += '</nav>'
    body = f'''<section class="book-hero">
  <div class="book-hero__bg" style="background-image:url('/assets/img/{b['bg']}.webp')" aria-hidden="true"></div>
  <div class="container book-hero__grid">
    <div class="{cover_class(b, 'book-hero__cover')} reveal">{f'<span class="book-card__flag">{esc(status_label(b))}</span>' if soon else ''}{img(b['cover'], full_title(b) + ' book cover', eager=True)}</div>
    <div class="book-hero__copy reveal" style="--d:120ms">
      {eyebrow(series_kicker(b))}
      <h1 class="display">{esc(b['title'])}{f'<span class="subtitle">{esc(b["subtitle"])}</span>' if b['subtitle'] else ''}</h1>
      <p class="tagline">{esc(b['tagline'])}</p>
      {award_html(b)}
      {shop_block}
    </div>
  </div>
</section>
<section class="section book-blurb"><div class="container"><div class="prose prose--book reveal">{blurb}</div></div></section>
{''.join(sections)}
{pager}
{newsletter_strip()}'''
    desc = f'{full_title(b)} ({b["series_name"].removesuffix(" Series")}, Book {b["series_no"]}) by Bree T. Wilson. ' + re.sub(r'<[^>]+>', '', b['blurb'][0])
    extra = (f'<meta property="book:author" content="{SITE_URL}/about">\n'
             + (f'<meta property="book:isbn" content="{b["isbn"]}">\n' if b.get('isbn') else '')
             + (f'<meta property="book:release_date" content="{b["published"]}">\n' if b.get('published') else ''))
    return layout(book_url(b), full_title(b), desc, body, '/books/', schema=[book_schema(b, full=True)],
                  crumbs=[('Books', '/books/'), (full_title(b), book_url(b))], og_image=b['og'], og_type='book',
                  preload=[b['bg']], extra_meta=extra)


def awards():
    wins = ''.join(f'''<article class="win-card reveal" style="--d:{i * 90}ms">
  <button class="win-card__img" data-zoom="/assets/img/{c}.webp" aria-label="View certificate: {esc(t)}">{img(c, t + ' — award certificate')}</button>
  <div><p class="eyebrow">{esc(y)}</p><h3>{esc(t)}</h3><p>{esc(d)}</p></div>
</article>''' for i, (y, t, d, c) in enumerate(PAGES['awards']['wins']))
    gallery = ''.join(f'<button class="g-item reveal" data-zoom="/assets/img/{n}.webp" data-caption="{esc(a)}" aria-label="View photo: {esc(a)}">{img(n, a)}</button>' for n, a in PAGES['awards']['gallery'])
    body = f'''{page_hero('Awards', 'International Impact Book Awards', 'bg-library', 'A four-time International Impact Book Awards Distinguished Author winner.')}
<section class="section awards-intro">
  <div class="container awards-intro__grid">
    <div class="award-badge award-badge--lg reveal">{laurel_svg()}<div class="award-badge__text"><small>International</small><strong>Impact</strong><small>Book Awards</small><em>4-Time</em><small>Award Winner</small>{ICONS['star']}</div></div>
    <div class="prose reveal" style="--d:120ms">{''.join(f'<p>{p}</p>' for p in PAGES['awards']['intro'])}</div>
  </div>
</section>
<section class="section wins"><div class="container">
  <div class="section-head section-head--center reveal">{eyebrow('Honors')}<h2 class="display h2">Award-Winning Books</h2></div>
  <div class="win-grid">{wins}</div>
</div></section>
<section class="section gallery"><div class="container">
  <div class="section-head section-head--center reveal">{eyebrow('Photo Gallery')}<h2 class="display h2">IIBA Gala 2026</h2></div>
  <div class="masonry" data-gallery>{gallery}</div>
</div></section>
{contact_strip()}'''
    return layout('/awards/', 'Awards', 'Bree T. Wilson’s four International Impact Book Awards wins for the Hannah Walker Mystery Series, with certificates and photos from the IIBA Gala 2026.', body, '/awards/',
                  crumbs=[('Awards', '/awards/')], preload=['bg-library'])


TITLE_PATTERNS = {
    'the-thirteenth-riddle-a-poisoned-silence': r'(?:The )?Thirteenth Riddle',
    'who-murdered-erica-ivy': r'Who Murdered Erica I(?:vy)?',
}
BOOK_PATTERNS = [(b, re.compile(TITLE_PATTERNS.get(b['slug'], re.escape(b['title'])))) for b in BOOKS]


def post_book(p):
    """The book a post is mainly about: first one named in its title, else in its text."""
    for text in (p['title'], p['html']):
        hits = [(m.start(), b) for b, rx in BOOK_PATTERNS for m in [rx.search(text)] if m]
        if hits:
            return min(hits, key=lambda h: h[0])[1]
    return None


def link_books(h):
    """Links the first plain-text mention of each book in a post to its book page."""
    done, out, skip = set(), [], 0
    for part in re.split(r'(<[^>]+>)', h):
        if part.startswith('<'):
            tag = re.match(r'</?(\w+)', part)
            if tag and tag.group(1) in ('a', 'h2', 'h3'):
                skip += -1 if part.startswith('</') else 1
            out.append(part)
            continue
        if not skip:
            for b, rx in BOOK_PATTERNS:
                if b['slug'] in done:
                    continue
                m = rx.search(part)
                if m:
                    part = part[:m.start()] + f'<a href="{book_url(b)}">{m.group(0)}</a>' + part[m.end():]
                    done.add(b['slug'])
                    break
        out.append(part)
    return ''.join(out)


def blog_pages():
    pages = []
    # Page 1 leads with one featured post, so it carries one extra to keep the 3-column grid full.
    first = POSTS_PER_PAGE + 1
    chunks = [POSTS[:first]] + [POSTS[i:i + POSTS_PER_PAGE] for i in range(first, len(POSTS), POSTS_PER_PAGE)]
    total = len(chunks)
    for n, chunk in enumerate(chunks, 1):
        cards = ''.join(post_card(p, big=(n == 1 and i == 0)) for i, p in enumerate(chunk))
        nav = '<nav class="pagination" aria-label="Blog pages">'
        for k in range(1, total + 1):
            href = '/blog/' if k == 1 else f'/blog/page/{k}/'
            nav += f'<a href="{href}"{" aria-current=page" if k == n else ""}>{k}</a>'
        nav += '</nav>'
        path = '/blog/' if n == 1 else f'/blog/page/{n}/'
        body = f'''{page_hero('Blog', 'Notes from the Author', 'bg-desk', 'Character profiles, behind-the-scenes stories and award news from the Hannah Walker Mystery Series.')}
<section class="section blog-list"><div class="container"><div class="post-grid post-grid--blog">{cards}</div>{nav}</div></section>
{newsletter_strip()}'''
        pages.append((path, layout(path, 'Blog' + (f' — Page {n}' if n > 1 else ''), 'The Bree T. Wilson blog: character profiles, behind-the-scenes stories and award news from the Hannah Walker Mystery Series' + (f' (page {n}).' if n > 1 else '.'), body, '/blog/',
                                   crumbs=[('Blog', '/blog/')] + ([(f'Page {n}', path)] if n > 1 else []), preload=['bg-desk'])))
    for i, p in enumerate(POSTS):
        content = p['html'].replace('src="IMG/', 'src="/assets/img/blog-').replace('<img ', '<img loading="lazy" ')
        content = re.sub(r'src="/assets/img/blog-([^"]+)\.(png|jpe?g|webp)"', r'src="/assets/img/blog-\1.webp"', content)
        content = re.sub(r'<img loading="lazy" src="/assets/img/(blog-[^"]+)\.webp" alt="[^"]*">',
                         lambda m: img(m.group(1), p['title']), content)
        content = link_books(content)
        book = post_book(p)
        newer, older = (POSTS[i - 1] if i else None), (POSTS[i + 1] if i + 1 < len(POSTS) else None)
        pager = '<nav class="post-pager" aria-label="More posts">'
        pager += f'<a class="prev" href="/blog/{older["slug"]}/"><small>Older Post</small>{esc(older["title"])}</a>' if older else '<span></span>'
        pager += f'<a class="next" href="/blog/{newer["slug"]}/"><small>Newer Post</small>{esc(newer["title"])}</a>' if newer else '<span></span>'
        pager += '</nav>'
        related = [q for q in POSTS if q is not p and book and post_book(q) is book][:3] or [q for q in POSTS if q is not p][:3]
        rel = ''.join(f'<li><a href="/blog/{q["slug"]}/"><time datetime="{q["date"]}">{fmt_date(q["date"])}</time>{esc(q["title"])}</a></li>' for q in related)
        side = ''
        for series in series_ids():
            items = ''.join(f'<li><a href="{book_url(b)}">{img(b["flat"], full_title(b) + " cover")}<span>{esc(full_title(b))}</span></a></li>' for b in books_in(series))
            side += f'<h2 class="mini-h">{esc(series_short(series))}</h2><ul class="mini-books">{items}</ul>'
        body = f'''<section class="post-hero">
  <div class="page-hero__bg" style="background-image:url('/assets/img/bg-desk.webp')" aria-hidden="true"></div>
  <div class="container post-hero__inner reveal">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/blog/">Blog</a></nav>
    <time datetime="{p['date']}">{fmt_date(p['date'])}</time>
    <h1 class="h-serif">{esc(p['title'])}</h1>
    <p class="byline">By <a href="/about/">Bree T. Wilson</a>{f' · <a href="{book_url(book)}">{esc(full_title(book))}</a>' if book else ''}</p>
  </div>
</section>
<section class="section post"><div class="container post__grid">
  <article class="prose prose--post">{content}
    <div class="related"><h2 class="mini-h">{'More on ' + esc(book['short']) if book else 'More from the Blog'}</h2><ul>{rel}</ul></div>
    {pager}</article>
  <aside class="post__side">{side}
    <div class="side-nl"><h2 class="mini-h">Newsletter</h2><p>Get new book announcements and the occasional update.</p>{btn('Sign Up', '/newsletter/')}</div></aside>
</div></section>'''
        url = clean_url(f'/blog/{p["slug"]}/')
        og = book['og'] if book else 'og.jpg'
        schema = [{'@type': 'BlogPosting', 'headline': p['title'][:110], 'datePublished': p['date'], 'dateModified': p['date'],
                   'description': meta_desc(p['excerpt']), 'image': f'{SITE_URL}/assets/img/{og}', 'url': url,
                   'mainEntityOfPage': url, 'author': {'@type': 'Person', 'name': 'Bree T. Wilson', 'url': SITE_URL + '/about'},
                   'publisher': {'@type': 'Person', 'name': 'Bree T. Wilson', 'url': SITE_URL + '/'},
                   **({'about': {'@type': 'Book', 'name': full_title(book), 'url': clean_url(book_url(book))}} if book else {})}]
        extra = f'<meta property="article:published_time" content="{p["date"]}">\n<meta property="article:author" content="{SITE_URL}/about">\n'
        pages.append((f'/blog/{p["slug"]}/', layout(f'/blog/{p["slug"]}/', p['seo_title'], p['excerpt'], body, '/blog/', schema=schema,
                                                     crumbs=[('Blog', '/blog/'), (p['title'], f'/blog/{p["slug"]}/')],
                                                     og_image=og, og_type='article', extra_meta=extra)))
    return pages


def newsletter():
    body = f'''{page_hero('Join My Mailing List', 'Newsletter', 'bg-library', '', small=True)}
<section class="section nl-page">
  <div class="container nl-page__grid">
    <div class="nl-page__covers reveal" aria-hidden="true">{''.join(img(b['cover'], '') for b in books_in('hannah-walker')[:3])}</div>
    <div class="nl-card reveal" style="--d:120ms">
      {eyebrow('Newsletter')}
      <h2 class="display h2">Be the First to Know</h2>
      <p>Get new book announcements and the occasional update.</p>
      {newsletter_form('page')}
    </div>
  </div>
</section>'''
    return layout('/newsletter/', 'Newsletter', 'Join Bree T. Wilson’s mailing list for new book announcements and the occasional update from the Hannah Walker Mystery Series.', body, '/newsletter/',
                  crumbs=[('Newsletter', '/newsletter/')])


def contact():
    body = f'''{page_hero('Contact Bree T. Wilson', 'Contact', 'bg-library', 'Have a question or just want to say hello? I’d love to hear from you!', small=True)}
<section class="section contact-page">
  <div class="container contact-page__grid">
    <aside class="contact-aside reveal">
      <h2 class="h-serif">Get in Touch</h2>
      <p>You can also email me with any questions, and I invite you to explore and follow my social media channels.</p>
      <a class="contact-mail" href="mailto:{EMAIL}">{ICONS['mail']}<span>{EMAIL}</span></a>
      {social_links('social social--lg')}
      <a class="press-card" href="{PRESS_RELEASE}" target="_blank" rel="noopener"><small>Media</small>Author Press Release {ICONS['arrow']}</a>
    </aside>
    <form class="contact-form reveal" style="--d:120ms" data-form="contact" action="{FORM_ENDPOINT}" method="POST" novalidate>
      <input type="hidden" name="_subject" value="New message from breetwilson.com">
      <input type="hidden" name="_template" value="table">
      <input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
      <fieldset><legend>Name <em>(required)</em></legend>
        <div class="row2">
          <label>First Name<input name="first_name" required autocomplete="given-name"></label>
          <label>Last Name<input name="last_name" required autocomplete="family-name"></label>
        </div></fieldset>
      <label>Email <em>(required)</em><input type="email" name="email" required autocomplete="email"></label>
      <label>Subject <em>(required)</em><input name="subject" required></label>
      <label>Message <em>(required)</em><textarea name="message" rows="6" required></textarea></label>
      <button type="submit" class="btn btn-gold"><span>Submit</span>{ICONS['arrow']}</button>
      <p class="form-note" role="status" aria-live="polite"></p>
    </form>
  </div>
</section>'''
    return layout('/contact/', 'Contact', 'Contact murder mystery author Bree T. Wilson with questions, media and press requests, or just to say hello.', body, '/contact/',
                  schema=[{'@type': 'ContactPage', 'about': {'@id': SITE_URL + '/#author'}}], crumbs=[('Contact', '/contact/')])


def welcome():
    w = PAGES['welcome']
    body = f'''{page_hero('Welcome!', 'A Note from Bree', 'bg-desk', '', small=True)}
<section class="section welcome">
  <div class="container welcome__grid">
    <figure class="welcome__cover reveal">{img('paris-noir-flat', 'Paris Noir: Deadly Obsession cover', w=366, h=467)}</figure>
    <div class="prose prose--lead reveal" style="--d:120ms">{''.join(f'<p>{p}</p>' for p in w)}
      <p class="signature"><img src="/assets/img/signature.png" alt="Bree T. Wilson" width="501" height="76"></p>
      <p><a class="contact-mail" href="mailto:{EMAIL}">{ICONS['mail']}<span>{EMAIL}</span></a></p>
    </div>
  </div>
</section>
{newsletter_strip()}'''
    return layout('/welcome/', 'Welcome', 'A welcome note from Bree T. Wilson, the award-winning murder mystery author behind the Hannah Walker Mystery Series.', body, crumbs=[('Welcome', '/welcome/')])


def legal(key, path, title):
    d = PAGES[key]
    blocks = [f'<p class="effective">{esc(d["effective"])}</p>']
    for sec in d['sections']:
        if sec[0]:
            blocks.append(f'<h2>{esc(sec[0])}</h2>')
        for para in sec[1:]:
            if isinstance(para, list):
                blocks.append('<ul>' + ''.join(f'<li>{esc(x)}</li>' for x in para) + '</ul>')
            else:
                blocks.append(f'<p>{para}</p>')
    body = f'''{page_hero(title, 'Legal', 'bg-library', '', small=True)}
<section class="section"><div class="container"><div class="prose prose--legal">{''.join(blocks)}</div></div></section>'''
    return layout(path, title, f'{title} for breetwilson.com, the official website of author Bree T. Wilson ({d["effective"]}).', body, crumbs=[(title, path)])


def not_found():
    body = f'''<section class="nf">
  <div class="page-hero__bg" style="background-image:url('/assets/img/bg-library.webp')" aria-hidden="true"></div>
  <div class="container nf__inner">
    {eyebrow('Error 404')}
    <h1 class="display">This Page Has Vanished</h1>
    <p>Every clue leads somewhere—just not here. Try one of these instead.</p>
    <div class="actions">{btn('Back Home', '/')}{btn('Explore the Books', '/books/', 'ghost', arrow=False)}</div>
  </div>
</section>'''
    return layout('/404.html', 'Page Not Found', 'The page you were looking for could not be found. Explore the Hannah Walker Mystery Series by award-winning author Bree T. Wilson instead.', body, noindex=True)


# ---------------------------------------------------------------- write

def page_file(path):
    """Logical page path -> output file: / -> index.html, /about/ -> about.html,
    /blog/page/2/ -> blog/page-2.html, /blog/slug/ -> blog/slug.html."""
    if path == '/':
        return 'index.html'
    if path.endswith('.html'):
        return path.strip('/')
    path = re.sub(r'^/blog/page/(\d+)/$', r'/blog/page-\1/', path)
    return path.strip('/') + '.html'


def localize(content, path):
    """Rewrites root-relative links (/about/, /assets/...) for the chosen output mode."""
    here = Path(page_file(path)).parent

    def target(url):
        url, frag = (url.split('#', 1) + [''])[:2]
        frag = '#' + frag if frag else ''
        if url.startswith('/assets/') or url.endswith(('.xml', '.txt')):
            f = url.lstrip('/')
        else:
            f = page_file(url if url.endswith('/') or url.endswith('.html') else url + '/')
        if DEPLOY:  # clean, root-relative URLs on the live host
            return ('/' + f[:-5] if f.endswith('.html') else '/' + f).replace('/index', '/') + frag
        return os.path.relpath(f, here).replace(os.sep, '/') + frag

    content = re.sub(r'((?:href|src|poster|data-zoom)=")(/(?!/)[^"]*)"', lambda m: m.group(1) + target(m.group(2)) + '"', content)
    return re.sub(r"url\('(/assets/[^']+)'\)", lambda m: f"url('{target(m.group(1))}')", content)


def write(path, content):
    dest = OUT / page_file(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(localize(content, path), encoding='utf-8')
    return path


HTACCESS = r'''# Bree T. Wilson — Apache rules (clean URLs that match the old Squarespace links)
Options -MultiViews -Indexes
DirectoryIndex index.html
ErrorDocument 404 /404.html

<IfModule mod_rewrite.c>
RewriteEngine On
# Force https + www
RewriteCond %{HTTPS} off [OR]
RewriteCond %{HTTP_HOST} !^www\. [NC]
RewriteRule ^ https://www.breetwilson.com%{REQUEST_URI} [R=301,L,NE]
# /page.html -> /page and /index.html -> /
RewriteCond %{THE_REQUEST} \s/+(.*?)index\.html[\s?] [NC]
RewriteRule ^ /%1 [R=301,L,NE]
RewriteCond %{THE_REQUEST} \s/+(.+?)\.html[\s?] [NC]
RewriteRule ^ /%1 [R=301,L,NE]
# drop trailing slashes (old links like /about/)
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.+)/$ /$1 [R=301,L]
# serve /page from page.html
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME}.html -f
RewriteRule ^(.+)$ $1.html [L]
</IfModule>

<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType image/webp "access plus 1 year"
ExpiresByType image/jpeg "access plus 1 year"
ExpiresByType image/png "access plus 1 year"
ExpiresByType video/mp4 "access plus 1 year"
ExpiresByType text/css "access plus 1 month"
ExpiresByType application/javascript "access plus 1 month"
</IfModule>
<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE text/html text/css application/javascript image/svg+xml application/xml
</IfModule>
'''


def main():
    for d in list(OUT.iterdir()) if OUT.exists() else []:
        if d.name not in ('assets',) and d.is_dir():
            shutil.rmtree(d)
        elif d.is_file() and d.suffix in ('.html', '.xml', '.txt'):
            d.unlink()
    built = [write('/', home()), write('/about/', about()), write('/books/', books_index()),
             write('/awards/', awards()), write('/newsletter/', newsletter()), write('/contact/', contact()),
             write('/welcome/', welcome()),
             write('/privacy-policy/', legal('privacy', '/privacy-policy/', 'Privacy Policy')),
             write('/terms-and-conditions/', legal('terms', '/terms-and-conditions/', 'Terms and Conditions')),
             write('/404.html', not_found())]
    built += [write(book_url(b), book_page(b)) for b in BOOKS]
    built += [write(p, c) for p, c in blog_pages()]
    today = date.today().isoformat()
    post_dates = {f'/blog/{p["slug"]}/': p['date'] for p in POSTS}
    rows = []
    for u in built:
        if u.endswith('.html'):
            continue
        prio = '1.0' if u == '/' else '0.9' if u in ('/books/', '/about/') or u in [book_url(b) for b in BOOKS] else '0.6' if u.startswith('/blog/') else '0.7'
        rows.append(f'  <url><loc>{clean_url(u)}</loc><lastmod>{post_dates.get(u, today)}</lastmod><priority>{prio}</priority></url>\n')
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + ''.join(rows) + '</urlset>\n', encoding='utf-8')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {SITE_URL}/sitemap.xml\n', encoding='utf-8')
    (OUT / '.htaccess').write_text(HTACCESS, encoding='utf-8')
    # Netlify / Cloudflare Pages: serve pretty URLs, old Squarespace paths keep working
    (OUT / '_redirects').write_text(
        '/home            /                301\n'
        '/index           /                301\n'
        '/cart            /books           301\n'
        '/books/*         /books           301\n'
        '/blog/:slug/     /blog/:slug      301\n'
        '/:page/          /:page           301\n'
        '/*               /404.html        404\n', encoding='utf-8')
    print(f'Built {len(built)} pages into {OUT} ({"deploy: clean URLs" if DEPLOY else "relative .html links"})')


if __name__ == '__main__':
    main()

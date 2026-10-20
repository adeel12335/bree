"""Optimises the scraped photos, book covers and Figma AI backgrounds into
public/assets/img (WebP) and re-encodes the trailers into public/assets/video."""
import shutil, subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / 'source' / 'media'
AI = ROOT / 'source' / 'ai'
OUT = ROOT / 'public' / 'assets' / 'img'
VID = ROOT / 'public' / 'assets' / 'video'
OUT.mkdir(parents=True, exist_ok=True)
VID.mkdir(parents=True, exist_ok=True)

# (source, output name, max width, quality)
JOBS = [
    # Figma AI backgrounds (no people)
    (AI / 'library.png', 'bg-library', 2000, 74),
    (AI / 'tabletop.png', 'bg-tabletop', 2000, 74),
    (AI / 'paris-sketch.png', 'paris-sketch', 900, 76),
    (AI / 'campus.png', 'bg-campus', 2000, 72),
    (AI / 'chapel.png', 'bg-chapel', 2000, 72),
    (AI / 'paris-night.png', 'bg-paris-night', 2000, 72),
    (AI / 'train.png', 'bg-train', 2000, 72),
    (AI / 'desk.png', 'bg-desk', 2000, 72),
    # Book covers (original site)
    (MEDIA / 'img' / 'Deadly-College-Murders-3d-Book-Cover.png', 'cover-deadly-college-murders', 700, 86),
    (MEDIA / 'img' / 'Deadly-Vows-3d-Cover.png', 'cover-deadly-vows', 700, 86),
    (MEDIA / 'img' / 'Paris-Noir-3d-cover.png', 'cover-paris-noir', 700, 86),
    (MEDIA / 'img' / '1000014795.jpeg', 'cover-thirteenth-riddle', 900, 82),
    (MEDIA / 'img' / 'Screenshot-2026-02-15-192725-deadky-ibsessiinb.png', 'paris-noir-flat', 500, 84),
    # Photos & awards (original site)
    (MEDIA / 'img' / 'IIBA.png', 'bree-iiba-backdrop', 900, 82),
    (MEDIA / 'img' / '1000014852.jpg', 'bree-gala-portrait', 1024, 82),
    (MEDIA / 'img' / '1000014841.jpg', 'gala-red-carpet', 1024, 80),
    (MEDIA / 'img' / '1000014853.jpg', 'gala-red-carpet-2', 1024, 80),
    (MEDIA / 'img' / '1000014848.jpg', 'gala-podium', 1024, 80),
    (MEDIA / 'img' / '1000014842.jpg', 'gala-award-1', 1024, 80),
    (MEDIA / 'img' / '1000014843.jpg', 'gala-award-2', 1024, 80),
    (MEDIA / 'img' / 'IMG_7889.jpeg', 'bree-nustant', 1100, 80),
    (MEDIA / 'img' / 'IMG_7963.jpeg', 'bree-impact-wall', 1100, 80),
    (MEDIA / 'img' / 'IMG_7964.jpeg', 'bree-impact-wall-2', 1100, 80),
    (MEDIA / 'img' / 'IMG_7969.jpeg', 'bree-press-wall', 1100, 80),
    (MEDIA / 'img' / 'IMG_7970.jpeg', 'bree-press-wall-2', 1100, 80),
    (MEDIA / 'img' / '2026_07_20_IIBA-1549.jpg', 'iiba-2026-thai-tiger', 1400, 80),
    (MEDIA / 'img' / '2026_07_20_IIBA-2139.jpg', 'iiba-2026-stage', 1400, 80),
    (MEDIA / 'img' / 'Screenshot_20251022_122258_Gmail.jpg', 'cert-2025-paris-noir', 1079, 84),
    (MEDIA / 'img' / 'Bree-T-Wilson.png', 'cert-deadly-college-murders', 1400, 84),
    (MEDIA / 'img' / 'Bree-T-Wilson-(2).png', 'cert-thirteenth-riddle', 1400, 84),
    (MEDIA / 'img' / '56-(1).png', 'cert-deadly-vows', 1400, 84),
    (MEDIA / 'img' / 'Digital-Sticker.png', 'distinguished-author-seal', 600, 86),
    # Flat covers: DCM from the site's blog, Deadly Vows from Smashwords (the publisher's listing)
    (MEDIA / 'img' / 'DCM-flat-cover.jpg', 'flat-deadly-college-murders', 700, 84),
    (MEDIA / 'img' / 'DV-flat.jpg', 'flat-deadly-vows', 700, 84),
    (MEDIA / 'img' / 'PN-flat-cover.png', 'flat-paris-noir-wrap', 608, 84),
]


def save(src, name, width, q):
    im = Image.open(src)
    im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
    if im.mode == 'RGBA' and im.getchannel('A').getextrema()[0] == 255:
        im = im.convert('RGB')
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    dest = OUT / f'{name}.webp'
    im.save(dest, 'WEBP', quality=q, method=6)
    return im.size, dest.stat().st_size


for src, name, w, q in JOBS:
    size, nbytes = save(src, name, w, q)
    print(f'{name:32} {size} {nbytes // 1024} KB')

for f in (MEDIA / 'blog').glob('*'):
    size, nbytes = save(f, 'blog-' + f.stem, 1200, 80)
    print(f'blog-{f.stem:27} {size} {nbytes // 1024} KB')

# Client-supplied photo (IIBA award for Deadly Vows): trim the screenshot bars, then a
# full version for the gallery and an arch-shaped crop (both people) for the home hero.
award = Image.open(MEDIA / 'img' / 'iiba-deadly-vows-award.png').convert('RGB').crop((0, 30, 1080, 744))
award.save(OUT / 'iiba-deadly-vows-award.webp', 'WEBP', quality=86, method=6)
award.crop((205, 0, 715, 714)).save(OUT / 'bree-iiba-deadly-vows-hero.webp', 'WEBP', quality=88, method=6)
award.crop((205, 0, 715, 714)).save(MEDIA / 'img' / 'bree-hero-crop.png')

# Bree's handwritten signature (from the site's share image) -> gold on transparent
sig = Image.open(MEDIA / 'img' / 'Home-Bree-T-Wilson.png').convert('L')
sig = sig.crop(sig.point(lambda v: 255 if v < 140 else 0).getbbox())
alpha = sig.point(lambda v: max(0, min(255, (215 - v) * 2)))
gold = Image.new('RGBA', sig.size, (230, 201, 135, 0))
gold.putalpha(alpha)
gold.save(OUT / 'signature.png', optimize=True)

# Social share images (1200x630): site default + one per book
from PIL import ImageDraw, ImageFilter, ImageFont
SERIF = 'C:/Windows/Fonts/georgia.ttf'


def share_card(cover, title, line2, out):
    bg = Image.open(AI / 'library.png').convert('RGB').resize((1200, 675)).crop((0, 22, 1200, 652))
    bg = Image.blend(bg, Image.new('RGB', bg.size, (10, 9, 8)), .45)
    c = Image.open(cover).convert('RGBA')
    c.thumbnail((440, 540))
    shadow = Image.new('RGBA', bg.size, 0)
    x, y = 1200 - c.width - 90, (630 - c.height) // 2
    ImageDraw.Draw(shadow).rectangle((x + 10, y + 20, x + c.width + 10, y + c.height + 20), fill=(0, 0, 0, 170))
    bg = Image.alpha_composite(bg.convert('RGBA'), shadow.filter(ImageFilter.GaussianBlur(18)))
    bg.alpha_composite(c, (x, y))
    d = ImageDraw.Draw(bg)
    d.text((80, 150), 'BREE T. WILSON', font=ImageFont.truetype(SERIF, 26), fill=(201, 163, 90), spacing=8)
    f = ImageFont.truetype(SERIF, 58)
    yy = 200
    for ln in title:
        d.text((80, yy), ln, font=f, fill=(243, 236, 224)); yy += 70
    d.line((82, yy + 18, 160, yy + 18), fill=(201, 163, 90), width=2)
    d.text((80, yy + 40), line2, font=ImageFont.truetype(SERIF, 26), fill=(214, 204, 186))
    bg.convert('RGB').save(OUT / out, quality=84)


share_card(MEDIA / 'img' / 'bree-hero-crop.png', ['Murder Mystery', 'Author'], '4-time International Impact Book Award winner', 'og.jpg')
share_card(MEDIA / 'img' / 'Deadly-College-Murders-3d-Book-Cover.png', ['Deadly College', 'Murders'], 'Book 1 · The Hannah Walker Mystery Series', 'og-deadly-college-murders.jpg')
share_card(MEDIA / 'img' / 'Deadly-Vows-3d-Cover.png', ['Deadly Vows'], 'Echoes of College Crimes · Hannah Walker Book 2', 'og-deadly-vows.jpg')
share_card(MEDIA / 'img' / 'Paris-Noir-3d-cover.png', ['Paris Noir'], 'Deadly Obsession · Hannah Walker Book 3', 'og-paris-noir.jpg')
share_card(MEDIA / 'img' / '1000014795.jpeg', ['The Thirteenth', 'Riddle'], 'A Poisoned Silence · Hannah Walker Book 4', 'og-thirteenth-riddle.jpg')

# Touch icon
icon = Image.new('RGB', (180, 180), (18, 16, 14))
d = ImageDraw.Draw(icon)
d.rounded_rectangle((10, 10, 170, 170), 22, outline=(201, 163, 90), width=3)
d.text((90, 94), 'BW', font=ImageFont.truetype(SERIF, 78), fill=(230, 201, 135), anchor='mm')
icon.save(OUT / 'apple-touch-icon.png')

# Trailers: 720p H.264 + poster frame
for src, name in [('trailer-deadly-college-murders.mp4', 'trailer-deadly-college-murders'),
                  ('trailer-deadly-vows.mp4', 'trailer-deadly-vows')]:
    mp4 = VID / f'{name}.mp4'
    if not mp4.exists():
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(MEDIA / src), '-vf', 'scale=-2:720',
                        '-c:v', 'libx264', '-crf', '26', '-preset', 'slow', '-c:a', 'aac', '-b:a', '128k',
                        '-movflags', '+faststart', str(mp4)], check=True)
    poster = OUT / f'{name}-poster.jpg'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '4', '-i', str(mp4), '-frames:v', '1',
                    '-q:v', '4', str(poster)], check=True)
    print(name, mp4.stat().st_size // 1024, 'KB')

"""Builds the homepage intro from the real covers and the IIBA photograph.

Run: python tools/make_intro.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / 'public' / 'assets' / 'img'
VID = ROOT / 'public' / 'assets' / 'video'
FONT = Path(r'C:\Windows\Fonts\georgiab.ttf')
FONT_I = Path(r'C:\Windows\Fonts\georgiai.ttf')
W, H = 2560, 1440
INK = (11, 10, 9)
GOLD = (201, 163, 90)
CREAM = (243, 236, 224)
MUTED = (178, 168, 149)

AWARDS = IMG / 'iiba-gala-wide.jpg'


def font(size, italic=False):
    return ImageFont.truetype(str(FONT_I if italic else FONT), size)


def tracked(draw, text, fnt, y, fill, tracking, cx=W / 2):
    widths = [fnt.getlength(ch) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = cx - total / 2
    for ch, width in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += width + tracking


def vignette(im):
    overlay = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(overlay)
    d.ellipse((-180, -120, W + 180, H + 120), fill=255)
    overlay = overlay.filter(ImageFilter.GaussianBlur(90))
    dark = Image.new('RGB', (W, H), (0, 0, 0))
    return Image.composite(im, dark, overlay)


def canvas():
    im = Image.new('RGB', (W, H), INK)
    glow = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(glow)
    d.ellipse((W * 0.2, H * 0.15, W * 0.8, H * 0.9), fill=(32, 26, 18))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    return Image.blend(im, glow, 0.85)


def rule(draw, y, width=420):
    x = (W - width) / 2
    draw.line((x, y, x + width, y), fill=GOLD, width=2)
    draw.ellipse((W / 2 - 4, y - 4, W / 2 + 4, y + 4), fill=GOLD)


def trim(im):
    im = im.convert('RGBA')
    mask = im.getchannel('A').point(lambda p: 255 if p > 16 else 0)
    box = mask.getbbox()
    return im.crop(box) if box else im


def load_cover(name, height):
    im = trim(Image.open(IMG / f'{name}.webp'))
    im = im.resize((round(im.width * height / im.height), height), Image.Resampling.LANCZOS)
    return im


def paste(base, im, xy):
    base.paste(im, xy, im if im.mode == 'RGBA' else None)


def row_of(names, height, y, margin=120):
    covers = [load_cover(n, height) for n in names]
    gap = 48
    total = sum(c.width for c in covers) + gap * (len(covers) - 1)
    limit = W - margin * 2
    if total > limit:
        scale = limit / total
        covers = [c.resize((max(1, round(c.width * scale)), max(1, round(c.height * scale))), Image.Resampling.LANCZOS) for c in covers]
        total = sum(c.width for c in covers) + gap * (len(covers) - 1)
    x = (W - total) // 2
    plate = canvas()
    for cover in covers:
        paste(plate, cover, (x, y))
        x += cover.width + gap
    return plate


def title_card():
    im = canvas()
    d = ImageDraw.Draw(im)
    tracked(d, 'AWARD-WINNING AUTHOR', font(34), 470, GOLD, 10)
    rule(d, 540, 280)
    tracked(d, 'BREE T. WILSON', font(118), 590, CREAM, 6)
    sub = font(46, italic=True)
    text = 'Murder mystery author'
    d.text(((W - sub.getlength(text)) / 2, 760), text, font=sub, fill=MUTED)
    rule(d, 870, 280)
    return vignette(im)


def hannah_card():
    im = row_of([
        'cover-deadly-college-murders',
        'cover-deadly-vows',
        'cover-paris-noir',
        'cover-thirteenth-riddle',
    ], 780, 340)
    d = ImageDraw.Draw(im)
    tracked(d, 'THE HANNAH WALKER MYSTERY SERIES', font(36), 150, GOLD, 8)
    return vignette(im)


def awards_card():
    photo = Image.open(AWARDS).convert('RGB')
    px = photo.load()
    w, h = photo.size
    rows = []
    for y in range(h):
        bright = 0
        for x in range(0, w, 6):
            r, g, b = px[x, y]
            if r + g + b > 36:
                bright += 1
        if bright > 8:
            rows.append(y)
    photo = photo.crop((0, rows[0], w, rows[-1] + 1))
    scale = max(W / photo.width, H / photo.height)
    photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.Resampling.LANCZOS)
    left = (photo.width - W) // 2
    top = max(0, (photo.height - H) // 2 - 40)
    photo = photo.crop((left, top, left + W, top + H))
    photo = ImageEnhance.Color(photo).enhance(0.92)
    photo = ImageEnhance.Brightness(photo).enhance(0.9)
    shade = Image.new('RGB', (W, H), (0, 0, 0))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rectangle((0, H - 280, W, H), fill=230)
    mask = mask.filter(ImageFilter.GaussianBlur(28))
    im = Image.composite(shade, photo, mask)
    d = ImageDraw.Draw(im)
    tracked(d, 'INTERNATIONAL IMPACT BOOK AWARDS', font(32), 1248, GOLD, 7)
    sub = font(46, italic=True)
    text = 'Four-time Distinguished Author'
    d.text(((W - sub.getlength(text)) / 2, 1310), text, font=sub, fill=CREAM)
    return vignette(im)


def astrid_card():
    im = row_of([
        'cover-who-murdered-erica-ivy',
        'cover-the-woman-in-the-evidence',
        'cover-someone-lied-at-midnight',
    ], 860, 360)
    d = ImageDraw.Draw(im)
    tracked(d, 'A NEW SERIES  ·  IN DEVELOPMENT', font(32), 118, GOLD, 8)
    tracked(d, 'ASTRID FITZGERALD', font(58), 175, CREAM, 5)
    return vignette(im)


def close_card():
    im = canvas()
    d = ImageDraw.Draw(im)
    tracked(d, 'ENTER THE MYSTERY', font(34), 500, GOLD, 10)
    rule(d, 575, 280)
    site = font(78)
    text = 'breetwilson.com'
    d.text(((W - site.getlength(text)) / 2, 630), text, font=site, fill=CREAM)
    sub = font(40, italic=True)
    line = 'Hannah Walker   ·   Astrid Fitzgerald'
    d.text(((W - sub.getlength(line)) / 2, 780), line, font=sub, fill=MUTED)
    rule(d, 890, 280)
    return vignette(im)


def encode(plates, out):
    tmp = Path(tempfile.mkdtemp(prefix='intro-'))
    clips = []
    durations = [4.0, 5.0, 5.0, 5.2, 4.2]
    for i, (plate, seconds) in enumerate(zip(plates, durations)):
        src = tmp / f'plate-{i}.png'
        plate.save(src, optimize=True)
        clip = tmp / f'clip-{i}.mp4'
        frames = round(seconds * 30)
        subprocess.run([
            'ffmpeg', '-y', '-loop', '1', '-i', str(src),
            '-vf', (
                f"zoompan=z='min(1+0.0011*on,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s=1920x1080:fps=30,format=yuv420p"
            ),
            '-frames:v', str(frames), '-r', '30',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-an', str(clip),
        ], check=True)
        clips.append((clip, seconds))
    fade = 0.6
    offset = durations[0] - fade
    parts = []
    last = '[0]'
    for i in range(1, len(clips)):
        nxt = f'[v{i}]' if i < len(clips) - 1 else '[out]'
        parts.append(f'{last}[{i}]xfade=transition=fade:duration={fade}:offset={offset:.2f}{nxt}')
        last = nxt
        offset += durations[i] - fade
    graph = ';'.join(parts)
    subprocess.run([
        'ffmpeg', '-y', *[arg for clip, _ in clips for arg in ('-i', str(clip))],
        '-filter_complex', graph, '-map', '[out]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart', '-an', str(out),
    ], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    plates[0].resize((1920, 1080), Image.Resampling.LANCZOS).save(IMG / 'site-intro-poster.jpg', quality=88, optimize=True)


def main():
    VID.mkdir(parents=True, exist_ok=True)
    plates = [title_card(), hannah_card(), awards_card(), astrid_card(), close_card()]
    preview = ROOT / 'tools' / '_intro_preview'
    preview.mkdir(exist_ok=True)
    for i, plate in enumerate(plates):
        plate.resize((960, 540), Image.Resampling.LANCZOS).save(preview / f'{i}.jpg', quality=85)
    if '--preview' in sys.argv:
        print('previews only')
        return
    encode(plates, VID / 'site-intro.mp4')
    print('wrote', VID / 'site-intro.mp4')


if __name__ == '__main__':
    main()

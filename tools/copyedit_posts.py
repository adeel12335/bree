"""Copy-edits the imported blog posts: titles, stray markdown, lowercase "i",
runs of punctuation and broken paragraphs. Reads src/data/posts.original.json
(the untouched import) and writes src/data/posts.json, so it can be re-run."""
import json, re, shutil
from pathlib import Path

D = Path(__file__).resolve().parent.parent / 'src' / 'data'
if not (D / 'posts.original.json').exists():
    shutil.copy(D / 'posts.json', D / 'posts.original.json')
posts = json.loads((D / 'posts.original.json').read_text(encoding='utf-8'))
# Squarespace placeholder (lorem ipsum) and an older draft that duplicates "How Deadly College Murders came to be"
DROP = {'blog-post-template-hynhw-54kg3', 'Blog%20Post%20Title%20One-yt6cr'}
posts = [p for p in posts if p['slug'] not in DROP]

TITLES = {
    'my-journey-as-a-award-winning-author': 'My Journey as an Award-Winning Author',
    'deadly-college-murders-wins-at-iiba': 'Deadly College Murders Wins at IIBA!',
    'finalist-for-author-of-the-year': 'Finalist for Author of the Year!',
    'how-deadly-college-murders-came-to-be': 'How Deadly College Murders Came to Be',
    'deadly-college-murders-original-ending': 'Deadly College Murders: The Original Ending',
    'proudly-accepting-my-second-iiba-award-for-deadly-vows-echoes-of-college-crimes': 'Proudly Accepting My Second IIBA Award for Deadly Vows: Echoes of College Crimes',
    'character-profilejonathan': 'Character Profile: Jonathan',
    'character-profile-det-smithfrom-villain-to-ally': 'Character Profile: Det. Smith… From Villain to Ally',
    'character-profile-bree': 'Character Profile: Bree',
    'who-is-bree-t-wilson': 'Who Is Bree T. Wilson?',
}
# Shorter <title> tags for posts whose headline is too long for search results (the H1 keeps the full headline)
SEO_TITLES = {
    'a-tolling-bell-a-frantic-run-through-the-woods-a-sudden-loss-of-memory-and-a-bloodied-wedding-dress-these-haunting-dreams-carry-deep-significance-for-hannah-throughout-the-books': 'Hannah’s Haunting Dreams and What They Mean',
    'deadly-vows-echoes-of-college-crimes-wins-at-international-impact-book-awards': 'Deadly Vows Wins at the International Impact Book Awards',
    'from-paris-to-venice-florence-and-rome-the-european-adventures-of-hannah-and-raf': 'The European Adventures of Hannah and Raf',
    'hannah-and-jonathans-love-story-is-full-of-passion-and-challenges-but-will-they-make-it-through-and-finally-say-i-do': 'Hannah and Jonathan’s Love Story: Will They Say “I Do”?',
    'hannahs-showdown-with-the-culprit-showcases-a-unique-approach-setting-her-apart-from-hallmarks-typical-leading-mystery-ladies-in-the-way-she-unravels-the-truth': 'Hannah’s Showdown: Unlike Any Hallmark Mystery Heroine',
    'mason-an-antagonist-driven-by-an-intense-desire-for-revenge-against-hannah': 'Mason: An Antagonist Driven by Revenge',
    'paris-noir-where-nothing-is-as-it-appears-and-the-lines-of-obsession-blur-past-the-point-of-delusion': 'Paris Noir: Where Nothing Is as It Appears',
    'proudly-accepting-my-second-iiba-award-for-deadly-vows-echoes-of-college-crimes': 'Accepting My Second IIBA Award for Deadly Vows',
    'tatianas-role-in-shadows-of-the-past-a-deadly-riddle-takes-her-from-being-attacked-to-becoming-the-hero': 'Tatiana’s Role in Shadows of the Past',
    'the-hero-and-the-arch-nemesis-the-one-who-turns-the-heros-life-upside-down': 'The Hero and the Arch-Nemesis',
    'the-thirteenth-riddle-a-poisoned-silence-a-hannah-walker-mystery-series': 'The Thirteenth Riddle: A Poisoned Silence Preview',
    'the-thirteenth-riddle-a-poisoned-silence-has-won-at-iiba-making-me-a-four-time-award-winning-author': 'The Thirteenth Riddle Wins at IIBA: Four-Time Winner',
    'deadly-vows-echoes-of-college-crimes': 'Introducing Deadly Vows: Echoes of College Crimes',
}
LOWER_I = re.compile(r'(?<![\w’\'-])i(?=(?:[’\']\w+)?\b(?![.\-]))')


# Typos found by a spell-check pass over the built pages
TYPOS = {
    'Unfortunetly': 'Unfortunately', 'invisble': 'invisible', 'everythingn': 'everything',
    'Rafaek': 'Rafael', 'Icried': 'I cried', 'After the evens of': 'After the events of',
    'Nim Stant’ ': 'Nim Stant’s ', 'career.””': 'career.”', 'an archnemesis': 'an arch-nemesis',
}


def fix_text(t):
    for a, b in TYPOS.items():
        t = t.replace(a, b)
    t = re.sub(r'\*([^*<>]+?)\*', r'<em>\1</em>', t)       # *markdown italics*
    t = LOWER_I.sub('I', t)                                  # i -> I, i'm -> I'm
    t = re.sub(r'(?:…|\.){2,}(?:…|\.)*', lambda m: '…' if len(m.group(0)) > 1 else m.group(0), t)
    t = re.sub(r'…(?=[A-Za-z])', '… ', t)
    t = re.sub(r'!{2,}', '!', t)
    t = re.sub(r'\?{2,}', '?', t)
    t = t.replace('—-', '—').replace('--', '—')
    t = re.sub(r' {2,}', ' ', t)
    t = re.sub(r' ([,.!?;:])(?=\s|$)', r'\1', t)
    return t


def fix_html(h):
    # touch text only, never tags/attributes
    return ''.join(part if part.startswith('<') else fix_text(part) for part in re.split(r'(<[^>]+>)', h))


def merge_broken_paragraphs(h):
    """Joins <p> fragments that were split mid-sentence by hard line breaks."""
    out = re.sub(r'([a-z,;—-])</p>\s*<p>(?=[a-z—])', r'\1 ', h)
    # short unpunctuated lines are section labels
    return re.sub(r'<p>([A-Z][^<.!?]{2,40})</p>', r'<h3>\1</h3>', out)


for p in posts:
    p['title'] = fix_text(TITLES.get(p['slug'], p['title'])).replace('<em>', '').replace('</em>', '')
    p['seo_title'] = SEO_TITLES.get(p['slug'], p['title'])
    if p['slug'] == 'who-is-bree-t-wilson':
        p['html'] = merge_broken_paragraphs(p['html'].replace('thedevastating', 'the devastating')
                                            .replace('<p>About Bree T. Wilson</p>', '<h3>About Bree T. Wilson</h3>')
                                            .replace('introduces Hannah</p>\n<p>Walker', 'introduces Hannah Walker'))
    p['html'] = fix_html(p['html'])
    text = re.sub(r'<[^>]+>', ' ', p['html'])
    text = re.sub(r'\s+', ' ', text).strip()
    p['excerpt'] = text if len(text) <= 200 else text[:200].rsplit(' ', 1)[0].rstrip(',;:—') + '…'

(D / 'posts.json').write_text(json.dumps(posts, indent=1, ensure_ascii=False), encoding='utf-8')
print(len(posts), 'posts copy-edited')

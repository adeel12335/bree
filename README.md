# Bree T. Wilson — website redesign

This is a static HTML redesign of https://www.breetwilson.com, with a noir library theme in dark, gold and parchment.

## Open or upload

- **Open locally:** double-click `public/index.html`. Every page is a plain `.html` file with relative links, so no server is needed.
- **Upload:** copy everything inside `public/` (or `bree-t-wilson-website.zip`) to the host's web root.
  - `.htaccess` (Apache/cPanel) and `_redirects` (Netlify) give clean URLs such as `/about` and `/blog/<slug>`, which match the old Squarespace links.
  - For fully clean internal links on the live host, build with `python tools/build.py --deploy`.

## Edit

- Content lives in `src/data/`: `books.json`, `pages.json` (about, awards, welcome, legal) and `posts.json` (62 blog posts).
- `posts.original.json` is the untouched import. `tools/copyedit_posts.py` regenerates `posts.json` from it, applying grammar fixes and shorter SEO titles.
- After an edit, run:

```
python tools/build.py        # rebuild public/
python tools/seo_audit.py    # checks titles, descriptions, H1s, alt text, links, JSON-LD
```

## SEO in place

Every page has:

- a unique title and meta description
- a canonical URL (old URL scheme)
- Open Graph and Twitter cards, with a share image per book
- JSON-LD: Person, WebSite, BookSeries, Book (with ISBN and dates), BlogPosting and BreadcrumbList

The site also has:

- one H1 per page
- alt text and dimensions on every image
- a preloaded hero image
- `sitemap.xml` with lastmod, plus `robots.txt`
- automatic links from blog posts to the book pages, and related posts on each post

## Forms

The contact and newsletter forms post to FormSubmit at breetwilson25@gmail.com. The first submission sends a one-time activation email to that inbox, and it must be confirmed before messages arrive.

## Tools

- `tools/import_source.py` and `tools/prepare_assets.py` did the one-time import from `source/` (the scraped site), including the flat covers, signature and share images.
- `tools/figma_export.py` makes self-contained pages for the Figma import.

Figma file: https://www.figma.com/design/emCPH7pi7Gpe38dB6RUo97

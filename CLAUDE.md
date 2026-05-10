# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a static website for **Rizzo Labs** (NYU Langone / Rusk Rehabilitation), a research lab focused on assistive technology and rehabilitation engineering. It is built on the **Constra Bootstrap theme** (Bootstrap 4 + jQuery) with no build system — all HTML is served directly.

## No build system

There is no bundler, transpiler, or package manager. To preview the site, open any `.html` file in a browser or run a local server:

```bash
python3 -m http.server 8000
```

## Generating publications.html

`publications.html` is **auto-generated** by `pubListGen.py`. Do not hand-edit it — changes will be overwritten on the next run.

To regenerate:
```bash
pip install requests beautifulsoup4
python3 pubListGen.py
```

The script scrapes the NYU library publications API (`library.med.nyu.edu/api/publications/?person=rizzoj01`) and enriches missing DOIs/years via the Crossref API. Results are cached in `crossref_enrich_cache.json`. The structured publication data is also maintained in `publications.json`.

## Site architecture

- **Pages:** `index.html`, `projects.html`, `funding.html`, `publications.html` (generated), `team.html`, `join.html`, `photos.html`, `contact.html`, `media.html`, `recognition.html`
- **Custom styles:** `css/style.css` (source map at `css/style.css.map`)
- **Custom JS:** `js/script.js` — handles fixed header scroll behavior, back-to-top button, slick carousel init, and colorbox gallery; `accessibility.js` — runtime accessibility enhancements (wraps videos with `role=region`, keyboard focus improvements)
- **Plugins (vendored):** `plugins/` — Bootstrap 4, FontAwesome, Slick carousel, Colorbox, Shuffle.js, jQuery
- **Media:** project demo videos live directly in `images/` (e.g. `images/curb.mp4`); media highlights videos live in `video/` with poster images in `video/video_cover/`
- **Team/project images:** `images/img/` and `images/projects/`

## Accessibility enrichment

`a11y_generate.py` uses the Claude API (vision) + ffmpeg to automatically generate:
- `alt` text for images lacking descriptive alternatives
- `aria-label` and `<p class="a11y-audio-desc">` descriptions for videos

To run (requires `ANTHROPIC_API_KEY` env var and `ffmpeg` installed):
```bash
ANTHROPIC_API_KEY=sk-... python3 a11y_generate.py
```

It modifies HTML files in-place. The nav header list in the script (`HTML_FILES`) must be kept in sync with actual pages — `media.html` and `recognition.html` are **not** currently in that list.

## Key patterns

**Nav header is duplicated across every page.** There is no template engine — if you update the nav (add/remove a link, rename a page), you must update it in all 10 HTML files.

**Project filter on index.html** uses [Shuffle.js](https://vestride.github.io/Shuffle/). Each project card is a `.shuffle-item` with a `data-groups` attribute matching a radio button's `value`. Adding a new project requires a new radio label + a new `.shuffle-item` div.

**The active nav item** is set per-page by adding `class="nav-item active"` to the appropriate `<li>` in that page's header.

**Page banner sections** (non-index pages) use `<div id="banner-area" class="banner-area" ...>` with an inline background-image.

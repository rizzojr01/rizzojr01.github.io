import re
import time
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# ----------------------------
# Config
# ----------------------------

CONTACT_EMAIL = "jf4151@nyu.edu"
UA = f"RizzoLab-Publications/1.2 (mailto:{CONTACT_EMAIL})"

_YEAR_CACHE = {}
_CROSSREF_META_CACHE = {}


def normalize_doi(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    s = re.sub(r"^\s*doi\s*:\s*", "", s, flags=re.I)
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s, flags=re.I)
    s = s.strip().strip(".").strip()
    return s.lower()


def year_from_date_parts(msg: dict) -> str | None:
    if not isinstance(msg, dict):
        return None
    for key in ("published-print", "published-online", "issued", "created"):
        v = msg.get(key)
        if isinstance(v, dict) and "date-parts" in v:
            dp = v.get("date-parts")
            if isinstance(dp, list) and dp and isinstance(dp[0], list) and dp[0]:
                y = dp[0][0]
                if isinstance(y, int) and 1500 <= y <= 2100:
                    return str(y)
    return None


def safe_title(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def title_similarity(a: str, b: str) -> float:
    a = re.sub(r"[^a-z0-9\s]", " ", (a or "").lower())
    b = re.sub(r"[^a-z0-9\s]", " ", (b or "").lower())
    ta = [t for t in a.split() if t]
    tb = [t for t in b.split() if t]
    if not ta or not tb:
        return 0.0
    sa = set(ta)
    sb = set(tb)
    inter = len(sa & sb)
    denom = max(len(sa), len(sb))
    return inter / denom if denom else 0.0


def crossref_search_by_title_authors(title: str, authors: str, timeout: int = 15) -> dict | None:
    title_q = safe_title(title)
    if not title_q or title_q.lower() == "no title":
        return None

    key = (title_q.lower(), (authors or "").strip().lower())
    if key in _CROSSREF_META_CACHE:
        return _CROSSREF_META_CACHE[key]

    params = {
        "query.bibliographic": title_q,
        "rows": 5,
    }
    if authors and authors != "No Authors":
        params["query.author"] = authors

    url = "https://api.crossref.org/works"
    try:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": UA})
        if r.status_code != 200:
            _CROSSREF_META_CACHE[key] = None
            return None

        items = (r.json().get("message") or {}).get("items") or []
        if not items:
            _CROSSREF_META_CACHE[key] = None
            return None

        best = None
        best_score = -1.0

        for it in items:
            cr_title = ""
            if isinstance(it.get("title"), list) and it["title"]:
                cr_title = it["title"][0]
            sim = title_similarity(title_q, cr_title)

            cr_score = 0.0
            try:
                cr_score = float(it.get("score") or 0.0)
            except Exception:
                cr_score = 0.0

            combined = sim * 10.0 + (cr_score / 1000.0)
            if combined > best_score:
                best_score = combined
                best = it

        if best is not None:
            cr_title = ""
            if isinstance(best.get("title"), list) and best["title"]:
                cr_title = best["title"][0]
            sim = title_similarity(title_q, cr_title)
            if sim < 0.45:
                best = None

        _CROSSREF_META_CACHE[key] = best
        return best
    except Exception:
        _CROSSREF_META_CACHE[key] = None
        return None


def fill_missing_fields_from_crossref(pub: dict) -> dict:
    needs_any = (pub.get("doi") in ("", None)) or (pub.get("year") == "No Year") or (pub.get("journal") == "No Journal")
    if not needs_any:
        return pub

    cand = crossref_search_by_title_authors(pub.get("title", ""), pub.get("authors", ""))
    if not cand:
        return pub

    if (not pub.get("doi")) and cand.get("DOI"):
        pub["doi"] = normalize_doi(cand.get("DOI"))

    if pub.get("year") == "No Year":
        y = year_from_date_parts(cand)
        if y:
            pub["year"] = y

    if pub.get("journal") == "No Journal":
        ctitle = ""
        if isinstance(cand.get("container-title"), list) and cand["container-title"]:
            ctitle = cand["container-title"][0]
        if ctitle:
            pub["journal"] = ctitle

    return pub


# ----------------------------
# NYU Library source
# ----------------------------

def fetch_nyu_publications(url: str, timeout: int = 20):
    response = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    publications = []

    for item in soup.find_all("div", class_="result_item"):
        pub = {
            "title": "No Title",
            "authors": "No Authors",
            "doi": "",
            "journal": "No Journal",
            "year": "No Year",
            "source": "NYU Library",
        }

        title_tag = item.find("h3")
        if title_tag:
            pub["title"] = title_tag.get_text(strip=True)

        authors_tag = item.find("div", class_="authors")
        if authors_tag:
            pub["authors"] = authors_tag.get_text(" ", strip=True)

        doi_tag = item.find("a", class_="doi_link")
        if doi_tag:
            pub["doi"] = normalize_doi(doi_tag.get_text(strip=True))

        citation_tag = item.find("span", class_="citation")
        if citation_tag:
            citation_text = citation_tag.get_text(" ", strip=True)
            parts = [p.strip() for p in citation_text.split(".") if p.strip()]
            if len(parts) >= 1:
                pub["journal"] = parts[0]

            year_match = re.search(r"\b(19|20)\d{2}\b", citation_text)
            if year_match:
                pub["year"] = year_match.group(0)

        pub = fill_missing_fields_from_crossref(pub)
        time.sleep(0.12)

        publications.append(pub)

    return publications


# ----------------------------
# PubMed source
# ----------------------------

PUBMED_SEARCH_TERM = (
    'Rizzo JR[Author] AND '
    '(NYU OR "New York University" OR rehabilitation OR "assistive technology" '
    'OR "visual impairment" OR neurorehabilitation OR "low vision" OR "Rusk")'
)
PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_PAGE_SIZE = 200  # max allowed by NCBI


def fetch_pubmed_ids(term: str) -> list[str]:
    """Return all PMIDs matching the search term."""
    all_ids = []
    retstart = 0

    while True:
        params = {
            "db": "pubmed",
            "term": term,
            "retmax": PUBMED_PAGE_SIZE,
            "retstart": retstart,
            "retmode": "json",
            "sort": "pub_date",
        }
        try:
            r = requests.get(
                f"{PUBMED_BASE}/esearch.fcgi",
                params=params,
                headers={"User-Agent": UA},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            result = data.get("esearchresult", {})
            ids = result.get("idlist", [])
            all_ids.extend(ids)
            total = int(result.get("count", 0))
            retstart += len(ids)
            if retstart >= total or not ids:
                break
            time.sleep(0.35)
        except Exception as e:
            print(f"  PubMed esearch error: {e}")
            break

    return all_ids


def fetch_pubmed_summaries(pmids: list[str]) -> list[dict]:
    """Fetch esummary records for a list of PMIDs and return normalized pub dicts."""
    pubs = []
    batch_size = 200

    for i in range(0, len(pmids), batch_size):
        batch = pmids[i : i + batch_size]
        try:
            r = requests.get(
                f"{PUBMED_BASE}/esummary.fcgi",
                params={"db": "pubmed", "id": ",".join(batch), "retmode": "json"},
                headers={"User-Agent": UA},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json().get("result", {})
        except Exception as e:
            print(f"  PubMed esummary error: {e}")
            continue

        for pmid in batch:
            art = data.get(pmid)
            if not art or not isinstance(art, dict):
                continue

            # Authors
            author_list = art.get("authors", [])
            authors = ", ".join(a.get("name", "") for a in author_list if a.get("name"))

            # DOI
            doi = next(
                (
                    obj.get("value", "")
                    for obj in art.get("articleids", [])
                    if obj.get("idtype") == "doi"
                ),
                "",
            )

            # Year (pubdate is like "2024 Mar" or "2024")
            pubdate = art.get("pubdate", "")
            year_match = re.search(r"\b(19|20)\d{2}\b", pubdate)
            year = year_match.group(0) if year_match else "No Year"

            pub = {
                "title": art.get("title", "No Title").rstrip("."),
                "authors": authors or "No Authors",
                "doi": normalize_doi(doi),
                "journal": art.get("fulljournalname", "") or art.get("source", "") or "No Journal",
                "year": year,
                "source": "PubMed",
                "pmid": pmid,
            }
            pubs.append(pub)

        time.sleep(0.35)

    return pubs


# ----------------------------
# HTML helpers
# ----------------------------

def esc(s: str) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def year_int(y: str) -> int:
    try:
        m = re.search(r"\b(19|20)\d{2}\b", y or "")
        return int(m.group(0)) if m else -1
    except Exception:
        return -1


def pub_block(pub: dict) -> str:
    title = esc(pub.get("title") or "No Title")
    authors = esc(pub.get("authors") or "No Authors")
    journal = esc(pub.get("journal") or "No Journal")
    year = esc(pub.get("year") or "No Year")
    doi = (pub.get("doi") or "").strip()
    pmid = pub.get("pmid", "")

    data_search = esc(
        f"{pub.get('title','')} {pub.get('authors','')} {pub.get('journal','')} {pub.get('year','')} {doi}".lower()
    )

    if doi:
        doi_href = f"https://doi.org/{doi}"
        doi_link = f'<a href="{esc(doi_href)}" target="_blank" rel="noopener">{esc(doi)}</a>'
    else:
        doi_link = "No DOI"

    pmid_link = ""
    if pmid:
        pmid_link = f'<div class="meta-item"><i class="fas fa-external-link-alt"></i><span><strong>PubMed:</strong> <a href="https://pubmed.ncbi.nlm.nih.gov/{esc(pmid)}/" target="_blank" rel="noopener">PMID {esc(pmid)}</a></span></div>'

    return f"""
        <div class="publication pub-card" data-search="{data_search}">
          <div class="pub-title">{title}</div>

          <div class="pub-meta">
            <div class="meta-item"><i class="fas fa-user-edit"></i><span><strong>Authors:</strong> {authors}</span></div>
            <div class="meta-item"><i class="fas fa-book"></i><span><strong>Journal:</strong> {journal}</span></div>
            <div class="meta-item"><i class="fas fa-calendar-alt"></i><span><strong>Year:</strong> {year}</span></div>

            <div class="meta-item meta-doi">
              <i class="fas fa-link"></i>
              <span><strong>DOI:</strong> {doi_link}</span>
            </div>
            {pmid_link}
          </div>
        </div>
    """.rstrip()


# ----------------------------
# Main
# ----------------------------

def main():
    # ── Fetch from NYU Library ──────────────────────────────────────────────
    nyu_base_url = (
        "https://library.med.nyu.edu/api/publications/"
        "?person=rizzoj01&sort=display_rank&in-biosketch=yes&offset={}"
    )

    nyu_pubs = []
    offset = 0
    step = 10

    print("=== Fetching from NYU Library ===")
    while True:
        url = nyu_base_url.format(offset)
        print("  Fetching:", url)

        pubs = fetch_nyu_publications(url)
        if not pubs:
            break

        nyu_pubs.extend(pubs)
        offset += step
        time.sleep(0.2)

        if offset > 2000:
            break

    print(f"  NYU Library: {len(nyu_pubs)} publications fetched.")

    # ── Fetch from PubMed ──────────────────────────────────────────────────
    print("\n=== Fetching from PubMed ===")
    print(f"  Search term: {PUBMED_SEARCH_TERM}")
    pmids = fetch_pubmed_ids(PUBMED_SEARCH_TERM)
    print(f"  Found {len(pmids)} PMIDs. Fetching summaries…")
    pubmed_pubs = fetch_pubmed_summaries(pmids)
    print(f"  PubMed: {len(pubmed_pubs)} publications fetched.")

    # ── Merge & deduplicate ─────────────────────────────────────────────────
    print("\n=== Merging sources ===")
    all_pubs = nyu_pubs + pubmed_pubs

    seen_doi: set[str] = set()
    seen_title: set[tuple] = set()
    deduped = []

    for p in all_pubs:
        doi = (p.get("doi") or "").strip().lower()
        title_key = re.sub(r"[^a-z0-9]", "", (p.get("title") or "").lower())
        year_key = (p.get("year") or "").strip()

        if doi and doi in seen_doi:
            continue
        ty_key = (title_key, year_key)
        if ty_key in seen_title and not doi:
            continue

        if doi:
            seen_doi.add(doi)
        seen_title.add(ty_key)
        deduped.append(p)

    print(f"  Total after deduplication: {len(deduped)} (from {len(all_pubs)} raw)")

    # ── Sort & group by year ────────────────────────────────────────────────
    deduped.sort(
        key=lambda p: (year_int(p.get("year")), (p.get("title") or "").lower()),
        reverse=True,
    )

    grouped: dict[str, list] = {}
    for p in deduped:
        y = p.get("year") or "No Year"
        grouped.setdefault(y, []).append(p)

    years_sorted = sorted(grouped.keys(), key=lambda y: year_int(y), reverse=True)

    # ── Build HTML ──────────────────────────────────────────────────────────
    html_head = """<!DOCTYPE html>
<html lang="en">
<head>

  <!-- Basic Page Needs -->
  <meta charset="utf-8">
  <title>Rizzo Labs | Publications</title>

  <!-- Mobile Specific Metas -->
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="description" content="Publications from the Rizzo Lab at NYU Langone">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <meta name="author" content="Rizzo Labs">
  <meta name="theme-name" content="constra" />

  <!-- Favicon -->
  <link rel="icon" type="image/png" href="images/favicon.png">

  <!-- CSS -->
  <link rel="stylesheet" href="plugins/bootstrap/bootstrap.min.css">
  <link rel="stylesheet" href="plugins/fontawesome/css/all.min.css">
  <link rel="stylesheet" href="plugins/animate-css/animate.css">
  <link rel="stylesheet" href="plugins/slick/slick.css">
  <link rel="stylesheet" href="plugins/slick/slick-theme.css">
  <link rel="stylesheet" href="plugins/colorbox/colorbox.css">
  <link rel="stylesheet" href="css/style.css">

  <!-- Google Fonts: Montserrat -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@200;300;500&display=swap" rel="stylesheet">

  <style>
    .pub-controls {
      background: #fff;
      border: 1px solid rgba(0,0,0,0.08);
      border-radius: 10px;
      padding: 14px 16px;
      margin-bottom: 22px;
    }
    .pub-controls .form-control {
      border-radius: 8px;
      height: 44px;
    }
    .pub-controls .pub-stats {
      color: #666;
      font-size: 0.95rem;
      margin-top: 8px;
    }

    .pub-year-group {
      border: 1px solid rgba(0,0,0,0.08);
      border-radius: 10px;
      overflow: hidden;
      background: #fff;
      margin-bottom: 18px;
    }
    .pub-year-toggle {
      width: 100%;
      border: 0;
      background: #f8f8f8;
      padding: 14px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 700;
      cursor: pointer;
    }
    .pub-year-toggle:focus { outline: none; }
    .pub-year-label { font-size: 1.05rem; }
    .pub-count { font-weight: 600; color: #666; margin-left: 10px; }
    .pub-chevron {
      transition: transform 0.15s ease-in-out;
      color: #111;
    }
    .pub-year-toggle[aria-expanded="true"] .pub-chevron {
      transform: rotate(180deg);
    }

    .pub-year-body { padding: 16px; }

    .publication {
      padding: 16px 18px;
      margin-bottom: 14px;
      background: #ffffff;
      border: 1px solid rgba(0,0,0,0.06);
      border-radius: 10px;
    }
    .pub-title {
      font-size: 1.05rem;
      font-weight: 700;
      margin-bottom: 6px;
    }
    .pub-meta { display: flex; flex-direction: column; gap: 4px; }
    .meta-item {
      display: flex;
      align-items: baseline;
      gap: 6px;
      font-size: 0.93rem;
    }
    .meta-item i { width: 14px; color: #888; flex-shrink: 0; }
    .pub-doi a { word-break: break-word; }

    .pub-year-group.is-empty { display: none; }
  </style>
</head>

<body>

<!-- Header -->
<header id="header" class="header-one">
  <div class="site-navigation">
    <div class="container">
      <div class="row">
        <div class="col-lg-12">
          <nav class="navbar navbar-expand-lg navbar-dark p-0">

            <button class="navbar-toggler" type="button"
              data-toggle="collapse"
              data-target="#navbar-collapse"
              aria-controls="navbar-collapse"
              aria-expanded="false"
              aria-label="Toggle navigation">
              <span class="navbar-toggler-icon"></span>
            </button>

            <div id="navbar-collapse" class="collapse navbar-collapse">
              <ul class="nav navbar-nav mr-auto">

                <!-- Home -->
                <li class="nav-item">
                  <a class="nav-link" href="index.html">Home</a>
                </li>

                <!-- Projects -->
                <li class="nav-item dropdown">
                  <a class="nav-link" href="projects.html">Projects</a>
                </li>

                <!-- Funding -->
                <li class="nav-item">
                  <a class="nav-link" href="funding.html">Funding</a>
                </li>

                <!-- Publications -->
                <li class="nav-item active">
                  <a class="nav-link" href="publications.html">Publications</a>
                </li>

                <!-- Recognition -->
                <li class="nav-item">
                  <a class="nav-link" href="recognition.html">Recognition</a>
                </li>

                <!-- Media -->
                <li class="nav-item">
                  <a class="nav-link" href="media.html">Media</a>
                </li>

                <!-- Team -->
                <li class="nav-item">
                  <a class="nav-link" href="team.html">Team</a>
                </li>

                <!-- Photos -->
                <li class="nav-item">
                  <a class="nav-link" href="photos.html">Photos</a>
                </li>

                <!-- Join -->
                <li class="nav-item">
                  <a class="nav-link" href="join.html">Join</a>
                </li>

                <!-- Contact -->
                <li class="nav-item">
                  <a class="nav-link" href="contact.html">Contact</a>
                </li>

              </ul>
              <!-- Logo on right -->
              <a class="navbar-brand ml-3" href="index.html">
                <img src="images/web_logo.png" alt="Rizzo Labs" style="height:42px; filter:brightness(0) invert(1);">
              </a>
            </div>
          </nav>
        </div>
      </div>

      <div class="search-block" style="display: none;">
        <label for="search-field" class="w-100 mb-0">
          <input type="text" class="form-control" id="search-field"
            placeholder="Search publications, projects, people">
        </label>
        <span class="search-close">&times;</span>
      </div>

    </div>
  </div>
</header>
<!-- End Header -->

<div id="banner-area" class="banner-area" style="background-image:url(images/banner/banner1.jpg)">
  <div class="banner-text">
    <div class="container">
      <div class="banner-heading">
        <h1 class="banner-title">Publications</h1>
      </div>
    </div>
  </div>
</div>

<section id="main-container" class="main-container pb-4">
  <div class="container">

    <div class="row">
      <div class="col-lg-12">
        <div class="pub-controls">
          <input id="pubSearch" type="text" class="form-control" placeholder="Search by title, author, journal, year, or DOI">
          <div class="pub-stats">
            Showing <span id="pubShown">0</span> of <span id="pubTotal">0</span> publications
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-lg-12">
        <div id="pubGroups">
"""

    html_tail = """
        </div>
      </div>
    </div>

  </div>
</section>

<!-- Footer -->
<footer id="footer" class="footer">
  <div class="footer-main">
    <div class="container">

      <div class="row">

        <!-- Column 1: Contact -->
        <div class="col-lg-4 col-md-6 footer-widget">
          <h3 class="widget-title">Contact</h3>

          <ul class="list-unstyled mb-4">
            <li class="mb-2">
              <i class="fa fa-map-marker-alt mr-2" aria-hidden="true"></i>
              <span>
                <strong>Location</strong><br>
                NYU Langone Ambulatory Care Center<br>
                Rusk Rehabilitation<br>
                240 E 38th St, 17th Floor,<br>
                New York, NY 10016
              </span>
            </li>

            <li class="mb-2">
              <i class="fa fa-envelope mr-2" aria-hidden="true"></i>
              <a href="mailto:JohnRoss.Rizzo@nyulangone.org">JohnRoss.Rizzo@nyulangone.org</a>
            </li>

            <li class="mb-2">
              <i class="fa fa-envelope mr-2" aria-hidden="true"></i>
              <a href="mailto:mahya.beheshti@nyulangone.org">mahya.beheshti@nyulangone.org</a>
            </li>
          </ul>

          <div class="footer-social">
            <h3 class="widget-title">Connect</h3>
            <ul class="list-unstyled mb-0">
              <li class="d-inline-block">
                <a aria-label="LinkedIn"
                   href="https://www.linkedin.com/in/jr-rizzo-3b447125/"
                   target="_blank" rel="noopener">
                  <i class="fab fa-linkedin-in"></i>
                </a>
              </li>
              <li class="d-inline-block">
                <a aria-label="X"
                   href="https://x.com/jrrizzo00"
                   target="_blank" rel="noopener">
                  <i class="fab fa-twitter"></i>
                </a>
              </li>
              <li class="d-inline-block">
                <a aria-label="GitHub"
                   href="https://github.com/rizzojr01"
                   target="_blank" rel="noopener">
                  <i class="fab fa-github"></i>
                </a>
              </li>
            </ul>
          </div>
        </div>

        <!-- Column 2: Map -->
        <div class="col-lg-4 col-md-6 footer-widget">
          <h3 class="widget-title">Map</h3>

          <div class="footer-map-wrapper">
            <iframe
              title="Rizzo Labs map"
              class="footer-map"
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
              src="https://www.google.com/maps?q=240%20E%2038th%20St%2017th%20Floor%20New%20York%20NY%2010016&output=embed">
            </iframe>
          </div>

          <p class="mt-3 mb-0">
            <a class="read-more"
               href="https://www.google.com/maps?q=240%20E%2038th%20St%2017th%20Floor%20New%20York%20NY%2010016"
               target="_blank" rel="noopener">
              Open in Google Maps
            </a>
          </p>
        </div>

        <!-- Column 3: Subscription -->
        <div class="col-lg-4 col-md-12 footer-widget">
          <h3 class="widget-title">Stay Updated</h3>

          <p class="mb-3">Subscribe to receive:</p>
          <ul class="list-unstyled mb-3" style="font-size:0.9rem; color:#ccc;">
            <li class="mb-1"><i class="fa fa-check-circle mr-2" aria-hidden="true"></i>Publication alerts for new manuscripts from our lab</li>
            <li class="mb-1"><i class="fa fa-check-circle mr-2" aria-hidden="true"></i>News on lab milestones, talks, and events</li>
            <li class="mb-1"><i class="fa fa-check-circle mr-2" aria-hidden="true"></i>Invitations to participate in studies we are actively recruiting for</li>
          </ul>

          <form class="footer-newsletter" id="mc-form" novalidate>
            <div class="form-group mb-2">
              <label class="sr-only" for="mc-email">Email</label>
              <input
                id="mc-email"
                type="email"
                class="form-control"
                placeholder="Enter your email"
                required
              >
            </div>

            <button type="submit" class="btn btn-primary w-100">
              Subscribe
            </button>

            <small id="mc-message" class="d-block mt-2 footer-note"></small>
          </form>

          <small class="d-block mt-2 footer-note">No spam. Unsubscribe anytime.</small>
        </div>

      </div><!--/ Row end -->

    </div><!--/ Container end -->
  </div><!--/ Footer main end -->

  <div class="copyright">
    <div class="container">
      <div class="row align-items-center">
        <div class="col-md-12 text-center">
          <div class="copyright-info">
            <span>Copyright &copy; <span id="footer-year">2024</span> Rizzo Labs</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</footer>
<!-- End Footer -->

<script>
  document.getElementById("footer-year").textContent = new Date().getFullYear();
</script>

<!-- Scripts -->
<script src="plugins/jQuery/jquery.min.js"></script>
<script src="plugins/bootstrap/bootstrap.min.js" defer></script>
<script src="plugins/slick/slick.min.js"></script>
<script src="plugins/slick/slick-animation.min.js"></script>
<script src="plugins/colorbox/jquery.colorbox.js"></script>
<script src="plugins/shuffle/shuffle.min.js" defer></script>
<script src="js/script.js"></script>

<script src="accessibility.js"></script>

<script>
  (function () {
    var input = document.getElementById("pubSearch");
    var groups = Array.prototype.slice.call(document.querySelectorAll(".pub-year-group"));
    var total = document.querySelectorAll(".publication").length;

    var shownEl = document.getElementById("pubShown");
    var totalEl = document.getElementById("pubTotal");
    totalEl.textContent = String(total);

    function updateCounts() {
      var shown = document.querySelectorAll(".publication:not([hidden])").length;
      shownEl.textContent = String(shown);
    }

    function filter() {
      var q = (input.value || "").trim().toLowerCase();

      groups.forEach(function (g) {
        var pubs = Array.prototype.slice.call(g.querySelectorAll(".publication"));
        var anyVisible = false;

        pubs.forEach(function (p) {
          var hay = (p.getAttribute("data-search") || "");
          var match = !q || hay.indexOf(q) !== -1;

          if (match) {
            p.hidden = false;
            anyVisible = true;
          } else {
            p.hidden = true;
          }
        });

        if (anyVisible) {
          g.classList.remove("is-empty");
        } else {
          g.classList.add("is-empty");
        }
      });

      updateCounts();
    }

    input.addEventListener("input", filter);
    updateCounts();
  })();
</script>

</body>
</html>
"""

    body = []
    for y in years_sorted:
        pubs = grouped[y]
        safe_id = re.sub(r"[^0-9a-zA-Z]+", "-", y).strip("-") or "no-year"
        group_id = f"pubs-{safe_id}"
        count = len(pubs)

        expanded = "true" if y == years_sorted[0] else "false"
        show_class = "show" if y == years_sorted[0] else ""

        body.append(f"""
          <div class="pub-year-group">
            <button class="pub-year-toggle" type="button"
              data-toggle="collapse" data-target="#{group_id}"
              aria-expanded="{expanded}" aria-controls="{group_id}">
              <div>
                <span class="pub-year-label">{esc(y)}</span>
                <span class="pub-count">({count})</span>
              </div>
              <span class="pub-chevron"><i class="fas fa-chevron-down"></i></span>
            </button>

            <div id="{group_id}" class="collapse {show_class}">
              <div class="pub-year-body">
        """.rstrip())

        for p in pubs:
            body.append(pub_block(p))

        body.append("""
              </div>
            </div>
          </div>
        """.rstrip())

    full_html = html_head + "\n".join(body) + html_tail

    out_path = "publications.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"\nWrote {out_path} with {len(deduped)} publications.")
    print(f"  Sources: NYU Library ({len(nyu_pubs)}) + PubMed ({len(pubmed_pubs)})")


if __name__ == "__main__":
    main()

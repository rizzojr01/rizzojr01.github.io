import re
import time
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# ----------------------------
# Config
# ----------------------------
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

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
    """
    Lightweight similarity score: token overlap ratio.
    """
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
    """
    Search Crossref by bibliographic metadata and return the best candidate item dict, or None.
    """
    title_q = safe_title(title)
    if not title_q or title_q.lower() == "no title":
        return None

    key = (title_q.lower(), (authors or "").strip().lower())
    if key in _CROSSREF_META_CACHE:
        return _CROSSREF_META_CACHE[key]

    # Query Crossref. Use bibliographic for title like strings.
    # Add a second signal if authors exist.
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

        # Choose best by combined score: title similarity first, then Crossref score if present.
        best = None
        best_score = -1.0

        for it in items:
            cr_title = ""
            if isinstance(it.get("title"), list) and it["title"]:
                cr_title = it["title"][0]
            sim = title_similarity(title_q, cr_title)

            # Crossref sometimes has "score" on items in some contexts
            cr_score = 0.0
            try:
                cr_score = float(it.get("score") or 0.0)
            except Exception:
                cr_score = 0.0

            combined = sim * 10.0 + (cr_score / 1000.0)
            if combined > best_score:
                best_score = combined
                best = it

        # Require minimum similarity to avoid bad matches
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
    """
    If DOI, year, journal are missing, try Crossref metadata search by title and authors.
    """
    needs_any = (pub.get("doi") in ("", None)) or (pub.get("year") == "No Year") or (pub.get("journal") == "No Journal")
    if not needs_any:
        return pub

    cand = crossref_search_by_title_authors(pub.get("title", ""), pub.get("authors", ""))
    if not cand:
        return pub

    # DOI
    if (not pub.get("doi")) and cand.get("DOI"):
        pub["doi"] = normalize_doi(cand.get("DOI"))

    # Year
    if pub.get("year") == "No Year":
        y = year_from_date_parts(cand)
        if y:
            pub["year"] = y

    # Journal / container title
    if pub.get("journal") == "No Journal":
        ctitle = ""
        if isinstance(cand.get("container-title"), list) and cand["container-title"]:
            ctitle = cand["container-title"][0]
        if ctitle:
            pub["journal"] = ctitle
        else:
            # Fallback: for chapters, sometimes "publisher" is present but not a journal
            # Keep No Journal if nothing reasonable is found.
            pass

    return pub


def fetch_publications(url: str, timeout: int = 20):
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

        # New: if DOI is missing or year/journal missing, search Crossref by title+authors
        pub = fill_missing_fields_from_crossref(pub)
        time.sleep(0.12)

        publications.append(pub)

    return publications



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

    data_search = esc(
        f"{pub.get('title','')} {pub.get('authors','')} {pub.get('journal','')} {pub.get('year','')} {doi}".lower()
    )

    if doi:
        doi_href = f"https://doi.org/{doi}"
        doi_link = f'<a href="{esc(doi_href)}" target="_blank" rel="noopener">{esc(doi)}</a>'

    else:
        doi_link = "No DOI"
        doi_copy_btn = ""

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
          </div>
        </div>
    """.rstrip()



# ----------------------------
# Main: fetch all pages + write publications.html
# ----------------------------
def main():
    base_url = (
        "https://library.med.nyu.edu/api/publications/"
        "?person=rizzoj01&sort=display_rank&in-biosketch=yes&offset={}"
    )

    all_pubs = []
    offset = 0
    step = 10

    while True:
        url = base_url.format(offset)
        print("Fetching:", url)

        pubs = fetch_publications(url)
        if not pubs:
            break

        all_pubs.extend(pubs)
        offset += step
        time.sleep(0.2)

        if offset > 2000:
            break

    # Deduplicate
    seen = set()
    deduped = []
    for p in all_pubs:
        doi = (p.get("doi") or "").strip().lower()
        key = ("doi", doi) if doi else ("ty", (p.get("title") or "").strip().lower(), (p.get("year") or "").strip())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    # Sort by year desc, then title
    deduped.sort(key=lambda p: (year_int(p.get("year")), (p.get("title") or "").lower()), reverse=True)

    # Group by year
    grouped = {}
    for p in deduped:
        y = p.get("year") or "No Year"
        grouped.setdefault(y, []).append(p)

    years_sorted = sorted(grouped.keys(), key=lambda y: year_int(y), reverse=True)

    html_head = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Publications | Rizzo Lab</title>

  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="description" content="Publications from the Rizzo Lab">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">

  <link rel="icon" type="image/png" href="images/favicon.png">

  <!-- CSS (Constra) -->
  <link rel="stylesheet" href="plugins/bootstrap/bootstrap.min.css">
  <link rel="stylesheet" href="plugins/fontawesome/css/all.min.css">
  <link rel="stylesheet" href="plugins/animate-css/animate.css">
  <link rel="stylesheet" href="plugins/slick/slick.css">
  <link rel="stylesheet" href="plugins/slick/slick-theme.css">
  <link rel="stylesheet" href="plugins/colorbox/colorbox.css">
  <link rel="stylesheet" href="css/style.css">

  <style>
    .pub-controls{
      background:#fff;
      border:1px solid rgba(0,0,0,0.08);
      border-radius:10px;
      padding:14px 16px;
      margin-bottom:22px;
    }
    .pub-controls .form-control{
      border-radius:8px;
      height:44px;
    }
    .pub-controls .pub-stats{
      color:#666;
      font-size:0.95rem;
      margin-top:8px;
    }

    .pub-year-group{
      border:1px solid rgba(0,0,0,0.08);
      border-radius:10px;
      overflow:hidden;
      background:#fff;
      margin-bottom:18px;
    }
    .pub-year-toggle{
      width:100%;
      border:0;
      background:#f8f8f8;
      padding:14px 16px;
      display:flex;
      align-items:center;
      justify-content:space-between;
      font-weight:700;
      cursor:pointer;
    }
    .pub-year-toggle:focus{
      outline:none;
    }
    .pub-year-label{
      font-size:1.05rem;
    }
    .pub-count{
      font-weight:600;
      color:#666;
      margin-left:10px;
    }
    .pub-chevron{
      transition:transform 0.15s ease-in-out;
      color:#111;
    }
    .pub-year-toggle[aria-expanded="true"] .pub-chevron{
      transform:rotate(180deg);
    }

    .pub-year-body{
      padding:16px;
    }

    .publication{
      padding:16px 18px;
      margin-bottom:14px;
      background:#ffffff;
      border:1px solid rgba(0,0,0,0.06);
      border-radius:10px;
    }
    .pub-title{
      font-size:1.05rem;
      font-weight:700;
      margin-bottom:6px;
    }
    .pub-authors,.pub-journal,.pub-year,.pub-doi{
      font-size:0.95rem;
      margin-bottom:4px;
    }
    .pub-doi a{
      word-break:break-word;
    }

    .pub-year-group.is-empty{
      display:none;
    }
  </style>
</head>

<body>

<header id="header" class="header-one">
  <div class="site-navigation">
    <div class="container">
      <div class="row">
        <div class="col-lg-12">
          <nav class="navbar navbar-expand-lg navbar-dark p-0">

            <!-- Logo -->
            <a class="navbar-brand d-flex align-items-center" href="index.html">
              <img src="images/web_logo.png"
                   alt="Rizzo Labs logo"
                   class="nav-logo">
            </a>

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
                  <a class="nav-link" href="projects.html">
                    Projects
                  </a>
                </li>

                <!-- Funding & Awards -->
                <li class="nav-item">
                  <a class="nav-link" href="funding.html">Funding &amp; Awards</a>
                </li>

                <!-- Publications -->
                <li class="nav-item active">
                  <a class="nav-link" href="publications.html">Publications</a>
                </li>

                <!-- Team -->
                <li class="nav-item">
                  <a class="nav-link" href="team.html">Team</a>
                </li>

                <!-- Join -->
                <li class="nav-item">
                  <a class="nav-link" href="join.html">Join</a>
                </li>

                <!-- Photos -->
                <li class="nav-item">
                  <a class="nav-link" href="photos.html">Photos</a>
                </li>

                <!-- Contact -->
                <li class="nav-item">
                  <a class="nav-link" href="contact.html">Contact</a>
                </li>

              </ul>
            </div>

          </nav>
        </div>
      </div>
    </div>
  </div>
</header>

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

    <div class="row text-center">
      <div class="col-lg-12">
        <h3 class="section-sub-title">Publications</h3>
      </div>
    </div>

    <div class="row">
      <div class="col-lg-12">
        <div class="pub-controls">
          <input id="pubSearch" type="text" class="form-control" placeholder="Search by title, author, journal, year, or DOI">
          <div class="pub-stats">
            Showing <span id="pubShown">0</span> of <span id="pubTotal">0</span>
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

<footer id="footer" class="footer">
  <div class="footer-main">
    <div class="container">
      <div class="row">

        <div class="col-lg-4 footer-widget">
          <h3 class="widget-title">Contact</h3>
          <p>
            NYU Langone Ambulatory Care Center<br>
            Rusk Rehabilitation<br>
            240 E 38th St, 17th Floor<br>
            New York, NY 10016
          </p>
          <p><a href="mailto:jr.rizzo@nyulangone.org">jr.rizzo@nyulangone.org</a></p>
        </div>

        <div class="col-lg-4 footer-widget">
          <h3 class="widget-title">Map</h3>
          <iframe
            loading="lazy"
            style="border:0;width:100%;height:200px;"
            src="https://www.google.com/maps?q=240%20E%2038th%20St%2017th%20Floor%20New%20York%20NY%2010016&output=embed">
          </iframe>
        </div>

        <div class="col-lg-4 footer-widget">
          <h3 class="widget-title">Follow</h3>
          <p>
            <a href="https://www.linkedin.com/in/jr-rizzo-3b447125/">LinkedIn</a><br>
            <a href="https://github.com/rizzojr01">GitHub</a>
          </p>
        </div>

      </div>
    </div>
  </div>

  <div class="copyright text-center">
    &copy; <span id="year"></span> Rizzo Lab
  </div>
</footer>

<script>
  document.getElementById("year").textContent = new Date().getFullYear();
</script>

<script src="plugins/jQuery/jquery.min.js"></script>
<script src="plugins/bootstrap/bootstrap.min.js"></script>
<script src="js/script.js"></script>

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

    print(f"Wrote {out_path} with {len(deduped)} publications (raw fetched: {len(all_pubs)}).")
    print(f"Year lookup cache size: {len(_YEAR_CACHE)}")


if __name__ == "__main__":
    main()


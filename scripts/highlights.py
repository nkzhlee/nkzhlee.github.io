"""Paper-by-paper research highlights, using figures from the source papers."""
from html import escape


def ordered_highlights(publications, highlights):
    by_id = {record["id"]: record for record in highlights}
    expected = {paper["id"] for paper in publications if paper["type"] not in ("dataset", "poster")}
    if len(by_id) != len(highlights) or set(by_id) != expected:
        raise ValueError("Every paper, including workshops and preprints, needs exactly one highlight")
    # Stable sorting preserves the CV order within each year.
    return [(paper, by_id[paper["id"]]) for paper in sorted(publications, key=lambda p: p.get("year") or 0, reverse=True) if paper["id"] in by_id]


def paper_highlight(paper, highlight, compact=False):
    e = escape
    identifier = e(paper["id"])
    source_url = highlight.get("sourceUrl") or paper["links"][0]["url"]
    paper_url = paper["links"][0]["url"]
    year = paper.get("year") or "Undated"
    venue = paper["venue"] if str(year) in paper["venue"] else f'{year} · {paper["venue"]}'
    citation = f'/publications/#{identifier}'
    authors = e(paper["authors"]).replace("Zhaohui Li", "<strong>Zhaohui Li</strong>")
    search = e(" ".join([paper["title"], paper["authors"], paper["venue"], highlight["summary"], str(year)]), quote=True)
    source_label = e(highlight["figureLabel"])
    authors_line = f'<p class="authors">{authors}</p>'
    if paper.get("authorNote"):
        authors_line += f'<p class="authors">{e(paper["authorNote"])}</p>'
    return f'''<article class="paper-highlight" id="highlight-{identifier}" data-highlight data-year="{year}" data-highlight-search="{search}">
<figure class="paper-figure"><a href="{e(source_url, quote=True)}"><img src="{e(highlight['image'], quote=True)}" alt="{e(highlight['imageAlt'], quote=True)}" width="{int(highlight['imageWidth'])}" height="{int(highlight['imageHeight'])}" loading="lazy" decoding="async"></a><figcaption><a href="{e(source_url, quote=True)}">{source_label} from the paper</a></figcaption></figure>
<div class="paper-copy"><p class="paper-venue">{e(venue)}</p><h3><a href="{e(paper_url, quote=True)}">{e(paper["title"])}</a></h3><p class="paper-summary">{e(highlight["summary"])}</p>{'' if compact else authors_line}<div class="paper-links"><a href="{e(paper_url, quote=True)}">Paper</a><a href="{citation}">Full citation</a></div></div>
</article>'''


def render_highlights(publications, highlights, limit=None):
    ordered = ordered_highlights(publications, highlights)
    if limit is not None:
        return '<div class="paper-highlights">' + ''.join(paper_highlight(p, h, compact=True) for p, h in ordered[:limit]) + '</div>'
    years = sorted({p.get("year") for p, _ in ordered if p.get("year")}, reverse=True)
    controls = f'''<div class="highlight-tools"><div><label for="highlight-search">Find a paper</label><input type="search" id="highlight-search" placeholder="Title, topic, or author" autocomplete="off"></div><div><label for="highlight-year">Year</label><select id="highlight-year"><option value="">All years</option>{''.join(f'<option value="{y}">{y}</option>' for y in years)}</select></div><div><label for="highlight-order">Order</label><select id="highlight-order"><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select></div></div><p id="highlight-count" class="highlight-count" role="status" aria-live="polite">{len(ordered)} paper highlights · newest first</p>'''
    groups = []
    for year in years:
        cards = ''.join(paper_highlight(p, h) for p, h in ordered if p.get("year") == year)
        groups.append(f'<section class="highlight-year" id="papers-{year}" data-highlight-year="{year}"><h2>{year}</h2><div class="paper-highlights">{cards}</div></section>')
    return controls + '<noscript><p>All papers are shown below. Search and ordering require JavaScript.</p></noscript><div data-highlight-groups>' + ''.join(groups) + '</div><p id="highlight-empty" hidden>No papers match. Try another search or choose all years.</p>'

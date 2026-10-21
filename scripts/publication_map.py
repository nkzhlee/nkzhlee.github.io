"""Render the publication landscape without third-party dependencies.

Integration:
    from publication_map import render_publication_map, render_publication_map_svg
    taxonomy = json.loads((ROOT / 'data/publication-map.json').read_text())
    body += render_publication_map(PUBS, taxonomy)
    write('files/publication-map.svg', render_publication_map_svg(PUBS, taxonomy))

Load /css/publication-map.css and /js/publication-map.js on the publications page.
The map reveals its own result list, linking to existing publication article IDs.
It also dispatches publication-map:select with {ids, label, active} for consumers.
The public functions validate a complete, one-to-one taxonomy before rendering.
"""

from collections import Counter
from html import escape
import json
import re
from textwrap import wrap


def _prepare(publications, taxonomy):
    pubs = {p["id"]: p for p in publications}
    groups = {g["id"]: g for g in taxonomy["communities"]}
    venues = {v["id"]: v for v in taxonomy["venues"]}
    topics = {t["id"]: t for t in taxonomy["topics"]}
    records = taxonomy["publications"]
    record_ids = [p["id"] for p in records]
    if len(pubs) != len(publications) or len(set(record_ids)) != len(records):
        raise ValueError("Publication IDs must be unique in publications and map taxonomy")
    if set(record_ids) != set(pubs):
        raise ValueError("Publication map must include every publication exactly once")
    for group in groups.values():
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", group["color"]):
            raise ValueError("Community colors must be six-digit hex colors")
    for venue in venues.values():
        if venue["communityId"] not in groups:
            raise ValueError("Unknown venue community")
    for record in records:
        venue = venues[record["venueId"]]
        if record["communityId"] != venue["communityId"]:
            raise ValueError("Publication community must match its venue community")
        if not record["topicIds"] or len(set(record["topicIds"])) != len(record["topicIds"]):
            raise ValueError("Each publication needs unique topic IDs")
        if not set(record["topicIds"]) <= set(topics):
            raise ValueError("Unknown topic in publication map")
    return pubs, groups, venues, topics, records


def _button(label, *, community=None, venue=None, topic=None, css="", title=None):
    attrs = "".join(f' data-map-{key}="{escape(value, quote=True)}"' for key, value in
                    (("community", community), ("venue", venue), ("topic", topic)) if value)
    aria = f' aria-label="{escape(title, quote=True)}"' if title else ""
    return f'<button type="button" class="{css}" data-map-select{attrs} aria-pressed="false" aria-controls="map-results"{aria}>{label}</button>'


def _swatch(color):
    return f'<span class="map-swatch" style="--community-color:{color}" aria-hidden="true"></span>'


def render_publication_map(publications, taxonomy):
    """Return accessible desktop matrix + mobile venue cards and interaction data."""
    pubs, groups, venues, topics, records = _prepare(publications, taxonomy)
    venue_counts = Counter(r["venueId"] for r in records)
    group_counts = Counter(r["communityId"] for r in records)
    counts = Counter((r["venueId"], topic) for r in records for topic in r["topicIds"])
    topic_groups = {tid: [gid for gid in groups if any(r["communityId"] == gid and tid in r["topicIds"] for r in records)] for tid in topics}
    shared_count = sum(len(gids) > 1 for gids in topic_groups.values())
    community_legend = []
    for gid, group in groups.items():
        count = group_counts[gid]
        unit = "work" if count == 1 else "works"
        label = f'{_swatch(group["color"])}<span>{escape(group["label"])}</span><strong>{count} <span class="map-count-unit">{unit}</span></strong>'
        community_legend.append(_button(label, community=gid, css="map-community", title=f'{group["label"]} venue grouping: {count} {unit}; not a topic total'))

    columns = []
    mobile_topics = []
    for tid, topic in topics.items():
        dots = ''.join(_swatch(groups[gid]["color"]) for gid in topic_groups[tid])
        count_label = f'{len(topic_groups[tid])} ' + ('group' if len(topic_groups[tid]) == 1 else 'groups')
        label = f'<span>{escape(topic["label"])}</span><span class="map-topic-groups" aria-hidden="true">{dots}</span><small>{count_label}</small>'
        columns.append('<th scope="col">' + _button(label, topic=tid, css="map-topic", title=f'{topic["label"]}, represented in {count_label}; show related publications') + '</th>')
        mobile_topics.append(_button(f'{escape(topic["label"])}<span class="map-topic-groups" aria-hidden="true">{dots}</span>', topic=tid, css="map-mobile-topic"))

    rows = []
    cards = []
    previous_group = None
    for vid, venue in venues.items():
        gid = venue["communityId"]
        color = groups[gid]["color"]
        start = " map-group-start" if gid != previous_group else ""
        previous_group = gid
        count = venue_counts[vid]
        venue_label = f'{_swatch(color)}<span>{escape(venue["label"])}</span><strong>{count}</strong>'
        venue_button = _button(venue_label, venue=vid, css="map-venue", title=f'{venue.get("longLabel", venue["label"])}: {count} works')
        cells, chips = [], []
        for tid, topic in topics.items():
            value = counts[(vid, tid)]
            if value:
                title = f'{venue["label"]} × {topic["label"]}: {value} ' + ('work' if value == 1 else 'works')
                cells.append('<td>' + _button(f'<span class="map-count">{value}</span>', venue=vid, topic=tid, css="map-cell", title=title) + '</td>')
                chips.append(_button(f'<span>{escape(topic["label"])}</span><strong>{value}</strong>', venue=vid, topic=tid, css="map-chip", title=title))
            else:
                cells.append('<td class="map-empty"><span aria-hidden="true">—</span><span class="visually-hidden">0 works</span></td>')
        rows.append(f'<tr class="map-row{start}" data-map-row="{escape(vid)}" style="--community-color:{color}"><th scope="row">{venue_button}</th>{"".join(cells)}</tr>')
        cards.append(f'<article class="map-venue-card" data-map-row="{escape(vid)}" style="--community-color:{color}"><div class="map-card-heading">{venue_button}<span>{escape(groups[gid]["label"])}</span></div><div class="map-chips">{"".join(chips)}</div></article>')

    payload = {
        "publications": [{"id": p["id"], "title": p["title"], "year": p.get("year"), "type": p.get("type", "")} for p in publications],
        "communities": taxonomy["communities"], "venues": taxonomy["venues"],
        "topics": taxonomy["topics"], "records": records,
    }
    json_text = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return f'''<section class="wrap publication-map-section" id="publication-map" aria-labelledby="publication-map-heading" data-publication-map>
<div class="map-summary" aria-label="Publication map summary" hidden><span><strong>{len(records)}</strong> works</span><span><strong>{len(venues)}</strong> venues &amp; repositories</span><span><strong>{shared_count}</strong> themes shared across venue groups</span></div>
<div class="visually-hidden" id="map-grouping-note"><h3>Venue groupings, not topic totals</h3><p>Counts below group works by their publication venue or repository, not by every research area they address. For example, ASD-HI appears under AIED (AI for education), although it concerns autism and special education.</p></div>
<div class="map-legend" role="group" aria-label="Filter by venue grouping" aria-describedby="map-grouping-note">{"".join(community_legend)}</div>
<p class="map-instruction" hidden>Read across a venue to see its themes; read down a theme to see connections across communities. Select a colored count to explore the work.</p>
<div class="map-mobile-topics" aria-label="Shared topics">{"".join(mobile_topics)}</div>
<div class="map-table-wrap"><table class="map-table"><caption class="visually-hidden">Publication counts by venue and topic. Colors identify venue groupings, not all research on a topic; each work may have more than one topic.</caption><thead><tr><th scope="col" class="map-venue-header">Venue / repository<span>Unique works</span></th>{"".join(columns)}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<div class="map-mobile-venues">{"".join(cards)}</div>
<p class="map-note" hidden>Numbers count works, not citations. Each work belongs to one venue or repository and may appear under several topics, so topic counts should not be added. Colors are curated venue groupings, not exclusive disciplinary labels; gray identifies datasets and preprints.</p>
<div class="map-results" id="map-results" hidden><div class="map-results-heading"><div><p class="eyebrow">Selected connection</p><h3 data-map-result-title></h3></div><button type="button" data-map-clear>Clear selection</button></div><p class="map-result-status" role="status" aria-live="polite" data-map-status></p><ol data-map-result-list></ol></div>
<noscript><p class="map-note">The figure displays all counts. Interactive selections require JavaScript; full citations are available in the publication list.</p></noscript>
<script type="application/json" data-map-data>{json_text}</script>
</section>'''


def _svg_lines(text, x, y, width=16, line_height=17, **attrs):
    lines = wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [""]
    extra = " ".join(f'{key.replace("_", "-")}="{escape(str(value), quote=True)}"' for key, value in attrs.items())
    spans = ''.join(f'<tspan x="{x}" y="{y + i * line_height}">{escape(line)}</tspan>' for i, line in enumerate(lines))
    return f'<text {extra}>{spans}</text>'


def render_publication_map_svg(publications, taxonomy):
    """Return a standalone, high-resolution vector figure with identical counts."""
    pubs, groups, venues, topics, records = _prepare(publications, taxonomy)
    venue_counts = Counter(r["venueId"] for r in records)
    counts = Counter((r["venueId"], topic) for r in records for topic in r["topicIds"])
    width, label_width, row_height, top = 1370, 300, 54, 380
    col_width = (width - label_width - 45) / len(topics)
    height = top + len(venues) * row_height + 168
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
              '<title id="title">Zhaohui Li — publication landscape</title>',
              '<desc id="description">A venue-by-topic matrix. Colors show venue groupings, not all research on a topic. For example, ASD-HI appears under AIED although it concerns autism and special education. Numbers count works; a work may be tagged with several topics. The figure includes papers, a poster, datasets, and a preprint, not citation counts.</desc>',
              f'<rect width="{width}" height="{height}" fill="#faf9f5"/>',
              '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202e2d}.title{font-family:Georgia,serif;font-size:39px}.small{font-size:14px;fill:#52625f}.label{font-size:15px;font-weight:600}.count{fill:white;font-size:15px;font-weight:700;text-anchor:middle;dominant-baseline:central}</style>',
              '<text x="40" y="55" class="small" letter-spacing="2">ZHAOHUI LI · RESEARCH ACROSS COMMUNITIES</text>',
              '<text x="40" y="111" class="title">Publication landscape</text>',
              f'<text x="40" y="147" font-size="17">{len(records)} works · {len(venues)} venues and repositories · {len(topics)} overlapping research themes</text>']
    for i, (gid, group) in enumerate(groups.items()):
        col, row = i % 3, i // 3
        x, y = 40 + col * 443, 186 + row * 35
        pieces.append(f'<circle cx="{x + 6}" cy="{y - 5}" r="5" fill="{group["color"]}"/>')
        pieces.append(f'<text x="{x + 22}" y="{y}" font-size="14">{escape(group["label"])}</text>')
    pieces.append('<text x="40" y="267" class="small">Read across a venue for its themes; read down a theme to see connections across communities.</text>')
    pieces.append('<text x="40" y="322" class="label">Venue / repository</text><text x="40" y="346" class="small">Unique works at right</text>')
    for j, (tid, topic) in enumerate(topics.items()):
        cx = label_width + (j + .5) * col_width
        pieces.append(_svg_lines(topic["label"], cx, 312, width=16, line_height=18, font_size=14, font_weight=600, text_anchor="middle"))
        topic_groups = [gid for gid in groups if any(r["communityId"] == gid and tid in r["topicIds"] for r in records)]
        for k, gid in enumerate(topic_groups):
            dot_x = cx + (k - (len(topic_groups) - 1) / 2) * 11
            pieces.append(f'<circle cx="{dot_x}" cy="362" r="3.5" fill="{groups[gid]["color"]}"/>')
    previous_group = None
    for i, (vid, venue) in enumerate(venues.items()):
        y = top + i * row_height
        gid, color = venue["communityId"], groups[venue["communityId"]]["color"]
        if gid != previous_group:
            pieces.append(f'<line x1="40" y1="{y}" x2="{width - 40}" y2="{y}" stroke="#b6c5bc"/>')
        else:
            pieces.append(f'<line x1="40" y1="{y}" x2="{width - 40}" y2="{y}" stroke="#e3e7e0"/>')
        previous_group = gid
        cy = y + row_height / 2
        pieces.append(f'<rect x="40" y="{y + 13}" width="4" height="28" rx="2" fill="{color}"/>')
        label_lines = wrap(venue["label"], width=24, break_long_words=False)
        label_y = cy + 5 - 8 * (len(label_lines) - 1)
        pieces.append(_svg_lines(venue["label"], 57, label_y, width=24, line_height=16, font_size=14))
        pieces.append(f'<text x="275" y="{cy + 5}" text-anchor="end" font-size="14" font-weight="700">{venue_counts[vid]}</text>')
        for j, tid in enumerate(topics):
            cx = label_width + (j + .5) * col_width
            value = counts[(vid, tid)]
            if value:
                pieces.append(f'<circle cx="{cx}" cy="{cy}" r="16" fill="{color}"/><text x="{cx}" y="{cy}" class="count">{value}</text>')
            else:
                pieces.append(f'<line x1="{cx - 4}" x2="{cx + 4}" y1="{cy}" y2="{cy}" stroke="#c9d2cb"/>')
    bottom = top + len(venues) * row_height
    pieces.extend([f'<line x1="40" y1="{bottom}" x2="{width - 40}" y2="{bottom}" stroke="#b6c5bc"/>',
                   f'<text x="40" y="{bottom + 37}" class="small">Each number counts works, not citations. Circle size is constant; topic counts overlap and should not be added.</text>',
                   f'<text x="40" y="{bottom + 63}" class="small">Colors identify venue groupings, not topic totals. Gray denotes repositories for datasets and preprints.</text>',
                   f'<text x="40" y="{bottom + 89}" class="small">For example, ASD-HI appears under AIED (AI for education), although it concerns autism and special education.</text>',
                   f'<text x="40" y="{bottom + 131}" class="small">zhaohuilee.com/publications · Source: current academic CV and publication records</text>', '</svg>'])
    return '\n'.join(pieces)

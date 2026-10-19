# Zhaohui Li website

An academic website hosted on GitHub Pages at `zhaohuilee.com`. It includes a profile, research projects, publications and datasets, appointments and education, research support, awards, teaching, service, and a downloadable CV.

## Update the site

The site has no build dependencies beyond Python 3.

- Edit profile settings in `data/profile.json`.
- Edit publication records in `data/publications.json`.
- Edit project summaries, roles, mentors, collaborators, related papers, representative figures, and document evidence in `data/projects.json`. Eight selected projects follow the latest CV order through `selectedOrder`; additional work and a secondary research-area index follow them. Every publication or dataset record belongs to one primary project. SciEval and Judging the Judges share the science instructional-material evaluation project.
- `scripts/project_groups.py` builds `/projects/`, styled by `css/projects.css`. Project dates follow the authoritative CV. Recent submissions, proposals in preparation, and awarded funding use separate status labels. The page reuses original paper figures and links to full citations; merged project IDs retain bookmark aliases. Do not upload application documents as public site assets when using them as editorial sources.
- Edit paper summaries and figure provenance in `data/highlights-recent.json` (2025–2026) and `data/highlights-earlier.json` (2014–2024). Every paper, workshop paper, and preprint needs exactly one highlight; the AERA poster and two dataset records remain separate in the full publication list.
- Paper images in `files/paper-figures/` are crops of figures from the actual papers, not generated illustrations. Each record preserves the original PDF filename, one-based source page, crop box in PDF points, figure number, source URL, alt text, and image dimensions. Keep source attribution visible.
- `scripts/highlights.py` renders paper highlights, with year/search/order controls in `js/highlights.js`. Papers are sorted by year (newest first), not unverified citation counts. The home page previews the six newest papers.
- Edit publication communities, venue groups, and overlapping topic tags in `data/publication-map.json`. Every publication must appear exactly once in this mapping; each can have multiple topics. The map distinguishes repositories from conference/journal communities and counts works, not citations.
- Edit page content and templates in `scripts/build_site.py`.
- Edit layout in `css/academic.css` and interactions in `js/academic.js`.
- The publication figure is rendered by `scripts/publication_map.py`, with responsive styles in `css/publication-map.css` and selections in `js/publication-map.js`. The build also generates the downloadable `files/publication-map.svg` from the same records.
- Regenerate HTML and validate local links and publication records:

```sh
python3 scripts/build_site.py
python3 scripts/check_site.py
```

Preview locally with `python3 -m http.server 8766 --bind 127.0.0.1`, then open `http://127.0.0.1:8766`. Review changes at both desktop and mobile widths. Commit the source and generated pages together, then push to `master` to deploy through GitHub Pages.

## CV and portrait

The current CV is `files/Zhaohui_Li_CV.pdf`. Its editable LaTeX source is `cv-source/main.tex`, synchronized with the user's original template in `Academic_CV_ZhaohuiLI_Updated/main.tex` in the parent Career workspace (October 2026). Keep that editor source authoritative and synchronize approved changes before rebuilding the website download. To rebuild it with Tectonic:

```sh
mkdir -p tmp
tectonic --untrusted cv-source/main.tex -o tmp
cp tmp/main.pdf files/Zhaohui_Li_CV.pdf
```

Check the generated PDF before publishing. The portrait at `files/zhaohui-2026.jpg` is the original photo supplied by Zhaohui Li, with the display crop controlled by CSS.

The website retains previously verified complete author lists and publication links. The CV uses abbreviated citations; do not overwrite verified website metadata mechanically when synchronizing the CV. The AERA 2026 AIRE entry is a poster, not a proceedings paper. Update `updated`, `updated_date`, and `cv_updated` in `data/profile.json` only when the corresponding content has actually been refreshed. Contact links use the `email` field in the same profile.

The Google Scholar profile ID is `FuS676UAAAAJ`, matched through the linked AD Scientific Index profile (scientist 5407053), Penn State affiliation, Passonneau/Jun Xu coauthors, and exact papers. Scholar blocks automated retrieval; citation counts are not scraped or estimated. LLM4Art follows the article's byline (Zhaohui Li and Naiquan Li, equal first authors), not the differing proceedings table of contents.

## Domain

The custom domain is configured in `CNAME`. HTTPS requires valid DNS records and a certificate provisioned by GitHub Pages. After enabling HTTPS, update `base_url` in `data/profile.json` and regenerate the pages so canonical links and the sitemap use HTTPS.

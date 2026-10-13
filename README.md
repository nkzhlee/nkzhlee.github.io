# Zhaohui Li website

An academic website hosted on GitHub Pages at `zhaohuilee.com`. It includes a profile, research projects, publications and datasets, appointments and education, research support, awards, teaching, service, and a downloadable CV.

## Update the site

The site has no build dependencies beyond Python 3.

- Edit profile settings in `data/profile.json`.
- Edit publication records in `data/publications.json`.
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

The website retains previously verified complete author lists and publication links. The CV uses abbreviated citations; do not overwrite verified website metadata mechanically when synchronizing the CV. The AERA 2026 AIRE entry is a poster, not a proceedings paper. Spencer Foundation support is a proposal in submission, not an awarded grant. Update `updated`, `updated_date`, and `cv_updated` in `data/profile.json` only when the corresponding content has actually been refreshed.

## Domain

The custom domain is configured in `CNAME`. HTTPS requires valid DNS records and a certificate provisioned by GitHub Pages. After enabling HTTPS, update `base_url` in `data/profile.json` and regenerate the pages so canonical links and the sitemap use HTTPS.

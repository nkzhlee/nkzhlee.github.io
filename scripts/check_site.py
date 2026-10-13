#!/usr/bin/env python3
"""Validate generated academic pages before deployment; Python standard library only."""

from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlsplit
from publication_map import render_publication_map_svg
from highlights import ordered_highlights
from project_groups import validate_project_groups


ROOT = Path(__file__).resolve().parents[1]
PAGES = ["index.html"] + [
    f"{name}/index.html"
    for name in ("projects", "research", "publications", "experience", "teaching", "cv", "blog")
]
VOID_TAGS = set("area base br col embed hr img input link meta param source track wbr".split())


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags = Counter()
        self.ids = Counter()
        self.meta = {}
        self.refs = []
        self.publications = []
        self.highlights = []
        self.images = []
        self.projects = []
        self.project_publications = []
        self.title = []
        self.count_text = []
        self.stack = []
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.tags[tag] += 1
        element_id = attrs.get("id")
        if element_id is not None:
            self.ids[element_id] += 1
        if tag == "meta":
            self.meta[attrs.get("name", "").lower()] = attrs.get("content", "")
        for attribute in ("href", "src"):
            if attrs.get(attribute) is not None:
                self.refs.append((attrs[attribute], self.getpos()[0]))
        if "data-publication" in attrs:
            self.publications.append(element_id)
        if "data-highlight" in attrs:
            self.highlights.append(element_id)
        if "data-project" in attrs:
            self.projects.append(element_id)
        if "data-project-publication" in attrs:
            self.project_publications.append(attrs["data-project-publication"])
        if tag == "img":
            self.images.append(attrs)
        if tag not in VOID_TAGS:
            self.stack.append((tag, element_id))

    def handle_startendtag(self, tag, attributes):
        self.handle_starttag(tag, attributes)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, text):
        if any(tag == "title" for tag, _ in self.stack):
            self.title.append(text)
        if any(element_id == "publication-count" for _, element_id in self.stack):
            self.count_text.append(text)


def main():
    errors = []
    parsed = {}
    linked_files = set()

    def problem(path, message):
        errors.append(f"{path.relative_to(ROOT)}: {message}")

    def read_page(path):
        if path not in parsed:
            parsed[path] = Page(path.read_text(encoding="utf-8"))
        return parsed[path]

    for relative in PAGES:
        path = ROOT / relative
        if not path.is_file():
            problem(path, "missing generated page")
            continue
        page = read_page(path)
        source = path.read_text(encoding="utf-8")
        if "orcid.org" in source or "ORCID" in source:
            problem(path, "ORCID remains after replacement with Google Scholar")
        if "scholar.google.com/citations?user=FuS676UAAAAJ" not in source:
            problem(path, "missing Google Scholar profile link")
        for image in page.images:
            if not image.get("alt", "").strip():
                problem(path, f"missing descriptive image alt text: {image.get('src')}")
        for tag in ("h1", "main", "title"):
            if page.tags[tag] != 1:
                problem(path, f"expected one <{tag}>, found {page.tags[tag]}")
        if not "".join(page.title).strip():
            problem(path, "empty page title")
        for name in ("viewport", "description"):
            if not page.meta.get(name, "").strip():
                problem(path, f"missing or empty meta {name}")
        for element_id, count in page.ids.items():
            if not element_id or count > 1:
                problem(path, f"invalid or duplicate id {element_id!r} ({count} occurrences)")

        for reference, line in page.refs:
            url = urlsplit(reference)
            if url.scheme or url.netloc:
                continue
            decoded_path = unquote(url.path)
            target = (
                ROOT / decoded_path.lstrip("/")
                if decoded_path.startswith("/")
                else path.parent / decoded_path if decoded_path else path
            ).resolve()
            if not target.is_relative_to(ROOT):
                problem(path, f"line {line}: local URL leaves the site: {reference}")
                continue
            if target.is_dir() or decoded_path.endswith("/"):
                target /= "index.html"
            if not target.is_file():
                problem(path, f"line {line}: missing target for {reference!r}")
                continue
            linked_files.add(target)
            if url.fragment and target.suffix.lower() in (".html", ".htm"):
                fragment = unquote(url.fragment)
                # Text fragments do not refer to an element ID.
                fragment = fragment.split(":~:text=", 1)[0]
                if fragment and fragment not in read_page(target).ids:
                    problem(path, f"line {line}: missing fragment target for {reference!r}")

    for asset in ("files/Zhaohui_Li_CV.pdf", "files/zhaohui-2026.jpg", "files/publication-map.svg"):
        path = ROOT / asset
        if not path.is_file() or path.stat().st_size == 0:
            problem(path, "missing or empty required asset")
        elif path not in linked_files:
            problem(path, "required asset is not linked from a primary page")

    data_path = ROOT / "data/publications.json"
    try:
        publications = json.loads(data_path.read_text(encoding="utf-8"))
        if not isinstance(publications, list) or not all(isinstance(p, dict) for p in publications):
            raise ValueError("expected a list of publication objects")
        identifiers = [p.get("id") for p in publications]
        if not all(isinstance(identifier, str) and identifier.strip() for identifier in identifiers):
            raise ValueError("every publication must have a nonempty string id")
        duplicates = [identifier for identifier, count in Counter(identifiers).items() if count > 1]
        if duplicates:
            problem(data_path, f"duplicate publication IDs: {', '.join(duplicates)}")
        visible = [p["id"] for p in publications if p.get("status", "") != "Status to confirm"]
        page = parsed.get(ROOT / "publications/index.html")
        if page is not None:
            if Counter(page.publications) != Counter(visible):
                problem(ROOT / "publications/index.html", "publication cards do not match visible data records")
            count = re.match(r"\s*(\d+)\b", "".join(page.count_text))
            if not count or int(count.group(1)) != len(visible):
                problem(ROOT / "publications/index.html", f"displayed count must be {len(visible)}")
        taxonomy_path = ROOT / "data/publication-map.json"
        taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        expected_figure = render_publication_map_svg([p for p in publications if p["id"] in visible], taxonomy)
        figure_path = ROOT / "files/publication-map.svg"
        figure_source = figure_path.read_text(encoding="utf-8")
        ET.fromstring(figure_source)
        if figure_source != expected_figure:
            problem(figure_path, "stale figure: rerun scripts/build_site.py")
        if "publication-map" not in read_page(ROOT / "publications/index.html").ids:
            problem(ROOT / "publications/index.html", "missing publication map")
        highlights = [h for path in sorted((ROOT / "data").glob("highlights-*.json")) for h in json.loads(path.read_text())]
        ordered = ordered_highlights(publications, highlights)
        project_data = json.loads((ROOT / "data/projects.json").read_text(encoding="utf-8"))
        validate_project_groups(project_data, publications, highlights)
        projects_page = read_page(ROOT / "projects/index.html")
        if Counter(projects_page.projects) != Counter(project["id"] for project in project_data["projects"]):
            problem(ROOT / "projects/index.html", "project cards do not match project data")
        if Counter(projects_page.project_publications) != Counter(identifiers):
            problem(ROOT / "projects/index.html", "project member links do not cover each publication and resource once")
        expected_highlights = [f'highlight-{p["id"]}' for p, _ in ordered]
        if read_page(ROOT / "research/index.html").highlights != expected_highlights:
            problem(ROOT / "research/index.html", "missing, extra, or out-of-order paper highlights")
        for record in highlights:
            image = ROOT / record["image"].lstrip("/")
            if not image.is_file() or image.stat().st_size == 0:
                problem(image, "missing or empty paper figure")
            if not record["imageAlt"] or not record["summary"] or not record["sourceUrl"].startswith("https://"):
                raise ValueError(f"Incomplete highlight: {record['id']}")
            if record["sourcePage"] < 1 or len(record["crop"]) != 4 or min(record["imageWidth"], record["imageHeight"]) < 1:
                raise ValueError(f"Invalid figure provenance or dimensions: {record['id']}")
    except (OSError, ValueError, KeyError, ET.ParseError) as exc:
        problem(data_path, str(exc))

    if errors:
        print("Site validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Site validation passed: {len(PAGES)} pages, {len(visible)} publication records, {len(ordered)} paper highlights, {len(project_data['projects'])} grouped projects, map taxonomy/SVG, Google Scholar, local links and assets verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

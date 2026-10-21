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
        self.books = []
        self.publication_groups = {}
        self.map_elements = []
        self.h1_text = []
        self.highlights = []
        self.images = []
        self.projects = []
        self.project_publications = []
        self.main_sections = []
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
        if element_id == "publication-map" or any(ancestor == "publication-map" for _, ancestor in self.stack):
            self.map_elements.append((tag, attrs, tuple(self.stack)))
        if tag == "meta":
            self.meta[attrs.get("name", "").lower()] = attrs.get("content", "")
        for attribute in ("href", "src"):
            if attrs.get(attribute) is not None:
                self.refs.append((attrs[attribute], self.getpos()[0]))
        if "data-publication-group" in attrs:
            self.publication_groups[element_id] = []
        if "data-book" in attrs:
            self.books.append(element_id)
        elif "data-publication" in attrs:
            self.publications.append(element_id)
        if "data-publication" in attrs:
            group = next((ancestor for _, ancestor in reversed(self.stack) if ancestor in self.publication_groups), None)
            if group:
                self.publication_groups[group].append(element_id)
        if "data-highlight" in attrs:
            self.highlights.append(element_id)
        if "data-project" in attrs:
            self.projects.append(element_id)
        if "data-project-publication" in attrs:
            self.project_publications.append(attrs["data-project-publication"])
        if tag == "section" and self.stack and self.stack[-1][0] == "main":
            self.main_sections.append(element_id)
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
        if any(tag == "h1" for tag, _ in self.stack):
            self.h1_text.append(text)
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
        navigation = re.search(r'<nav aria-label="Primary navigation">(.*?)</nav>', source, re.S)
        if not navigation or any(reference in ("/teaching/", "/research/") for reference, _ in Page(navigation.group(1)).refs):
            problem(path, "primary navigation must keep Research and Service unlisted")
        if "orcid.org" in source or "ORCID" in source:
            problem(path, "ORCID remains after replacement with Google Scholar")
        if "scholar.google.com/citations?user=FuS676UAAAAJ" not in source:
            problem(path, "missing Google Scholar profile link")
        if any(text not in source for text in (
            'title="AI for the Next Generation"',
            '<span class="wordmark-principle">AI for the Next Generation</span>',
        )):
            problem(path, "header tagline must be AI for the Next Generation")
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

    home_path = ROOT / "index.html"
    home_source = home_path.read_text(encoding="utf-8")
    contact_path = ROOT / "cv/index.html"
    contact_source = contact_path.read_text(encoding="utf-8")
    contact_main = re.search(r"<main\b[^>]*>(.*?)</main>", contact_source, re.S)
    profile = json.loads((ROOT / "data/profile.json").read_text(encoding="utf-8"))
    appointment = re.search(r'<p class="appointment">(.*?)</p>', home_source, re.S)
    if not appointment:
        problem(home_path, "missing homepage appointment")
    else:
        appointment_refs = [reference for reference, _ in Page(appointment.group(1)).refs]
        if profile["college_url"] not in appointment_refs or profile["institution_url"] in appointment_refs:
            problem(home_path, "homepage appointment must link to the college instead of the university")
    if "".join(read_page(contact_path).h1_text).strip() != "Contact":
        problem(contact_path, "Contact page must have a Contact heading")
    if not contact_main or any(text in contact_main.group(1) for text in (
        "cv-panel", "Curriculum vitae", "Academic CV", "Open CV", "Download a copy",
    )):
        problem(contact_path, "Contact main content must not duplicate the CV panel")
    contact_refs = [reference for reference, _ in read_page(contact_path).refs]
    profile_links = re.search(r'<div class="profile-links">(.*?)</div>', home_source, re.S)
    if not profile_links or (
        profile["linkedin_url"] not in [reference for reference, _ in Page(profile_links.group(1)).refs]
        or ">LinkedIn</a>" not in profile_links.group(1)
    ):
        problem(home_path, "profile links must include the configured LinkedIn profile")
    booking_url = profile.get("booking_url", "").strip()
    if booking_url:
        if booking_url not in contact_refs:
            problem(contact_path, "missing configured public booking link")
        if not profile_links or (
            booking_url not in [reference for reference, _ in Page(profile_links.group(1)).refs]
            or ">Book a Meeting</a>" not in profile_links.group(1)
        ):
            problem(home_path, "profile links must include Book a Meeting using the configured public booking URL")
        parsed_booking = urlsplit(booking_url)
        if parsed_booking.scheme != "https" or parsed_booking.hostname not in {
            "book.ms", "outlook.office.com", "outlook.office365.com",
            "outlook.cloud.microsoft", "bookings.cloud.microsoft",
        }:
            problem(contact_path, "booking link must use an official Microsoft HTTPS host")
    elif "Request a meeting by email" not in contact_source:
        problem(contact_path, "unconfigured booking must offer an honest email fallback")
    if "/files/Zhaohui_Li_CV.pdf" not in [
        reference for reference, _ in read_page(home_path).refs
    ]:
        problem(home_path, "About must retain the direct CV link")
    news_match = re.search(r'<section\b[^>]*\bid="recent-news"[^>]*>(.*?)</section>', home_source, re.S)
    research_match = re.search(r'<section\b[^>]*\bid="research-experience"[^>]*>(.*?)</section>', home_source, re.S)
    if not news_match or not research_match:
        problem(home_path, "missing Research Experience or Recent News section")
    else:
        if news_match.end() > research_match.start():
            problem(home_path, "Recent News must precede Research Experience")
        news = news_match.group(1)
        if '<h2 id="recent-news-heading">Recent News</h2>' not in news:
            problem(home_path, "news heading must be Recent News")
        research = research_match.group(1)
        if "proceedings" in news.lower():
            problem(home_path, "Recent news should refer to conferences rather than proceedings")
        for required in (
            "/publications/#edited-books", "under contract", "AIED 2027", "LAK 2027",
            "https://iaied.org/conferences", "https://www.solaresearch.org/events/lak/lak27/",
            "I secured a $50,000", "Organization for Autism Research grant", "as Co-PI",
            "/publications/#aire-aera-2026", "was presented as a poster",
            'aria-expanded="false"', 'aria-controls="more-news-items"',
        ):
            if required not in news:
                problem(home_path, f"Recent news is missing {required!r}")
        initial_news = re.search(r"<ul>(.*?)</ul>", news, re.S)
        if not initial_news or initial_news.group(1).count("data-news-item=") != 6:
            problem(home_path, "Recent news must show six items before the expandable list")
        news_ids = re.findall(r'data-news-item="([^"]+)"', news)
        news_dates = json.loads((ROOT / "data/news-dates.json").read_text())
        if set(news_ids) != set(news_dates) or news.count('<time datetime=') != len(news_ids):
            problem(home_path, "every news announcement must have dated metadata and a visible date")
        elif news_ids != sorted(news_ids, key=lambda identifier: news_dates[identifier]["sort_date"], reverse=True):
            problem(home_path, "news announcements must be newest first")
        for identifier in ("book-contract", "conference-service"):
            if news_dates[identifier]["kind"] != "Website update":
                problem(home_path, "unverified signing/appointment dates must be labeled as website updates")
        if len(news_ids) != len(set(news_ids)):
            problem(home_path, "Recent news has duplicate announcements")
        news_publications = re.findall(r'data-news-publication="([^"]+)"', news)
        expected_news_publications = [
            p["id"] for p in json.loads((ROOT / "data/publications.json").read_text())
            if p.get("year") == 2026
        ]
        if Counter(news_publications) != Counter(expected_news_publications):
            problem(home_path, "Recent news must include every 2026 publication/presentation exactly once")
        more_news = re.search(r'<ul\b[^>]*\bid="more-news-items"[^>]*>(.*?)</ul>', news, re.S)
        if not more_news or more_news.group(1).count("data-news-item=") != len(news_ids) - 6:
            problem(home_path, "remaining announcements must be in the expandable news list")
        for moved in ("Organization for Autism Research grant", "Program committee member", "AIRE poster"):
            if moved in research:
                problem(home_path, f"news item remains in Research Experience: {moved!r}")
        for funding in ("$20 million", "Jan 2023–Dec 2027", "$10 million", "Sep 2024–Aug 2029"):
            if funding not in research:
                problem(home_path, f"Research Experience is missing center funding detail {funding!r}")
        if research.count("Total center funding:") != 2 or research.count("award period:") != 2:
            problem(home_path, "center funding and award periods must be clearly labeled")
        if research.count("My role: Aug 2024–present.") != 2:
            problem(home_path, "personal center role dates must be separate from award periods")
    if 'class="wrap section book-update"' in home_source:
        problem(home_path, "book announcement must be a news item, not a standalone section")
    experience_path = ROOT / "experience/index.html"
    experience_source = experience_path.read_text()
    for expected in ('href="#teaching-mentoring"', 'id="teaching-mentoring"', 'five doctoral students',
                     'three master’s students', 'Proposed course: AI for Education.'):
        if expected not in experience_source:
            problem(experience_path, f"missing teaching and mentoring evidence: {expected}")
    award = "Best Doctoral Dissertation in AI-Related Discipline"
    cv_source = (ROOT / "cv-source/main.tex").read_text()
    for path, source in ((home_path, home_source), (experience_path, experience_source), (ROOT / "cv-source/main.tex", cv_source)):
        if award not in source or "Best Doctoral Dissertation Award" in source:
            problem(path, "use the specific AI-related dissertation award title consistently")
    if "Shiyang Jiang" in cv_source or "Shiyang Jiang" in (ROOT / "data/projects.json").read_text():
        problem(ROOT / "data/projects.json", "collaborator name must be Shiyan Jiang")
    if "upcoming: AIED 2027 and LAK 2027" not in cv_source:
        problem(ROOT / "cv-source/main.tex", "CV must distinguish upcoming committee service")

    for asset in ("files/Zhaohui_Li_CV.pdf", "files/zhaohui-2026.jpg", "files/publication-map.svg"):
        path = ROOT / asset
        if not path.is_file() or path.stat().st_size == 0:
            problem(path, "missing or empty required asset")
        elif path not in linked_files and asset != "files/publication-map.svg":
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
        books = json.loads((ROOT / "data/edited-books.json").read_text(encoding="utf-8"))
        page = parsed.get(ROOT / "publications/index.html")
        if page is not None:
            publication_path = ROOT / "publications/index.html"
            publication_source = publication_path.read_text()
            disclosure = re.search(r'<details class="publication-map-disclosure">.*?</details>', publication_source, re.S)
            citation_list = publication_source.find('id="publication-list"')
            if not disclosure or citation_list < 0 or disclosure.end() > citation_list:
                problem(publication_path, "optional map must be collapsed and appear before the citation list")
            if "Venue groupings, not topic totals" not in publication_source or "ASD-HI appears under AIED" not in publication_source:
                problem(publication_path, "map must retain the accessible explanation of venue grouping counts")
            for class_name in ("map-summary", "map-instruction", "map-note"):
                explanations = [attrs for _, attrs, ancestors in page.map_elements
                                if class_name in attrs.get("class", "").split()
                                and not any(tag == "noscript" for tag, _ in ancestors)]
                if len(explanations) != 1 or "hidden" not in explanations[0]:
                    problem(publication_path, f"map explanation {class_name} must have the hidden attribute")
            grouping_notes = [attrs for _, attrs, _ in page.map_elements if attrs.get("id") == "map-grouping-note"]
            if len(grouping_notes) != 1 or (
                "visually-hidden" not in grouping_notes[0].get("class", "").split()
                or "hidden" in grouping_notes[0] or grouping_notes[0].get("aria-hidden") == "true"
            ):
                problem(publication_path, "map grouping explanation must be visually hidden but accessible")
            legends = [attrs for _, attrs, _ in page.map_elements if "map-legend" in attrs.get("class", "").split()]
            if len(legends) != 1 or "map-grouping-note" not in legends[0].get("aria-describedby", "").split():
                problem(publication_path, "map legend must retain its accessible grouping description")
            fallback_notes = [attrs for _, attrs, ancestors in page.map_elements
                              if "map-note" in attrs.get("class", "").split()
                              and any(tag == "noscript" for tag, _ in ancestors)]
            if len(fallback_notes) != 1 or (
                "hidden" in fallback_notes[0] or "visually-hidden" in fallback_notes[0].get("class", "").split()
            ):
                problem(publication_path, "map must retain a visible no-JavaScript fallback note")
            map_css_path = ROOT / "css/publication-map.css"
            summary_hidden_rule = re.search(r"\.map-summary\[hidden\]\s*\{[^}]*\bdisplay\s*:\s*none\b", map_css_path.read_text())
            global_hidden_rule = re.search(r"\[hidden\]\s*\{[^}]*\bdisplay\s*:\s*none\s*!important", (ROOT / "css/academic.css").read_text())
            if not summary_hidden_rule and not global_hidden_rule:
                problem(map_css_path, "hidden map summary must override its flex display")
            if Counter(page.publications) != Counter(visible):
                problem(ROOT / "publications/index.html", "publication cards do not match visible data records")
            if Counter(page.books) != Counter(book["id"] for book in books):
                problem(publication_path, "edited books do not match book data")
            count = re.match(r"\s*(\d+)\b", "".join(page.count_text))
            expected_count = len(visible) + len(books)
            if not count or int(count.group(1)) != expected_count:
                problem(publication_path, f"displayed count must be {expected_count}")
            if "".join(page.h1_text).strip() != "Publications":
                problem(publication_path, "page heading must be Publications")
            expected_groups = {
                "conference-publications": {"conference", "workshop", "poster"},
                "journal-publications": {"journal"},
                "data-publications": {"dataset", "preprint"},
                "edited-books": {"book"},
            }
            if list(page.publication_groups) != list(expected_groups):
                problem(publication_path, "publication sections must be ordered Conference, Journal, Data, Book")
            for group, allowed_types in expected_groups.items():
                expected = [book["id"] for book in books] if group == "edited-books" else [
                    p["id"] for p in sorted(publications, key=lambda p: p.get("year") or 0, reverse=True)
                    if p["id"] in visible and p["type"] in allowed_types
                ]
                if page.publication_groups.get(group) != expected:
                    problem(publication_path, f"wrong records or year order in {group}")
            if any(urlsplit(reference).path == "/files/publication-map.svg" for reference, _ in page.refs):
                problem(publication_path, "SVG download link must not be displayed")
        taxonomy_path = ROOT / "data/publication-map.json"
        taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        expected_labels = [
            "AI for education", "AI, NLP & Other ML", "Education Technology",
            "Special Education", "Datasets & Others",
        ]
        if [community["label"] for community in taxonomy["communities"]] != expected_labels:
            problem(taxonomy_path, "community labels or display order do not match requested categories")
        if [venue["id"] for venue in taxonomy["venues"][:4]] != ["aied", "aied-workshop", "lak", "caeai"]:
            problem(taxonomy_path, "AI for education venues must come first, starting with AIED")
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
        projects_path = ROOT / "projects/index.html"
        projects_page = read_page(projects_path)
        projects_source = projects_path.read_text(encoding="utf-8")
        if "project-theme-nav" in projects_source or 'aria-label="Project sections"' in projects_source:
            problem(projects_path, "Projects must not display the redundant section navigation row")
        if "future-projects" in projects_page.ids or any(
            urlsplit(reference).fragment == "future-projects" for reference, _ in projects_page.refs
        ):
            problem(projects_path, "Future directions must remain unlisted on Projects")
        if projects_page.main_sections != ["selected-projects", "project-topics", "additional-projects"]:
            problem(projects_path, "Projects must show selected work, research areas, then additional and earlier work last")
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

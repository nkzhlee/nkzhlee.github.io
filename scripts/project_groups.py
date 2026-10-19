"""Render selected research experience and related works, with a secondary topic index."""
from collections import Counter
from html import escape
import re


def validate_project_groups(data, publications, highlights):
    themes = {theme["id"]: theme for theme in data["themes"]}
    projects = data["projects"]
    if len(themes) != len(data["themes"]) or not themes:
        raise ValueError("Research themes need unique IDs")
    project_ids = [project["id"] for project in projects]
    if len(set(project_ids)) != len(project_ids):
        raise ValueError("Projects need unique IDs")
    anchors = project_ids + [alias for project in projects for alias in project.get("aliases", [])]
    if len(set(anchors)) != len(anchors) or set(anchors) & set(themes):
        raise ValueError("Project IDs and bookmark aliases need unique anchors")
    selected = [project for project in projects if project.get("selectedOrder") is not None]
    if sorted(project["selectedOrder"] for project in selected) != list(range(1, len(selected) + 1)):
        raise ValueError("Selected projects need consecutive, unique ordering")
    papers = {paper["id"]: paper for paper in publications}
    figures = {figure["id"]: figure for figure in highlights}
    members = [identifier for project in projects for identifier in project["publicationIds"]]
    if Counter(members) != Counter(papers.keys()):
        raise ValueError("Each publication or resource must belong to exactly one project")
    for theme in themes.values():
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", theme["color"]):
            raise ValueError("Invalid research-theme color")
    for project in projects:
        if project["themeId"] not in themes or any(identifier not in themes for identifier in project["relatedThemeIds"]):
            raise ValueError(f"Unknown theme in {project['id']}")
        if project.get("figureId") and (project["figureId"] not in figures or project["figureId"] not in project["publicationIds"]):
            raise ValueError(f"Figure must come from a related paper: {project['id']}")
        if not project["title"].strip() or not project["summary"].strip():
            raise ValueError(f"Incomplete project: {project['id']}")
        if project.get("selectedOrder") is not None and (project.get("role") != "Research lead" or not project.get("mentor", {}).get("name")):
            raise ValueError(f"Selected research needs a role and mentor: {project['id']}")
    science = next((p for p in projects if "scieval-2026" in p["publicationIds"]), None)
    if not science or "judging-judges-2026" not in science["publicationIds"]:
        raise ValueError("SciEval and Judging the Judges must share one project")
    return themes, papers, figures


def render_person(person):
    name = escape(person["name"])
    if person.get("url"):
        name = f'<a href="{escape(person["url"], quote=True)}">{name}</a>'
    if person.get("affiliation"):
        affiliation = escape(person["affiliation"])
        if person.get("affiliationUrl"):
            affiliation = f'<a href="{escape(person["affiliationUrl"], quote=True)}">{affiliation}</a>'
        name += f' ({affiliation})'
    if person.get("note"):
        name += f' · {escape(person["note"])}'
    return name


def render_metadata(project):
    rows = []
    if project.get("role"):
        rows.append(f'<div><dt>Role</dt><dd>{escape(project["role"])}</dd></div>')
    if project.get("mentor"):
        rows.append(f'<div><dt>Mentor</dt><dd>{render_person(project["mentor"])}</dd></div>')
    collaborators = project.get("collaborators", [])
    if collaborators:
        label = "Collaborator" if len(collaborators) == 1 else "Collaborators"
        rows.append(f'<div><dt>{label}</dt><dd>{"; ".join(render_person(person) for person in collaborators)}</dd></div>')
    if project.get("organizations"):
        rows.append(f'<div><dt>Center</dt><dd>{"; ".join(render_person(org) for org in project["organizations"])}</dd></div>')
    return '<dl class="project-details">' + ''.join(rows) + '</dl>' if rows else ''


def render_project(project, themes, papers, figures):
    e = escape
    identifier = e(project["id"], quote=True)
    figure = ""
    if project.get("figureId"):
        visual = figures[project["figureId"]]
        figure = f'''<figure class="project-figure"><a href="{e(visual['sourceUrl'], quote=True)}"><img src="{e(visual['image'], quote=True)}" alt="{e(visual['imageAlt'], quote=True)}" width="{int(visual['imageWidth'])}" height="{int(visual['imageHeight'])}" loading="lazy" decoding="async"></a><figcaption><a href="{e(visual['sourceUrl'], quote=True)}">{e(visual['figureLabel'])} · {e(project['figureTitle'])}</a></figcaption></figure>'''
    related = []
    for paper_id in sorted(project["publicationIds"], key=lambda key: papers[key].get("year") or 0, reverse=True):
        paper = papers[paper_id]
        venue = paper.get("venue", paper["type"])
        related.append(f'<li data-project-publication="{e(paper_id, quote=True)}"><a href="/publications/#{e(paper_id, quote=True)}">{e(paper["title"])}</a><span class="project-work-meta">{paper.get("year") or "Undated"} · {e(venue)}</span></li>')
    works = '<h4 class="related-work-heading">Related papers &amp; resources</h4><ul class="project-works">' + ''.join(related) + '</ul>' if related else ''
    connections = ''.join(f'<a href="#{e(key, quote=True)}" style="--theme-color:{themes[key]["color"]}">{e(themes[key]["shortTitle"])}</a>' for key in project["relatedThemeIds"])
    connections = f'<p class="project-connections">Also connects with: {connections}</p>' if connections else ''
    metadata = render_metadata(project)
    updates = []
    for update in project.get("updates", []):
        text = e(update["text"])
        if update.get("url"):
            text = f'<a href="{e(update["url"], quote=True)}">{text}</a>'
        updates.append(f'<li><strong>{e(update["label"])}:</strong> {text}</li>')
    updates = '<ul class="project-updates">' + ''.join(updates) + '</ul>' if updates else ''
    aliases = ''.join(f'<span class="project-alias" id="{e(alias, quote=True)}" aria-hidden="true"></span>' for alias in project.get("aliases", []))
    number = f'<span class="project-number">{project["selectedOrder"]:02d}.</span> ' if project.get("selectedOrder") else ''
    return f'''<article class="research-project{'' if figure else ' no-figure'}" id="{identifier}" data-project data-project-theme="{e(project['themeId'], quote=True)}">
{aliases}{figure}<div class="project-body"><p class="project-meta">{e(project['status'])} · {e(project['timeframe'])}</p><h3>{number}{e(project['title'])}</h3>{metadata}<p>{e(project['summary'])}</p>{updates}{connections}{works}</div></article>'''


def render_projects(data, publications, highlights):
    themes, papers, figures = validate_project_groups(data, publications, highlights)
    body = '<nav class="wrap project-theme-nav" aria-label="Project sections"><a href="#selected-projects">Selected research experience</a><a href="#additional-projects">Additional &amp; earlier work</a><a href="#project-topics">Browse by research area</a><a href="#future-projects">Future directions</a></nav>'
    selected = sorted((project for project in data["projects"] if project.get("selectedOrder") is not None), key=lambda project: project["selectedOrder"])
    additional = [project for project in data["projects"] if project.get("selectedOrder") is None]
    cards = ''.join('<li>' + render_project(project, themes, papers, figures) + '</li>' for project in selected)
    body += f'<section class="wrap project-section" id="selected-projects"><header><h2>Selected research experience</h2></header><ol class="selected-projects">{cards}</ol></section>'
    cards = ''.join(render_project(project, themes, papers, figures) for project in additional)
    body += f'<section class="wrap project-section" id="additional-projects"><header><h2>Additional &amp; earlier work</h2></header>{cards}</section>'
    body += '<section class="wrap project-topics" id="project-topics"><h2>Browse by research area</h2><div class="project-topic-grid">'
    for theme in data["themes"]:
        projects = [project for project in selected + additional if theme["id"] in [project["themeId"], *project["relatedThemeIds"]]]
        links = ''.join(f'<li><a href="#{escape(project["id"], quote=True)}">{escape(project["title"])}</a></li>' for project in projects)
        body += f'<section class="project-topic" id="{escape(theme["id"], quote=True)}" style="--theme-color:{theme["color"]}"><h3>{escape(theme["shortTitle"])}</h3><p>{escape(theme["description"])}</p><ul>{links}</ul></section>'
    return body + '</div></section>'

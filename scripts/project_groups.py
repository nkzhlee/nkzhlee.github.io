"""Render related research works as projects, organized by research theme."""
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
    science = next((p for p in projects if "scieval-2026" in p["publicationIds"]), None)
    if not science or "judging-judges-2026" not in science["publicationIds"]:
        raise ValueError("SciEval and Judging the Judges must share one project")
    return themes, papers, figures


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
        related.append(f'<li data-project-publication="{e(paper_id, quote=True)}"><a href="/publications/#{e(paper_id, quote=True)}">{e(paper["title"])}</a><span class="project-work-meta">{paper.get("year") or "Undated"} · {e(paper["type"])}</span></li>')
    works = '<h4 class="related-work-heading">Related papers &amp; resources</h4><ul class="project-works">' + ''.join(related) + '</ul>' if related else ''
    connections = ''.join(f'<a href="#{e(key, quote=True)}" style="--theme-color:{themes[key]["color"]}">{e(themes[key]["shortTitle"])}</a>' for key in project["relatedThemeIds"])
    connections = f'<p class="project-connections">Also connects with: {connections}</p>' if connections else ''
    role = f'<p class="project-role">{e(project["role"])}</p>' if project.get("role") else ''
    return f'''<article class="research-project{'' if figure else ' no-figure'}" id="{identifier}" data-project data-project-theme="{e(project['themeId'], quote=True)}">
{figure}<div class="project-body"><p class="project-meta">{e(project['status'])} · {e(project['timeframe'])}</p><h3>{e(project['title'])}</h3><p>{e(project['summary'])}</p>{role}{connections}{works}</div></article>'''


def render_projects(data, publications, highlights):
    themes, papers, figures = validate_project_groups(data, publications, highlights)
    links = ''.join(f'<a href="#{escape(theme["id"], quote=True)}" style="--theme-color:{theme["color"]}"><span aria-hidden="true"></span>{escape(theme["shortTitle"])}</a>' for theme in data["themes"])
    body = f'<nav class="wrap project-theme-nav" aria-label="Research themes">{links}<a href="#future-projects">Future directions</a></nav>'
    for theme in data["themes"]:
        projects = [project for project in data["projects"] if project["themeId"] == theme["id"]]
        cards = ''.join(render_project(project, themes, papers, figures) for project in projects)
        body += f'<section class="wrap project-theme-section" id="{escape(theme["id"], quote=True)}" style="--theme-color:{theme["color"]}"><header><h2>{escape(theme["title"])}</h2><p>{escape(theme["description"])}</p></header>{cards}</section>'
    return body

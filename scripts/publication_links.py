"""Consistent links to individual paper files hosted on this site."""
from html import escape


def paper_url(paper):
    download = paper.get("download", {})
    if download.get("url"):
        return download["url"]
    return next((link["url"] for link in paper.get("links", [])), "")


def download_link(paper):
    download = paper.get("download", {})
    if not download.get("url"):
        return ""
    url = escape(download["url"], quote=True)
    label = escape(f'Download PDF: {paper["title"]}', quote=True)
    return f'<a class="paper-download" href="{url}" download aria-label="{label}">Download PDF <span aria-hidden="true">↓</span></a>'


def pdf_version(paper):
    version = paper.get("download", {}).get("versionLabel")
    return f'<p class="pdf-version">PDF version: {escape(version)}.</p>' if version else ""

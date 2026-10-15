"""Build the static academic site. Run with Python 3; no third-party dependencies."""
from pathlib import Path
from html import escape
import json
from publication_map import render_publication_map, render_publication_map_svg
from highlights import render_highlights
from project_groups import render_projects

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "data/profile.json").read_text())
PUBS = json.loads((ROOT / "data/publications.json").read_text()) if (ROOT / "data/publications.json").exists() else []
TAXONOMY = json.loads((ROOT / "data/publication-map.json").read_text())
HIGHLIGHTS = [entry for path in sorted((ROOT / "data").glob("highlights-*.json")) for entry in json.loads(path.read_text())]
PROJECT_DATA = json.loads((ROOT / "data/projects.json").read_text())
PROJECT_BY_PAPER = {identifier: project for project in PROJECT_DATA["projects"] for identifier in project["publicationIds"]}
BASE = PROFILE["base_url"].rstrip("/")
CV = "/files/Zhaohui_Li_CV.pdf"
E = escape
NAV = [("/", "About"), ("/projects/", "Projects"), ("/research/", "Research"), ("/publications/", "Publications"), ("/experience/", "Experience"), ("/teaching/", "Teaching & service"), ("/cv/", "CV & contact")]
AI_LEADERSHIP = [
    ("National AI Institute for Exceptional Education (AI4ExceptionalEd)", "https://www.buffalo.edu/ai4exceptionaled.html"),
    ("Center for Early Literacy and Responsible AI (CELaRAI)", "https://earlyliteracyai.org/"),
]

def leadership_list():
    return '<ul class="resource-list leadership-list">' + ''.join(f'<li>AI Team Lead at the <a href="{E(url)}">{E(name)}</a>.</li>' for name, url in AI_LEADERSHIP) + '</ul>'

def write(path, value):
    dest = ROOT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(value, encoding="utf-8")

def layout(title, description, body, route="/"):
    nav = "".join(f'<a href="{url}"{chr(32)+"aria-current="+chr(34)+"page"+chr(34) if route == url else ""}>{label}</a>' for url, label in NAV)
    person = {"@context": "https://schema.org", "@type": "Person", "name": "Zhaohui Li", "url": BASE,
              "jobTitle": PROFILE["role"], "affiliation": {"@type":"CollegeOrUniversity","name":PROFILE["institution"]},
              "sameAs":[PROFILE["scholar_url"],"https://github.com/nkzhlee"]}
    map_assets = '<link rel="stylesheet" href="/css/publication-map.css"><script src="/js/publication-map.js" defer></script>' if route == "/publications/" else ""
    project_assets = '<link rel="stylesheet" href="/css/projects.css">' if route == "/projects/" else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{E(description)}">
<meta name="theme-color" content="#ffffff">
<meta property="og:type" content="website">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}">
<meta property="og:image" content="{BASE}/files/zhaohui-2026.jpg">
<meta property="og:url" content="{BASE}{route}">
<meta name="twitter:card" content="summary">
<title>{E(title)}</title>
<link rel="canonical" href="{BASE}{route}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/css/academic.css">
<script src="/js/academic.js" defer></script>
<script src="/js/highlights.js" defer></script>
{map_assets}
{project_assets}
<script type="application/ld+json">{json.dumps(person, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap header-inner">
<a class="wordmark" href="/" aria-label="Zhaohui Li, home">Zhaohui Li</a>
<nav aria-label="Primary navigation">{nav}</nav>
</div></header>
<main id="main">{body}</main>
<footer><div class="wrap footer-bottom"><span>© 2026 Zhaohui Li · Updated {E(PROFILE["updated"])}</span><div class="footer-links"><a href="mailto:nkzhaohuilee@gmail.com">Email</a><a href="{E(PROFILE['scholar_url'])}">Google Scholar</a><a href="https://github.com/nkzhlee">GitHub</a><a href="{CV}">CV (PDF)</a></div></div></footer>
</body></html>"""

def intro(kicker, title, text):
    return f'<header class="page-intro wrap"><h1>{title}</h1><p class="page-lead">{text}</p></header>'

def pub_links(p):
    links = "".join(f'<a href="{E(x["url"])}">{E(x["label"])} <span aria-hidden="true">↗</span></a>' for x in p.get("links",[]))
    project = PROJECT_BY_PAPER.get(p["id"])
    if project:
        links += f'<a href="/projects/#{E(project["id"], quote=True)}">Project</a>'
    return f'<div class="publication-links">{links}</div>' if links else ""

def pub_card(p, compact=False):
    url = p.get("links", [{}])[0].get("url") if p.get("links") else None
    title = f'<a href="{E(url)}">{E(p["title"])}</a>' if url else E(p["title"])
    authors = E(p["authors"])
    for name in ["Zhaohui Li", "Li, Z."]:
        authors = authors.replace(name, f"<strong>{name}</strong>")
    status = p.get("status","")
    author_note = f'<p class="authors">{E(p["authorNote"])}</p>' if p.get("authorNote") else ""
    status_badge = f'<span class="status">{E(status)}</span>' if status and status.lower() not in ("published", "verified", "released", p["type"].lower()) else ""
    classification = next((entry for entry in TAXONOMY["publications"] if entry["id"] == p["id"]), {})
    topic_labels = [topic["label"] for topic in TAXONOMY["topics"] if topic["id"] in classification.get("topicIds", [])]
    data = E(" ".join([*(str(p.get(k,"")) for k in ("title","authors","year","venue","type")), *topic_labels]), quote=True)
    return f'<article class="publication" data-publication data-search="{data}" data-type="{E(p["type"])}" data-year="{p.get("year") or ""}" id="{E(p["id"])}"><div class="publication-meta"><span>{p.get("year") or "Undated"}</span><span>{E(p["type"])}</span>{status_badge}</div><div class="publication-body"><h3>{title}</h3><p class="authors">{authors}</p>{author_note}<p class="venue">{E(p["venue"])}</p>{pub_links(p)}</div></article>'

def home():
    body = f'''<section class="profile wrap">
<figure class="profile-photo"><img src="/files/zhaohui-2026.jpg" alt="Zhaohui Li" width="1280" height="960" fetchpriority="high"></figure>
<div class="profile-copy"><h1>Zhaohui Li <span class="name-degree">Ph.D.</span></h1>
<p class="appointment">{E(PROFILE["role"])}<br>{E(PROFILE["college"])}<br><a href="{E(PROFILE["institution_url"])}">{E(PROFILE["institution"])}</a><br><span class="mentor">Mentor: <a href="{E(PROFILE["mentor_url"])}">Dr. {E(PROFILE["mentor"])}</a></span></p>
<p>I develop AI, particularly multimodal large language models, to support teaching, learning, and human connection. My work translates educational goals into computational tasks and builds algorithms, datasets, and systems for assessment and feedback, instructional material evaluation, storybook generation, and student behavior analysis. Through interdisciplinary collaboration, I aim to automate parts of task formulation and evaluation design and study risks such as emotional overreliance on AI and reduced independent reasoning. My goal is reliable, responsible AI that supports equitable, high-quality education.</p>
<div class="profile-links"><a href="{E(PROFILE['scholar_url'])}">Google Scholar</a><a href="mailto:nkzhaohuilee@gmail.com">Email</a><a href="{CV}">CV (PDF)</a><a href="https://github.com/nkzhlee">GitHub</a></div></div></section>
<section class="wrap section home-notes" id="research-experience"><h2>Research Experience</h2>
<p class="research-background">I received my Ph.D. in Computer Science from The Pennsylvania State University in 2024, advised by <a href="https://scholar.google.com/citations?hl=en&amp;user=jb9VOp0AAAAJ">Dr. Rebecca J. Passonneau</a> in the <a href="https://www.nlplab.psu.edu/">Natural Language Processing Lab</a>. My dissertation on automated assessment of STEM reasoning received the Best Doctoral Dissertation Award. Before joining UT San Antonio, I was a postdoctoral associate at the University at Buffalo’s Institute for Artificial Intelligence and Data Science (IAD), mentored by <a href="{E(PROFILE['mentor_url'])}">Dr. Jinjun Xiong</a>.</p>
<p>I continue to work with the following centers at the University at Buffalo:</p>{leadership_list()}<ul>
<li>Co-PI on a $50,000 <a href="https://researchautism.org/research-item/study-of-parents-ai-coach-for-parent-implemented-communication-interventions-for-children-with-asd/">Organization for Autism Research grant</a> for AI-supported parent coaching (2026–2027).</li>
<li>Program committee member for AIED 2025, AIED 2026, and LAK 2027.</li>
<li><a href="/publications/#aire-aera-2026">AIRE poster at AERA 2026</a>: personalized decodable texts for early literacy.</li>
</ul></section>
<section class="wrap section"><div class="section-title"><h2>Recent papers</h2><a href="/research/">All {len(HIGHLIGHTS)} paper highlights →</a></div>
{render_highlights(PUBS, HIGHLIGHTS, limit=6)}
<p class="section-end"><a href="/projects/">Projects by research area</a> · <a href="/research/">More paper highlights</a> · <a href="/publications/">Full publication list</a> · <a href="/publications/#publication-map">Fields &amp; venues</a></p></section>'''
    write("index.html", layout("Zhaohui Li | AI for Education & Natural Language Processing", "Academic website of Zhaohui Li: research, publications, teaching, service, and CV in AI for education and natural language processing.", body))


def research():
    body = intro("Research", "Paper highlights", "Figures and short summaries from my papers, ordered by year. Select a figure to see its source.")
    body += '<div class="wrap jump-links" aria-label="Research sections"><a href="#paper-highlights">Papers</a><a href="#leadership">Research leadership</a><a href="#ongoing">Research areas &amp; projects</a><a href="#future">Future directions</a><a href="#resources">Datasets &amp; software</a><a href="/publications/#publication-map">Fields &amp; venues</a></div>'
    body += f'<section class="wrap section" id="paper-highlights" aria-label="Paper highlights">{render_highlights(PUBS, HIGHLIGHTS)}<p class="section-end">The <a href="/publications/">full publication list</a> also includes posters and dataset records.</p></section>'
    body += f'<section class="wrap section research-section" id="leadership"><h2>Research leadership</h2><p>I continue to work with <a href="{E(PROFILE["mentor_url"])}">Dr. Jinjun Xiong</a> and serve as AI Team Lead at the following University at Buffalo centers:</p>{leadership_list()}</section>'
    body += '<section class="wrap section research-section" id="ongoing"><h2>Projects by research area</h2><p>Explore related papers, datasets, and systems grouped by their shared research questions.</p><ul class="resource-list"><li id="assessment"><a href="/projects/#pedagogical-alignment">Pedagogical alignment &amp; assessment</a></li><li id="interaction"><a href="/projects/#human-ai-collaboration">Human–AI collaboration</a></li><li id="literacy"><a href="/projects/#personalized-learning">Personalized learning &amp; special education</a></li><li><a href="/projects/#earlier-nlp">Earlier NLP &amp; machine learning</a></li></ul></section>'
    body += '''
<section class="wrap section research-section prose" id="future"><h2>Future directions</h2><p>I plan to develop a theoretical framework for translating educational goals into computational tasks, informed by interdisciplinary collaboration, and an agent-based system to support task formulation and evaluation design. I also plan to investigate responsible AI use in education, including potential risks of emotional overreliance and declines in students’ independent reasoning.</p></section>
<section class="wrap section" id="resources"><h2>Datasets &amp; software</h2><ul class="resource-list">
<li><a href="https://doi.org/10.26208/JFMP-V777">I-STUDIO</a> — Short student answers to statistics questions, with assessment labels (2023).</li>
<li><a href="https://doi.org/10.26208/BWE2-BR31">Physics lab report assessment</a> — Rubric-based assessment data for machine learning (2022).</li>
<li><a href="/publications/#scieval-2026">SciEval</a> — A benchmark for evaluating K–12 science instructional materials (2026).</li>
<li><a href="/publications/#asd-hi-2025">ASD-HI</a> — Parent–child interaction data for automated assessment of home interventions (2025).</li>
<li><a href="https://github.com/ICT-BDA/EasyML">EasyML</a> — A dataflow-based system for machine-learning workflows.</li>
</ul></section>'''
    write("research/index.html", layout("Paper Highlights | Zhaohui Li", "Figures and project summaries for 20 papers in AI, natural language processing, educational assessment, and early literacy, ordered by year.", body, "/research/"))

def projects():
    body = intro("Projects", "Research projects", "My research connects pedagogical alignment, human–AI collaboration, and personalized learning. Related papers, datasets, and systems are grouped around a shared research question.")
    body += render_projects(PROJECT_DATA, PUBS, HIGHLIGHTS)
    body += '''<section class="wrap section project-future" id="future-projects"><h2>Future directions</h2><p>Building on these projects, I plan to pursue three connected directions:</p><ul>
<li><strong>Educational goals to AI tasks:</strong> LLM agents that propose rubrics and evaluation specifications for educator review.</li>
<li><strong>AI that strengthens human connection:</strong> Agents that invite teacher, peer, and family participation while supporting independent thinking.</li>
<li><strong>Personalized special-education support:</strong> Materials and coaching aligned with educator-approved Individualized Education Program (IEP) goals, with specialist review.</li>
</ul><p class="section-end"><a href="/research/">Paper highlights by year</a> · <a href="/publications/">Full publication list</a></p></section>'''
    write("projects/index.html", layout("Research Projects | Zhaohui Li", "Research projects in pedagogical alignment, human–AI collaboration, personalized learning, special education, and earlier NLP, with related papers and datasets.", body, "/projects/"))

def publications():
    visible=[p for p in PUBS if p.get("status","")!="Status to confirm"]
    types=sorted(set(p["type"] for p in visible))
    years=sorted(set(p["year"] for p in visible if p.get("year")),reverse=True)
    controls=f'''<div class="publication-tools"><div class="search-field"><label for="publication-search">Search publications</label><input type="search" id="publication-search" placeholder="Title, author, venue, or keyword" autocomplete="off"></div><div><label for="publication-type">Type</label><select id="publication-type"><option value="">All types</option>{"".join(f'<option>{E(t)}</option>' for t in types)}</select></div><div><label for="publication-year">Year</label><select id="publication-year"><option value="">All years</option>{"".join(f'<option>{y}</option>' for y in years)}</select></div></div><div class="result-toolbar"><p id="publication-count" role="status" aria-live="polite">{len(visible)} publications and research resources</p><button id="reset-filters" type="button">Reset filters</button></div>'''
    body=intro("Publications","Papers, datasets & preprints","Research in natural language processing, educational assessment, early literacy, and multimodal learning.")
    body+='<div class="wrap jump-links" aria-label="Publication sections"><a href="#publication-map">Communities & shared topics</a><a href="#publication-list">Full publication list</a><a href="/files/publication-map.svg" download>Download figure (SVG)</a></div>'
    body+=render_publication_map(visible, TAXONOMY)
    write("files/publication-map.svg", render_publication_map_svg(visible, TAXONOMY))
    body+=f'<section class="wrap section publications-section" id="publication-list" aria-labelledby="publication-list-heading"><h2 id="publication-list-heading">Full publication list</h2>{controls}<noscript><p>All publications are shown below. Search and filters require JavaScript.</p></noscript><div class="publication-list">{"".join(pub_card(p) for p in visible)}</div><p id="no-results" hidden>No publications match these filters. Try another term or reset the filters.</p></section>'
    write("publications/index.html",layout("Publications | Zhaohui Li","Publications by Zhaohui Li, with searchable titles, years, publication types, and links to papers and datasets.",body,"/publications/"))

def timeline_row(date,title,org,detail="",extra=""):
    return f'<article class="timeline-row"><p class="timeline-date">{date}</p><div><h3>{title}</h3><p class="organization">{org}</p>{f"<p>{detail}</p>" if detail else ""}{extra}</div></article>'

def experience():
    mentor = f'Mentor: <a href="{E(PROFILE["mentor_url"])}">Dr. {E(PROFILE["mentor"])}</a>.'
    appointments = timeline_row("Sep 2026–Present","Postdoctoral Associate",f'College of AI, Cyber and Computing · <a href="{E(PROFILE["institution_url"])}">UT San Antonio</a><br>San Antonio, TX',mentor)
    appointments += timeline_row("Aug 2024–Aug 2026","Postdoctoral Associate",'Institute for Artificial Intelligence and Data Science (IAD) · <a href="https://www.buffalo.edu/">University at Buffalo</a><br>Buffalo, NY',mentor,'<p>I continue to work with these centers as AI Team Lead:</p>' + leadership_list())
    body=intro("Academic background","Experience","Academic appointments, education, research support, and selected recognition.")
    body+=f'<div class="wrap experience-layout"><nav class="section-nav" aria-label="On this page"><a href="#appointments">Appointments</a><a href="#education">Education</a><a href="#funding">Research support</a><a href="#recognition">Recognition</a></nav><div>'
    body+=f'<section class="section" id="appointments"><h2>Appointments</h2><div class="timeline">{appointments}</div></section>'
    education=timeline_row("Aug 2019–May 2024","Ph.D. in Computer Science",'The Pennsylvania State University · <a href="https://www.nlplab.psu.edu/">Natural Language Processing Lab</a><br>State College, PA','Advisor: <a href="https://scholar.google.com/citations?hl=en&amp;user=jb9VOp0AAAAJ">Dr. Rebecca J. Passonneau</a>.<br>Dissertation: <em>Automated and Semi-Automated Assessment of STEM Reasoning Questions</em> (<strong>Best Doctoral Dissertation Award</strong>).')
    education+=timeline_row("Aug 2012–Jun 2016","B.S. in Computer Science and Engineering","Nankai University<br>Tianjin, China",'Advisors: <a href="https://scholar.google.com/citations?hl=en&amp;user=su14mcEAAAAJ">Dr. Jun Xu</a> and <a href="https://scholar.google.com/citations?user=oab9IRYAAAAJ&amp;hl=en">Dr. Jie Liu</a>.<br>Thesis: <em>BDA: Big Data Analysis as a Service</em> (<a href="https://github.com/ICT-BDA/EasyML">2k+ GitHub stars</a>).')
    body+=f'<section class="section" id="education"><h2>Education</h2><div class="timeline">{education}</div></section>'
    body+='''<section class="section" id="funding"><h2>Research support</h2><p class="section-intro">Projects I have contributed to, with my role stated for each. The dates below describe the funded projects.</p><div class="funding-list">
<article><span class="small-label">Feb 2026–Dec 2027 · Co-principal investigator</span><h3><a href="https://researchautism.org/research-item/study-of-parents-ai-coach-for-parent-implemented-communication-interventions-for-children-with-asd/">AI-supported parent coaching</a></h3><p>Organization for Autism Research · $50,000</p><p>Study of Parent’s AI Coach for Parent-Implemented Communication Interventions for Children with ASD.</p></article>
<article><span class="small-label">Jan 2023–Dec 2027 · Technical lead</span><h3>National AI Institute for Exceptional Education</h3><p>National Science Foundation · Award 2229873 · $20 million total institute award</p><p>Supporting Jinjun Xiong (Co-PI) in developing AI for challenges in special education.</p></article>
<article><span class="small-label">Sep 2024–Aug 2029 · Technical lead</span><h3>Center for Early Literacy and Responsible AI</h3><p>Institute of Education Sciences · Award R305C240046 · $10 million total center award</p><p>Supporting Jinjun Xiong (Co-PI) in developing responsible AI tools for early literacy and diverse learners.</p></article>
<article><span class="small-label">Mar 2023–Feb 2025 · Research contributor</span><h3>Project CLASSIFIES</h3><p>National Science Foundation · IUSE Award 2236150 · $300,000 total project award</p><p>NLP algorithm development and technical proposal contributions with Rebecca J. Passonneau (Co-PI).</p></article>
<article><span class="small-label">2023–2024 · Principal investigator</span><h3>Interactive e-books for children</h3><p>Nittany AI Challenge · Penn State · $5,000</p></article>
</div><div class="proposal-note"><p class="small-label">Proposal in submission · Since July 2025</p><h3>AI-automated behavioral support plans</h3><p>Co-PI on a Spencer Foundation Large Research Grant on Education proposal for young children with autism spectrum disorder. Program funding range: $125,000–$500,000. This proposal is not listed as an awarded grant.</p></div></section>
<section class="section" id="recognition"><h2>Selected recognition</h2><div class="timeline">
<article class="timeline-row"><p class="timeline-date">2024</p><div><h3>Best Doctoral Dissertation in an AI-Related Discipline Award</h3><p><a href="https://ai.psu.edu/news/ai-related-dissertation-contest-finalist-winner-reflect-on-process">Pennsylvania State University ↗</a></p></div></article>
<article class="timeline-row"><p class="timeline-date">2018</p><div><h3>Best Paper Nominee</h3><p>China Conference on Information Retrieval</p></div></article>
<article class="timeline-row"><p class="timeline-date">2016</p><div><h3>Best Demo Paper Nominee</h3><p>ACM International Conference on Information and Knowledge Management</p></div></article>
<article class="timeline-row"><p class="timeline-date">2014–2015</p><div><h3>Nankai University Fellowship</h3><p>Nankai University</p></div></article>
</div></section></div></div>'''
    write("experience/index.html",layout("Experience | Zhaohui Li","Academic appointments, education, research funding contributions, and awards.",body,"/experience/"))

def teaching():
    body=intro("Academic activity","Teaching & service","Teaching experience in computer science, invited speaking, and service to AI, NLP, and education research.")
    body+='<div class="wrap teaching-grid"><section class="section"><p class="eyebrow">Teaching</p><h2>Courses & invited speaking</h2><div class="timeline">'
    body+=timeline_row("Spring 2020","Natural Language Processing","Penn State · CSE 597 · Graduate","Teaching assistant. Supported student projects, teaching, and grading.")
    body+=timeline_row("Fall 2019","Artificial Intelligence","Penn State · CMPSC 442 · Undergraduate","Teaching assistant. Teaching, grading, and examinations for a course with more than 100 students.")
    body+=timeline_row("February 2022","NSF Argumentation Workshop","PACE Lab · Illinois State University","Invited speaker on AI-assisted assessment.")
    body+=f'</div></section><section class="section"><h2>Research leadership</h2><p class="section-intro">Current roles with University at Buffalo centers</p>{leadership_list()}<h2 class="service-heading">Professional service</h2><div class="service-list">'
    body+='''
<article><h3>Session chair</h3><p>AIED 2025 and 2026</p><p>Language learning and story generation; AI agents for education.</p></article>
<article><h3>Program committee</h3><p>AIED 2025, AIED 2026, and LAK 2027</p></article>
<article><h3>Peer review</h3><p>ACL Rolling Review (ACL, EMNLP, NAACL), AAAI, AIED, and SIGIR</p></article>
<article><h3>Grant review</h3><p>NSF panel service in the Division of Research on Learning.</p></article>
<article><h3>Student volunteer</h3><p>AAAI 2019</p></article>
</div></section></div>'''
    write("teaching/index.html",layout("Teaching & Service | Zhaohui Li","Teaching in artificial intelligence and NLP, invited speaking, reviewing, and conference service.",body,"/teaching/"))

def contact():
    body=intro("CV & contact","Academic CV and contact","My CV contains a detailed record of appointments, education, publications, research projects, teaching, and service.")
    body=f'''{body}<section class="wrap section contact-layout"><div class="cv-panel"><p class="eyebrow">Curriculum vitae</p><h2>Zhaohui Li, Ph.D.</h2><p>Academic CV · Updated {E(PROFILE["cv_updated"])}</p><a class="button" href="{CV}">Open CV <span class="file-label">PDF</span></a><a class="download-link" href="{CV}" download="Zhaohui_Li_CV.pdf">Download a copy ↓</a></div><div class="contact-details"><h2>Contact</h2><dl><dt>Email</dt><dd><a href="mailto:nkzhaohuilee@gmail.com">nkzhaohuilee@gmail.com</a></dd><dt>Current appointment</dt><dd>{E(PROFILE["role"])}<br>{E(PROFILE["college"])}<br>{E(PROFILE["institution"])}</dd><dt>Mentor</dt><dd><a href="{E(PROFILE["mentor_url"])}">Dr. {E(PROFILE["mentor"])}</a></dd><dt>Research profiles</dt><dd><a href="{E(PROFILE['scholar_url'])}">Google Scholar</a><br><a href="https://github.com/nkzhlee">GitHub: nkzhlee ↗</a></dd></dl><p>For collaboration inquiries, please include your research question and a link to relevant work.</p></div></section>'''
    write("cv/index.html",layout("CV & Contact | Zhaohui Li","Download Zhaohui Li's academic CV and find contact details and research profiles.",body,"/cv/"))

def legacy():
    mapping={"about/":"/","archives/":"/publications/","categories/":"/research/","tags/":"/research/","c/":"/"}
    for dirname,dest in mapping.items():
        paths=list((ROOT/dirname).rglob("*.html")) if (ROOT/dirname).exists() else [ROOT/dirname/"index.html"]
        for path in paths:
            rel=path.relative_to(ROOT)
            write(rel,f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0; url={dest}"><meta name="robots" content="noindex"><title>Page moved | Zhaohui Li</title></head><body><p>This page has moved. <a href="{dest}">Continue to the updated site</a>.</p></body></html>')
    body=intro("Reading archive","A note on asking questions","A reading recommendation saved in 2019.")
    body+='<section class="wrap section prose"><p><em>The Only Stupid Question Is the One You Don’t Ask</em> is an article from Bridging the Gap about asking for clarification when something is unclear.</p><p><a href="https://www.bridging-the-gap.com/the-only-stupid-question-is-the-one-you-dont-ask/">Read the original article at Bridging the Gap ↗</a></p><p><a href="/">Return to my academic profile →</a></p></section>'
    write("blog/index.html",layout("Reading Archive | Zhaohui Li","A reading recommendation from the archive, with a link to the original source.",body,"/blog/"))
    write("2019/01/03/ask-question/index.html",layout("Reading Note: Asking Questions | Zhaohui Li","A reading recommendation credited to Bridging the Gap.",body,"/2019/01/03/ask-question/"))

def metadata():
    routes=[u for u,_ in NAV]
    write("sitemap.xml",'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{BASE}{u}</loc><lastmod>{PROFILE["updated_date"]}</lastmod></url>' for u in routes)+'</urlset>\n')
    write("robots.txt",f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    body=intro("404","This page isn’t here.","The link may point to an older page. You can find my current work through the links below.")
    body+='<section class="wrap section"><div class="profile-links"><a class="button" href="/">Academic profile</a><a href="/publications/">Publications</a><a href="/research/">Research</a></div></section>'
    write("404.html",layout("Page Not Found | Zhaohui Li","Find the updated academic profile, research, and publications of Zhaohui Li.",body,"/404.html"))
    write(".nojekyll","")

if __name__=="__main__":
    home(); research(); projects(); publications(); experience(); teaching(); contact(); legacy(); metadata()
    print(f"Built academic site with {len(PUBS)} publication records.")

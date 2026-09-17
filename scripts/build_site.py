"""Build the static academic site. Run with Python 3; no third-party dependencies."""
from pathlib import Path
from html import escape
import json

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "data/profile.json").read_text())
PUBS = json.loads((ROOT / "data/publications.json").read_text()) if (ROOT / "data/publications.json").exists() else []
BASE = PROFILE["base_url"].rstrip("/")
CV = "/files/Zhaohui_Li_CV.pdf"
E = escape
NAV = [("/", "About"), ("/research/", "Research"), ("/publications/", "Publications"), ("/experience/", "Experience"), ("/teaching/", "Teaching & service"), ("/cv/", "CV & contact")]

def write(path, value):
    dest = ROOT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(value, encoding="utf-8")

def layout(title, description, body, route="/"):
    nav = "".join(f'<a href="{url}"{chr(32)+"aria-current="+chr(34)+"page"+chr(34) if route == url else ""}>{label}</a>' for url, label in NAV)
    person = {"@context": "https://schema.org", "@type": "Person", "name": "Zhaohui Li", "url": BASE,
              "jobTitle": PROFILE["role"], "affiliation": {"@type":"CollegeOrUniversity","name":PROFILE["institution"]},
              "sameAs":["https://orcid.org/0009-0002-0537-3546","https://github.com/nkzhlee"]}
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{E(description)}">
<meta name="theme-color" content="#143f3e">
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
<script type="application/ld+json">{json.dumps(person, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap header-inner">
<a class="wordmark" href="/" aria-label="Zhaohui Li, home">Zhaohui Li<span>AI · Language · Education</span></a>
<nav aria-label="Primary navigation">{nav}</nav>
</div></header>
<main id="main">{body}</main>
<footer><div class="wrap footer-grid"><div><a class="footer-name" href="/">Zhaohui Li</a><p>Natural language processing &amp; AI for education</p></div><div class="footer-links"><a href="mailto:nkzhaohuilee@gmail.com">Email</a><a href="https://orcid.org/0009-0002-0537-3546">ORCID</a><a href="https://github.com/nkzhlee">GitHub</a><a href="{CV}">CV <span class="file-label">PDF</span></a></div></div><div class="wrap footer-bottom"><span>© 2026 Zhaohui Li</span><span>Updated September 2026</span></div></footer>
</body></html>"""

def intro(kicker, title, text):
    return f'<header class="page-intro wrap"><p class="eyebrow">{kicker}</p><h1>{title}</h1><p class="page-lead">{text}</p></header>'

def pub_links(p):
    links = "".join(f'<a href="{E(x["url"])}">{E(x["label"])} <span aria-hidden="true">↗</span></a>' for x in p.get("links",[]))
    return f'<div class="publication-links">{links}</div>' if links else ""

def pub_card(p, compact=False):
    url = p.get("links", [{}])[0].get("url") if p.get("links") else None
    title = f'<a href="{E(url)}">{E(p["title"])}</a>' if url else E(p["title"])
    authors = E(p["authors"])
    for name in ["Zhaohui Li", "Li, Z."]:
        authors = authors.replace(name, f"<strong>{name}</strong>")
    status = p.get("status","")
    status_badge = f'<span class="status">{E(status)}</span>' if status and status.lower() not in ("published", "verified", "released", p["type"].lower()) else ""
    data = E(" ".join(str(p.get(k,"")) for k in ("title","authors","year","venue","type")), quote=True)
    return f'<article class="publication" data-publication data-search="{data}" data-type="{E(p["type"])}" data-year="{p.get("year") or ""}" id="{E(p["id"])}"><div class="publication-meta"><span>{p.get("year") or "Undated"}</span><span>{E(p["type"])}</span>{status_badge}</div><div class="publication-body"><h3>{title}</h3><p class="authors">{authors}</p><p class="venue">{E(p["venue"])}</p>{pub_links(p)}</div></article>'

def home():
    selected = []
    for phrase in ("PaiCoach", "SciEval", "StoryLab"):
        match = next((p for p in PUBS if phrase.lower() in p["title"].lower()), None)
        if match: selected.append(pub_card(match, True))
    body = f'''<section class="profile wrap">
<div class="profile-copy"><p class="eyebrow">Natural language processing · AI for education</p><h1>Zhaohui Li <span class="name-degree">Ph.D.</span></h1><p class="appointment">{E(PROFILE["role"])}<br><a href="{E(PROFILE["institution_url"])}">{E(PROFILE["institution"])}</a></p>
<p class="bio-lead">I study how language and multimodal models can support educational assessment, early literacy, and parent-child communication.</p>
<p>My research connects model development with datasets and evaluation designed with educators. I work on short-answer assessment, AI-assisted reading, and the analysis of parent-child interactions.</p>
<div class="profile-links"><a class="button" href="{CV}">Curriculum vitae <span class="file-label">PDF</span></a><a href="mailto:nkzhaohuilee@gmail.com">Email</a><a href="https://orcid.org/0009-0002-0537-3546">ORCID ↗</a><a href="https://github.com/nkzhlee">GitHub ↗</a></div></div>
<figure class="profile-photo"><img src="/files/zhaohui-2026.jpg" alt="Zhaohui Li" width="1280" height="960" fetchpriority="high"><figcaption>Computer science · Learning sciences</figcaption></figure></section>
<section class="research-overview section-tint"><div class="wrap"><div class="section-title"><div><p class="eyebrow">Research</p><h2>Assessment, literacy, and interaction</h2></div><a class="link-arrow" href="/research/">Research projects <span aria-hidden="true">→</span></a></div><div class="theme-grid">
<article><span class="index">01</span><h3>Assessment &amp; feedback</h3><p>How can AI assess student reasoning, explain its judgments, and identify when human review is needed?</p><a href="/research/#assessment">Models, rubrics, and evaluation →</a></article>
<article><span class="index">02</span><h3>Reading &amp; language</h3><p>How can language models help educators create and evaluate reading materials for young learners?</p><a href="/research/#literacy">Story generation and early literacy →</a></article>
<article><span class="index">03</span><h3>Multimodal learning</h3><p>What can language, speech, and interaction data tell us about how children and families learn together?</p><a href="/research/#interaction">Parent-child and child-robot interaction →</a></article></div></div></section>
<section class="wrap section"><div class="section-title"><div><p class="eyebrow">Selected publications</p><h2>Recent work</h2></div><a class="link-arrow" href="/publications/">All publications →</a></div><div class="publication-list">{"".join(selected)}</div></section>
<section class="wrap section background-grid"><div><p class="eyebrow">Background</p><h2>From NLP to educational AI</h2><p>I received my Ph.D. in Computer Science from Penn State in 2024, advised by Rebecca J. Passonneau. My doctoral research focused on automated and semi-automated assessment of STEM reasoning.</p><p>At the University at Buffalo, I worked on AI for exceptional education and early literacy. I previously worked on machine reading comprehension and the open-source EasyML system.</p><a class="link-arrow" href="/experience/">Appointments, education, and funding →</a></div><aside class="academic-note"><p class="eyebrow">Academic activity</p><h3>Research, teaching, and service</h3><ul class="plain-list"><li>Teaching experience in artificial intelligence and natural language processing</li><li>Program committee and session chair service at AIED</li><li>Peer review for NLP, AI, and education venues</li></ul><a href="/teaching/">Teaching &amp; service →</a></aside></section>
<section class="contact-band"><div class="wrap"><div><p class="eyebrow">Contact</p><h2>Research inquiries</h2><p>For research questions or collaboration, email me with a brief description of your work.</p></div><a class="contact-email" href="mailto:nkzhaohuilee@gmail.com">nkzhaohuilee@gmail.com <span aria-hidden="true">↗</span></a></div></section>'''
    write("index.html", layout("Zhaohui Li | AI for Education & Natural Language Processing", "Academic website of Zhaohui Li: research, publications, teaching, service, and CV in AI for education and natural language processing.", body))

PROJECTS = [
("assessment","01","Assessment & feedback","Making educational judgments useful and reviewable","I develop models and datasets for assessing short answers, STEM reasoning, and instructional materials. This work studies both prediction quality and the information a teacher needs to interpret or review an assessment.",[
("Short-answer assessment","Models that compare student answers with questions and rubrics, then group similar answers to support instructor feedback.","A semantic feature-wise transformation","2021 · 2023"),
("Human review and selective prediction","Methods that identify when an automated grading system should defer to a person.","Learning when to defer","2023 · 2024"),
("SciEval","A benchmark of 273 K–12 science lessons, assessed against 13 criteria from the EQuIP rubric.","SciEval","2026")]),
("literacy","02","Reading & language","Tools for creating and studying reading experiences","I work with literacy researchers on story generation, dialogic reading, and evaluation of instructional materials. The focus is on how these tools fit the work of educators and the needs of beginning readers.",[
("StoryLab","A system for teachers to guide the generation of illustrated stories for young learners.","StoryLab","2025"),
("AI Reading Enhancer","Ongoing work on generating decodable books and evaluating them with literacy experts.",None,"Ongoing"),
("Dialogic reading","Studies of bilingual English learning and comparisons between reading with a parent and a conversational agent.","bilingual conversational agent","2025")]),
("interaction","03","Multimodal learning","Understanding learning through interaction","I study the language and behavior in parent-child and child-robot interactions, combining multimodal data with questions from education and developmental research.",[
("ASD-HI and PaiCoach","Analysis of parent-child interactions during shared book reading, with expert review of AI-supported coaching feedback.","PaiCoach","2025 · 2026"),
("Embodied reading companions","Feasibility research on an LLM-powered humanoid robot as a reading companion for children's AI literacy.","Humanoid Robot","2026"),
("LLM4Art","Collaborative research on how language models interpret artworks.","LLM4Art","2026"),
("Dyslexia simulation","Ongoing work on interactive simulations for educator training and disability awareness.",None,"Ongoing")])
]

def research():
    body=intro("Research","AI in educational practice","My work brings together natural language processing, multimodal models, and educational assessment. These projects connect technical questions to specific teaching and learning tasks.")
    body+='<div class="wrap jump-links" aria-label="Research areas"><a href="#assessment">Assessment</a><a href="#literacy">Early literacy</a><a href="#interaction">Multimodal learning</a><a href="#resources">Datasets & software</a></div>'
    for slug,num,label,title,text,projects in PROJECTS:
        cards=[]
        for name,desc,match,date in projects:
            paper = next((p for p in PUBS if match and match.lower() in p["title"].lower()),None)
            link=f'<a href="/publications/#{paper["id"]}">Related publication →</a>' if paper else '<a href="mailto:nkzhaohuilee@gmail.com">Ask about this work →</a>'
            cards.append(f'<article class="project"><p class="small-label">{date}</p><h3>{name}</h3><p>{desc}</p>{link}</article>')
        body+=f'<section id="{slug}" class="wrap section research-section"><div class="research-heading"><span class="index">{num}</span><div><p class="eyebrow">{label}</p><h2>{title}</h2><p>{text}</p></div></div><div class="project-grid">{"".join(cards)}</div></section>'
    body+='''<section class="section-tint section" id="resources"><div class="wrap"><p class="eyebrow">Research resources</p><h2>Datasets &amp; software</h2><div class="resource-list">
<article><span class="small-label">Dataset · 2023</span><h3>I-STUDIO</h3><p>A dataset of short student answers to statistics questions, with assessment labels.</p><a href="https://doi.org/10.26208/JFMP-V777">Dataset record ↗</a></article>
<article><span class="small-label">Dataset · 2022</span><h3>Physics lab report assessment</h3><p>Data for machine learning on rubric-based assessment of physics lab reports.</p><a href="https://doi.org/10.26208/BWE2-BR31">Penn State Data Commons ↗</a></article>
<article><span class="small-label">Open-source software</span><h3>EasyML</h3><p>A dataflow-based system for applying machine learning algorithms to real-world tasks.</p><a href="https://github.com/ICT-BDA/EasyML">Repository on GitHub ↗</a></article>
</div></div></section>'''
    write("research/index.html",layout("Research | Zhaohui Li","Research in educational assessment, early literacy, parent-child interaction, and multimodal learning; datasets and open-source software.",body,"/research/"))

def publications():
    visible=[p for p in PUBS if p.get("status","")!="Status to confirm"]
    types=sorted(set(p["type"] for p in visible))
    years=sorted(set(p["year"] for p in visible if p.get("year")),reverse=True)
    controls=f'''<div class="publication-tools"><div class="search-field"><label for="publication-search">Search publications</label><input type="search" id="publication-search" placeholder="Title, author, venue, or keyword" autocomplete="off"></div><div><label for="publication-type">Type</label><select id="publication-type"><option value="">All types</option>{"".join(f'<option>{E(t)}</option>' for t in types)}</select></div><div><label for="publication-year">Year</label><select id="publication-year"><option value="">All years</option>{"".join(f'<option>{y}</option>' for y in years)}</select></div></div><div class="result-toolbar"><p id="publication-count" role="status" aria-live="polite">{len(visible)} publications and research resources</p><button id="reset-filters" type="button">Reset filters</button></div>'''
    body=intro("Publications","Papers, datasets & preprints","Research in natural language processing, educational assessment, early literacy, and multimodal learning.")
    body+=f'<section class="wrap section publications-section" aria-labelledby="publication-list-heading"><h2 class="visually-hidden" id="publication-list-heading">Publication list</h2>{controls}<noscript><p>All publications are shown below. Search and filters require JavaScript.</p></noscript><div class="publication-list">{"".join(pub_card(p) for p in visible)}</div><p id="no-results" hidden>No publications match these filters. Try another term or reset the filters.</p></section>'
    write("publications/index.html",layout("Publications | Zhaohui Li","Publications by Zhaohui Li, with searchable titles, years, publication types, and links to papers and datasets.",body,"/publications/"))

def timeline_row(date,title,org,detail=""):
    return f'<article class="timeline-row"><p class="timeline-date">{date}</p><div><h3>{title}</h3><p class="organization">{org}</p>{f"<p>{detail}</p>" if detail else ""}</div></article>'

def experience():
    appointments = timeline_row("Sep 2026–present","Postdoctoral Associate","UT San Antonio · College of AI, Cyber and Computing") if PROFILE["institution"].startswith("UT San") else ""
    appointments += timeline_row("Aug 2024–Aug 2026" if appointments else "Aug 2024–present","Postdoctoral Associate","University at Buffalo · Institute for Artificial Intelligence and Data Science","AI team lead for the National AI Institute for Exceptional Education and the Center for Early Literacy and Responsible AI; mentor: Jinjun Xiong.")
    appointments += timeline_row("2019–2024","Graduate Research Assistant","Penn State · Natural Language Processing Lab","Department of Computer Science and Engineering; advisor: Rebecca J. Passonneau.")
    appointments += timeline_row("Feb–Aug 2019","Research Intern","Baidu Research · Big Data Lab","Mentor: Jun Huan.")
    body=intro("Academic background","Experience","Academic appointments, education, research support, and selected recognition.")
    body+=f'<div class="wrap experience-layout"><nav class="section-nav" aria-label="On this page"><a href="#appointments">Appointments</a><a href="#education">Education</a><a href="#funding">Research support</a><a href="#recognition">Recognition</a></nav><div>'
    body+=f'<section class="section" id="appointments"><h2>Appointments</h2><div class="timeline">{appointments}</div></section>'
    education=timeline_row("2019–2024","Ph.D., Computer Science","Pennsylvania State University","Advisor: Rebecca J. Passonneau. Dissertation: Automated and Semi-Automated Assessment of STEM Reasoning Questions.")
    education+=timeline_row("2012–2016","B.S., Computer Science and Engineering","Nankai University")
    body+=f'<section class="section" id="education"><h2>Education</h2><div class="timeline">{education}</div></section>'
    body+='''<section class="section" id="funding"><h2>Research support</h2><p class="section-intro">Projects I have contributed to, with my role stated for each. The dates below describe the funded projects.</p><div class="funding-list">
<article><span class="small-label">2026–2027 · Co-principal investigator</span><h3>AI-supported parent coaching</h3><p>Organization for Autism Research · $50,000</p><p>Parent-implemented communication interventions for children with autism.</p></article>
<article><span class="small-label">2023–2027 · Technical leadership</span><h3>National AI Institute for Exceptional Education</h3><p>National Science Foundation · Award 2229873</p><p>AI development with Jinjun Xiong’s team at the University at Buffalo.</p></article>
<article><span class="small-label">2024–2029 · Technical leadership</span><h3>Center for Early Literacy and Responsible AI</h3><p>Institute of Education Sciences · Award R305C240046</p><p>AI tools for early literacy, developed with literacy researchers and educators.</p></article>
<article><span class="small-label">2023–2025 · Research contributor</span><h3>Project CLASSIFIES</h3><p>National Science Foundation · IUSE Award 2236150</p><p>NLP algorithm development and technical proposal contributions with Rebecca J. Passonneau.</p></article>
<article><span class="small-label">2023–2024 · Principal investigator</span><h3>Interactive e-books for children</h3><p>Nittany AI Challenge · Penn State · $5,000</p></article>
</div></section>
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
    body+='''</div></section><section class="section"><p class="eyebrow">Service</p><h2>Reviewing & community</h2><div class="service-list">
<article><h3>Session chair</h3><p>AIED 2025 and 2026</p><p>Language learning and story generation; AI agents for education.</p></article>
<article><h3>Program committee</h3><p>AIED 2025 and 2026</p></article>
<article><h3>Peer review</h3><p>ACL Rolling Review, AAAI, AIED, and SIGIR</p></article>
<article><h3>Grant review</h3><p>NSF panel service in the Division of Research on Learning.</p></article>
<article><h3>Student volunteer</h3><p>AAAI 2019</p></article>
</div></section></div>'''
    write("teaching/index.html",layout("Teaching & Service | Zhaohui Li","Teaching in artificial intelligence and NLP, invited speaking, reviewing, and conference service.",body,"/teaching/"))

def contact():
    body=intro("CV & contact","Academic CV and contact","My CV contains a detailed record of appointments, education, publications, research projects, teaching, and service.")
    body=f'''{body}<section class="wrap section contact-layout"><div class="cv-panel"><p class="eyebrow">Curriculum vitae</p><h2>Zhaohui Li, Ph.D.</h2><p>Academic CV · Updated September 2026</p><a class="button" href="{CV}">Open CV <span class="file-label">PDF</span></a><a class="download-link" href="{CV}" download="Zhaohui_Li_CV.pdf">Download a copy ↓</a></div><div class="contact-details"><h2>Contact</h2><dl><dt>Email</dt><dd><a href="mailto:nkzhaohuilee@gmail.com">nkzhaohuilee@gmail.com</a></dd><dt>Current appointment</dt><dd>{E(PROFILE["role"])}<br>{E(PROFILE["institution"])}</dd><dt>Research profiles</dt><dd><a href="https://orcid.org/0009-0002-0537-3546">ORCID: 0009-0002-0537-3546 ↗</a><br><a href="https://github.com/nkzhlee">GitHub: nkzhlee ↗</a></dd></dl><p>For collaboration inquiries, please include your research question and a link to relevant work.</p></div></section>'''
    write("cv/index.html",layout("CV & Contact | Zhaohui Li","Download Zhaohui Li's academic CV and find contact details and research profiles.",body,"/cv/"))

def legacy():
    mapping={"projects/":"/research/","about/":"/","archives/":"/publications/","categories/":"/research/","tags/":"/research/","c/":"/"}
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
    write("sitemap.xml",'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{BASE}{u}</loc><lastmod>2026-09-17</lastmod></url>' for u in routes)+'</urlset>\n')
    write("robots.txt",f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    body=intro("404","This page isn’t here.","The link may point to an older page. You can find my current work through the links below.")
    body+='<section class="wrap section"><div class="profile-links"><a class="button" href="/">Academic profile</a><a href="/publications/">Publications</a><a href="/research/">Research</a></div></section>'
    write("404.html",layout("Page Not Found | Zhaohui Li","Find the updated academic profile, research, and publications of Zhaohui Li.",body,"/404.html"))
    write(".nojekyll","")

if __name__=="__main__":
    home(); research(); publications(); experience(); teaching(); contact(); legacy(); metadata()
    print(f"Built academic site with {len(PUBS)} publication records.")

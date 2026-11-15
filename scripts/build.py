#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt
import html, json, pathlib, re, shutil
from urllib.parse import quote
import yaml
import mistune

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
PUBLIC = ROOT / "public"
STATIC = ROOT / "static"
BASE = CFG.get("base_path", "").rstrip("/")

if PUBLIC.exists():
    shutil.rmtree(PUBLIC)
PUBLIC.mkdir(parents=True)
shutil.copytree(STATIC, PUBLIC / "assets", dirs_exist_ok=True)

md = mistune.create_markdown(plugins=["table", "strikethrough", "task_lists", "url"])


def esc(x): return html.escape(str(x), quote=True)
def link(path: str) -> str:
    path = "/" + path.lstrip("/")
    return (BASE + path) if BASE else path

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "post"

def split_frontmatter(text: str):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            meta = yaml.safe_load(text[4:end]) or {}
            return meta, text[end + 5:]
    return {}, text

def first_h1(body: str):
    for line in body.splitlines():
        m = re.match(r"^#\s+(.+)$", line)
        if m: return m.group(1).strip()
    return None

def excerpt(body: str, limit=190):
    body = re.sub(r"```.*?```", " ", body, flags=re.S)
    body = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", body)
    body = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", body)
    body = re.sub(r"[#>*_`~|-]", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return body[:limit] + ("…" if len(body) > limit else "")

def date_value(v):
    if isinstance(v, (dt.date, dt.datetime)): return v.isoformat()[:10]
    if v: return str(v)
    return ""

posts = []
for folder in [ROOT / "content/posts", ROOT / "content/imported"]:
    for path in sorted(folder.glob("*.md")):
        if path.name.lower() == "readme.md" or path.name.startswith("."):
            continue
        text = path.read_text(encoding="utf-8")
        meta, body = split_frontmatter(text)
        title = str(meta.get("title") or first_h1(body) or path.stem.replace("-", " ").title())
        slug = slugify(str(meta.get("slug") or path.stem))
        tags = meta.get("tags") or []
        if isinstance(tags, str): tags = [x.strip() for x in tags.split(",") if x.strip()]
        post = {
            "title": title,
            "slug": slug,
            "tags": [str(t) for t in tags],
            "date": date_value(meta.get("date")),
            "source_url": str(meta.get("source_url") or ""),
            "description": str(meta.get("description") or excerpt(body)),
            "body": body,
            "html": md(body),
        }
        posts.append(post)

posts.sort(key=lambda p: (p["date"], p["title"].lower()), reverse=True)

STYLE = link("assets/style.css")
APP = link("assets/app.js")
HOME = link("")
ADMIN = link("admin/")


def shell(title: str, content: str, description=""):
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · {esc(CFG['title'])}</title>
<meta name="description" content="{esc(description or CFG['subtitle'])}">
<link rel="stylesheet" href="{STYLE}">
</head><body>
<header class="top"><div class="wrap nav"><a class="brand" href="{HOME}">{esc(CFG['title'])}</a><nav><a href="{HOME}">Writeups</a><a href="{ADMIN}">Import .md</a><a href="https://github.com/{esc(CFG['github_owner'])}/{esc(CFG['github_repo'])}" target="_blank">GitHub</a><button id="themeBtn" class="ghost" aria-label="Toggle theme">◐</button></nav></div></header>
<main class="wrap">{content}</main>
<footer class="wrap foot">Built from Markdown · Hosted with GitHub Pages · {esc(CFG['author'])}</footer>
<script src="{APP}"></script></body></html>'''

cards = []
all_tags = sorted({t for p in posts for t in p["tags"]}, key=str.lower)
for p in posts:
    tags = " ".join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"])
    meta_bits = [p["date"]] if p["date"] else []
    if p["source_url"]: meta_bits.append("HackMD source")
    search = esc(" ".join([p["title"], p["description"], *p["tags"]]).lower())
    cards.append(f'''<article class="card post-card" data-search="{search}" data-tags="{esc(' '.join(p['tags']).lower())}">
<a class="card-link" href="{link('posts/'+p['slug']+'/')}"><h2>{esc(p['title'])}</h2></a>
<div class="meta">{' · '.join(map(esc,meta_bits))}</div><p>{esc(p['description'])}</p><div>{tags}</div></article>''')

tag_buttons = ''.join(f'<button class="tag-filter" data-tag="{esc(t.lower())}">{esc(t)}</button>' for t in all_tags)
index_content = f'''<section class="hero"><div class="eyebrow">SECURITY NOTES / WRITEUPS</div><h1>{esc(CFG['subtitle'])}</h1><p>Markdown-first technical notes. HackMD sources can be synchronized automatically during GitHub Pages deployment.</p></section>
<section class="toolbar"><input id="search" type="search" placeholder="Search writeups, tools, tags…" aria-label="Search"><div class="filters"><button class="tag-filter active" data-tag="">All</button>{tag_buttons}</div></section>
<section id="posts" class="grid">{''.join(cards) if cards else '<div class="empty">No posts yet. Use Import .md or add Markdown files to content/posts.</div>'}</section>'''
(PUBLIC / "index.html").write_text(shell(CFG["title"], index_content), encoding="utf-8")

for p in posts:
    out = PUBLIC / "posts" / p["slug"]
    out.mkdir(parents=True, exist_ok=True)
    tags = " ".join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"])
    source = f'<a class="source" href="{esc(p["source_url"])}" target="_blank" rel="noopener">Original HackMD ↗</a>' if p["source_url"] else ""
    content = f'''<article class="post"><a class="back" href="{HOME}">← All writeups</a><header class="post-head"><h1>{esc(p['title'])}</h1><div class="meta">{esc(p['date'])} {source}</div><div>{tags}</div></header><div class="markdown">{p['html']}</div></article>'''
    (out / "index.html").write_text(shell(p["title"], content, p["description"]), encoding="utf-8")

admin_dir = PUBLIC / "admin"
admin_dir.mkdir(parents=True, exist_ok=True)
repo_upload = f"https://github.com/{CFG['github_owner']}/{CFG['github_repo']}/upload/main/content/posts"
admin_content = f'''<section class="hero small"><div class="eyebrow">MARKDOWN IMPORTER</div><h1>Prepare a .md post</h1><p>This page never asks for a GitHub token. Choose a Markdown file, add metadata, download the prepared post, then upload it to the repository.</p></section>
<section class="admin-box">
<label>Markdown file<input id="mdFile" type="file" accept=".md,text/markdown,text/plain"></label>
<div class="form-row"><label>Title<input id="postTitle" placeholder="Post title"></label><label>Tags<input id="postTags" placeholder="ctf, reverse-engineering"></label></div>
<div class="form-row"><label>Date<input id="postDate" type="date"></label><label>Slug<input id="postSlug" placeholder="my-writeup"></label></div>
<div class="actions"><button id="downloadPost">Download prepared .md</button><a class="button secondary" href="{esc(repo_upload)}" target="_blank">Open GitHub upload ↗</a></div>
<p class="note"><strong>Why this flow?</strong> GitHub Pages is static. Writing directly to a repository from frontend JavaScript would require exposing an access token or adding an authentication backend. This workflow keeps credentials out of the site.</p>
<label>Preview<textarea id="mdPreview" rows="20" spellcheck="false" placeholder="Select a .md file to preview it here"></textarea></label>
</section><script>window.BLOG_BASE={json.dumps(BASE)};</script><script src="{link('assets/admin.js')}"></script>'''
(admin_dir / "index.html").write_text(shell("Import Markdown", admin_content), encoding="utf-8")

search = [{k:p[k] for k in ["title","slug","tags","date","description"]} for p in posts]
(PUBLIC / "search.json").write_text(json.dumps(search, ensure_ascii=False, indent=2), encoding="utf-8")
(PUBLIC / ".nojekyll").write_text("", encoding="utf-8")
print(f"Built {len(posts)} post(s) into {PUBLIC}")

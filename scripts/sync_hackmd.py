#!/usr/bin/env python3
import json, pathlib, re, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = json.loads((ROOT / "data/hackmd_sources.json").read_text(encoding="utf-8"))
OUT = ROOT / "content/imported"
OUT.mkdir(parents=True, exist_ok=True)


def raw_url(url: str) -> str:
    return url if url.endswith(".md") else url + ".md"


def title_from_markdown(text: str, fallback: str) -> str:
    # Ignore front matter and find first H1.
    for line in text.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return fallback


def yaml_quote(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'

for src in SOURCES:
    url = src["url"]
    target = OUT / f'{src["slug"]}.md'
    req = urllib.request.Request(raw_url(url), headers={"User-Agent": "security-writeups-blog/1.0", "Accept": "text/markdown"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = r.read().decode("utf-8", errors="replace")
        if "<html" in data[:500].lower():
            raise RuntimeError("HackMD returned HTML instead of Markdown")
        title = title_from_markdown(data, src["fallback_title"])
        # Preserve source markdown exactly; add front matter only when absent.
        if data.lstrip().startswith("---"):
            content = data
        else:
            content = (
                "---\n"
                f"title: {yaml_quote(title)}\n"
                "tags: [writeup, hackmd]\n"
                f"source_url: {yaml_quote(url)}\n"
                "imported_from: hackmd\n"
                "---\n\n" + data
            )
        target.write_text(content, encoding="utf-8")
        print(f"Imported {url} -> {target.relative_to(ROOT)}")
    except Exception as e:
        if target.exists():
            print(f"WARNING: could not refresh {url}; using cached file: {e}")
        else:
            # Keep deployment alive and make the missing source obvious.
            target.write_text(
                "---\n"
                f"title: {yaml_quote(src['fallback_title'])}\n"
                "tags: [writeup, hackmd]\n"
                f"source_url: {yaml_quote(url)}\n"
                "sync_status: unavailable\n"
                "---\n\n"
                "> This source could not be synchronized during the build. Open the original HackMD link above.\n",
                encoding="utf-8",
            )
            print(f"WARNING: placeholder created for {url}: {e}")

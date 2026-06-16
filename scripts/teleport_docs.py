#!/usr/bin/env python3
"""teleport_docs.py — search & read the Teleport documentation (goteleport.com).

Backed by Teleport's own published, agent-friendly endpoints:
  - https://goteleport.com/docs/llms.txt  — the page index (Title/URL/description, by section)
  - https://goteleport.com/docs/<path>.md — clean markdown for any docs page (token-counted)

Three things the model does, escalating only as far as the question needs:
  search   lexical search over the cached llms.txt index   (no page bodies -> cheap)
  fetch    pull one page's clean markdown, windowed         (context-bounded)
  related  list sibling pages in the same index section     (fan out to adjacent topics)
  refresh  re-download llms.txt (the entire maintenance story)

stdlib only; network only on `fetch`/`refresh`.
"""
import argparse
import os
import re
import sys
import urllib.request
import urllib.error

DOCS_BASE = "https://goteleport.com/docs"
LLMS_URL = f"{DOCS_BASE}/llms.txt"
MANIFEST = os.path.join(os.path.dirname(__file__), "..", "references", "llms.txt")
DEFAULT_MAX_CHARS = 5000

LINK_RE = re.compile(r"^\-\s*\[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)\s*:?\s*(?P<desc>.*)$")
# words we don't want to weight in lexical scoring
STOP = {
    "the", "a", "an", "to", "of", "for", "and", "or", "in", "on", "with", "how",
    "do", "i", "is", "are", "my", "me", "can", "use", "using", "teleport", "set",
    "up", "get", "what", "when", "where", "which", "guide", "docs", "doc",
}


def _http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "teleport-docs-skill/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def load_manifest():
    """Parse llms.txt -> list of {title, url, desc, section}."""
    if not os.path.exists(MANIFEST):
        sys.exit("manifest missing; run: teleport_docs.py refresh")
    entries, section = [], ""
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("## "):
                section = line[3:].strip()
                continue
            m = LINK_RE.match(line)
            if m:
                entries.append({
                    "title": m.group("title").strip(),
                    "url": m.group("url").strip(),
                    "desc": m.group("desc").strip(),
                    "section": section,
                })
    return entries


def _terms(text: str):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def cmd_search(args):
    entries = load_manifest()
    q = _terms(args.query)
    if not q:
        sys.exit("empty query after removing stop words; be more specific")
    scored = []
    for e in entries:
        title_t = _terms(e["title"])
        desc_t = _terms(e["desc"])
        # url path slug words are strong signal (e.g. "machine-id", "tbot")
        slug_t = _terms(e["url"].replace("/", " ").replace("-", " ").replace(".md", ""))
        sec_t = _terms(e["section"])
        score = 0
        for term in set(q):
            if term in title_t:
                score += 5
            if term in slug_t:
                score += 4
            if term in desc_t:
                score += 2
            if term in sec_t:
                score += 1
            # substring fallback for partial matches (e.g. "rbac" in "rbacs")
            if score == 0 and term in e["title"].lower():
                score += 1
        if score:
            scored.append((score, e))
    scored.sort(key=lambda x: (-x[0], x[1]["title"]))
    if not scored:
        print(f"No matches for: {args.query}")
        print("Try broader terms, or `refresh` if the index is stale.")
        return
    for score, e in scored[: args.limit]:
        print(f"[{e['title']}]({e['url']})")
        if e["desc"]:
            print(f"    {e['desc']}")
        print(f"    — section: {e['section']}  (score {score})")
        print()


def _to_md_url(target: str) -> str:
    """Accept a full URL, a /docs/... path, or a bare slug; return a .md URL."""
    if target.startswith("http://") or target.startswith("https://"):
        url = target
    elif target.startswith("/docs/"):
        url = "https://goteleport.com" + target
    elif target.startswith("docs/"):
        url = "https://goteleport.com/" + target
    else:
        url = f"{DOCS_BASE}/{target.lstrip('/')}"
    if not url.endswith(".md"):
        url = url.rstrip("/") + ".md"
    return url


def _strip_token_count(md: str) -> str:
    # pages are prefixed with a {"token_count": N} line — drop it
    lines = md.splitlines()
    if lines and lines[0].lstrip().startswith('{"token_count"'):
        lines = lines[1:]
        if lines and lines[0].strip() == "":
            lines = lines[1:]
    return "\n".join(lines)


def _extract_section(md: str, heading: str) -> str:
    """Return the block from the heading matching `heading` to the next same-or-higher heading."""
    lines = md.splitlines()
    target = heading.strip().lower()
    start = None
    start_level = 0
    for i, ln in enumerate(lines):
        hm = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if hm and target in hm.group(2).strip().lower():
            start, start_level = i, len(hm.group(1))
            break
    if start is None:
        return ""
    out = [lines[start]]
    for ln in lines[start + 1:]:
        hm = re.match(r"^(#{1,6})\s+", ln)
        if hm and len(hm.group(1)) <= start_level:
            break
        out.append(ln)
    return "\n".join(out)


def cmd_fetch(args):
    url = _to_md_url(args.target)
    try:
        md = _strip_token_count(_http_get(url))
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} fetching {url}\n(check the URL via `search`; it must be a real docs page)")
    except urllib.error.URLError as e:
        sys.exit(f"network error fetching {url}: {e.reason}")

    print(f"# source: {url}\n")
    if args.section:
        block = _extract_section(md, args.section)
        if not block:
            sys.exit(f'section "{args.section}" not found; fetch without --section to see headings')
        print(block)
        return

    total = len(md)
    start = max(0, args.start)
    end = min(total, start + args.max_chars)
    sys.stdout.write(md[start:end])
    if end < total:
        print(f"\n\n--- truncated at char {end}/{total}. "
              f"continue with: --start {end} ---")


def cmd_related(args):
    entries = load_manifest()
    target = _to_md_url(args.url)
    section = None
    for e in entries:
        if e["url"] == target or e["url"].rstrip(".md") == target.rstrip(".md"):
            section = e["section"]
            break
    if section is None:
        sys.exit(f"{target} not found in index; run `search` to find the right URL")
    print(f"# pages in section: {section}\n")
    for e in entries:
        if e["section"] == section and e["url"] != target:
            print(f"[{e['title']}]({e['url']})")
            if e["desc"]:
                print(f"    {e['desc']}")


def cmd_refresh(args):
    data = _http_get(LLMS_URL)
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        f.write(data)
    n = len(LINK_RE.findall(data)) if False else sum(
        1 for ln in data.splitlines() if LINK_RE.match(ln))
    print(f"refreshed {MANIFEST}\n{n} pages indexed from {LLMS_URL}")


def main():
    p = argparse.ArgumentParser(description="Search & read the Teleport docs.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="lexical search over the cached llms.txt index")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=cmd_search)

    f = sub.add_parser("fetch", help="fetch one page's clean markdown (windowed)")
    f.add_argument("target", help="full URL, /docs/... path, or slug")
    f.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    f.add_argument("--start", type=int, default=0)
    f.add_argument("--section", help="return only this heading's block")
    f.set_defaults(func=cmd_fetch)

    r = sub.add_parser("related", help="list sibling pages in the same index section")
    r.add_argument("url")
    r.set_defaults(func=cmd_related)

    rf = sub.add_parser("refresh", help="re-download llms.txt")
    rf.set_defaults(func=cmd_refresh)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

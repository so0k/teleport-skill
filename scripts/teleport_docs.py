#!/usr/bin/env python3
"""teleport_docs.py — search & read the Teleport documentation (goteleport.com).

Backed by Teleport's own published, agent-friendly endpoints:
  - https://goteleport.com/docs/llms.txt  — the page index (Title/URL/description, by section)
  - https://goteleport.com/docs/<path>.md — clean markdown for any docs page (token-counted)

Four things the model does, escalating only as far as the question needs:
  search   TF-IDF content search over a pre-built index (references/search-index.json)
           Falls back to lexical title/description search if the index is missing.
  fetch    pull one page's clean markdown, windowed         (context-bounded)
  related  list sibling pages in the same index section     (fan out to adjacent topics)
  refresh  re-download llms.txt + rebuild the search index  (the entire maintenance story)

stdlib only; network only on `fetch`/`refresh`.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

DOCS_BASE = "https://goteleport.com/docs"
LLMS_URL = f"{DOCS_BASE}/llms.txt"
SCRIPT_DIR = os.path.dirname(__file__)
REFERENCES = os.path.join(SCRIPT_DIR, "..", "references")
MANIFEST = os.path.join(REFERENCES, "llms.txt")
INDEX_FILE = os.path.join(REFERENCES, "search-index.json")
DEFAULT_MAX_CHARS = 5000

LINK_RE = re.compile(r"^\-\s*\[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)\s*:?\s*(?P<desc>.*)$")

# Stop words MUST be identical to the index builder's, or query tokenization
# won't align with the indexed terms — a divergent set silently drops terms from
# queries that were indexed (and vice-versa), degrading recall. teleport_index.py
# is the single source of truth; import it rather than maintaining a second copy.
if SCRIPT_DIR and SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from teleport_index import STOP_WORDS as STOP


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
    tokens = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]
    if not tokens and text.strip():
        # Query had content but produced no usable tokens. Distinguish the two
        # causes so the message isn't misleading: all-stop-word/too-short ASCII
        # queries vs genuinely non-ASCII input (the index is English/ASCII-only).
        if re.search(r"[a-z0-9]", text.lower()):
            sys.exit("query has no searchable terms (only stop words or single characters); add a distinctive term")
        sys.exit("no indexable terms in query; the search index is English/ASCII-only")
    return tokens


def _load_index():
    """Load the TF-IDF search index from disk, or return None if missing/corrupt."""
    if not os.path.exists(INDEX_FILE):
        return None
    try:
        with open(INDEX_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def cmd_search(args):
    """TF-IDF content search with lexical fallback."""
    idx = _load_index()

    if idx:
        _search_tfidf(args, idx)
    else:
        _search_lexical(args, reason="index_missing")


def _search_tfidf(args, idx: dict):
    """Search page content using the pre-built TF-IDF index."""
    q_terms = _terms(args.query)
    if not q_terms:
        sys.exit("empty query after removing stop words; be more specific")

    docs = idx["docs"]
    index = idx["index"]
    scores: dict[int, float] = {}

    for term in set(q_terms):
        postings = index.get(term, {})
        for doc_idx_str, weight in postings.items():
            doc_idx = int(doc_idx_str)
            scores[doc_idx] = scores.get(doc_idx, 0) + weight

    if not scores:
        # Fall back to lexical if TF-IDF finds nothing — index exists but
        # query terms don't match any indexed content.
        _search_lexical(args, reason="no_term_matches")
        return

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    displayed = min(len(ranked), args.limit)
    built = idx.get("built", "unknown date")
    print(f"# {displayed} of {len(ranked)} results for: {args.query}  (TF-IDF content search, index built {built})\n")

    for _, (doc_idx, score) in enumerate(ranked[: args.limit]):
        doc = docs[doc_idx]
        print(f"[{doc['title']}]({doc['url']})")
        if doc.get("preview"):
            print(f"    {doc['preview'][:300]}")
        if doc.get("desc"):
            print(f"    — {doc['desc']}")
        print(f"    — score: {score:.1f}")
        print()


def _search_lexical(args, reason=None):
    """Fallback: lexical search over llms.txt titles and descriptions."""
    entries = load_manifest()
    q = _terms(args.query)
    if not q:
        sys.exit("empty query after removing stop words; be more specific")
    scored = []
    for e in entries:
        title_t = _terms(e["title"])
        desc_t = _terms(e["desc"])
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
            if score == 0 and term in e["title"].lower():
                score += 1
        if score:
            scored.append((score, e))
    scored.sort(key=lambda x: (-x[0], x[1]["title"]))
    if not scored:
        print(f"No matches for: {args.query}")
        print("Try broader terms, or `refresh` if the index is stale.")
        return
    if reason == "index_missing":
        header = f"# {len(scored)} results for: {args.query}  (lexical title search — build index with `refresh --index`)\n"
    else:
        header = f"# {len(scored)} results for: {args.query}  (lexical title search)\n"
    print(header)
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
    # Drop any #fragment or ?query before appending .md — the .md endpoint is a
    # flat file and 404s on '.../tsh#section.md' or '.../tsh?tab=cloud.md'.
    url = url.split("#", 1)[0].split("?", 1)[0]
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
    n = sum(1 for ln in data.splitlines() if LINK_RE.match(ln))
    print(f"refreshed {MANIFEST}\n{n} pages indexed from {LLMS_URL}")

    if args.index:
        print("\nbuilding TF-IDF search index ...")
        import subprocess
        indexer = os.path.join(SCRIPT_DIR, "teleport_index.py")
        result = subprocess.run(
            [sys.executable, indexer],
            timeout=600
        )
        if result.returncode != 0:
            print(f"warning: index build failed (exit {result.returncode})")


def main():
    p = argparse.ArgumentParser(description="Search & read the Teleport docs.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="TF-IDF content search (lexical fallback if index missing)")
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

    rf = sub.add_parser("refresh", help="re-download llms.txt; --index to rebuild search index")
    rf.add_argument("--index", action="store_true", help="also rebuild the TF-IDF search index")
    rf.set_defaults(func=cmd_refresh)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

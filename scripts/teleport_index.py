#!/usr/bin/env python3
"""teleport_index.py — build a searchable TF-IDF index from all Teleport docs pages.

Downloads every page listed in llms.txt via the clean .md endpoints, tokenizes
them, and saves a sparse index to references/search-index.json. Pure stdlib;
the index is ~2–5MB for 765 pages and is shipped in the repo so consumers never
need to build it — just run `refresh` when the docs drift.

Index format (references/search-index.json):
  {
    "version": 1,
    "built": "2026-06-16T...",
    "doc_count": 765,
    "docs": [{"url": "...", "title": "...", "desc": "..."}, ...],
    "index": {"term": {"0": 2.5, "5": 1.3}, ...}
  }

Search (in teleport_docs.py) loads the index, tokenizes the query, and sums
term weights per document — no model, no embeddings, no network.
"""

import json
import math
import os
import re
import sys
import time
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path

DOCS_BASE = "https://goteleport.com/docs"
LLMS_URL = f"{DOCS_BASE}/llms.txt"
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
REFERENCES = REPO_DIR / "references"
LLMS_MANIFEST = REFERENCES / "llms.txt"
INDEX_FILE = REFERENCES / "search-index.json"

# ── tokenization ────────────────────────────────────────────────────────────

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall", "you", "your",
    "we", "our", "they", "them", "their", "it", "its", "he", "she", "his",
    "her", "this", "that", "these", "those", "not", "no", "nor", "so",
    "if", "then", "than", "too", "very", "just", "about", "also", "into",
    "over", "such", "only", "other", "new", "some", "any", "each", "all",
    "both", "few", "more", "most", "up", "out", "when", "where", "which",
    "what", "who", "how", "why", "here", "there", "now", "get", "set",
    "use", "using", "used", "see", "make", "made", "need", "like", "one",
    "two", "how", "i", "my", "me", "teleport",
}

def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumeric, filter stop words + short tokens."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


# ── page fetching ───────────────────────────────────────────────────────────

def _http_get(url: str) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": "teleport-index-builder/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_llms_txt(path: Path) -> list[dict]:
    """Parse llms.txt → [{title, url, desc, section}, ...]."""
    entries = []
    section = ""
    link_re = re.compile(
        r"^\- \[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)\s*:?\s*(?P<desc>.*)$"
    )
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("## "):
                section = line[3:].strip()
                continue
            m = link_re.match(line)
            if m:
                entries.append({
                    "title": m.group("title").strip(),
                    "url": m.group("url").strip(),
                    "desc": m.group("desc").strip(),
                    "section": section,
                })
    return entries


def fetch_page_md(url: str) -> str:
    """Fetch a docs page as clean markdown (strips the token_count header)."""
    if not url.endswith(".md"):
        url = url.rstrip("/") + ".md"
    raw = _http_get(url)
    # Drop the leading {"token_count": N} line if present
    lines = raw.splitlines()
    if lines and lines[0].lstrip().startswith('{"token_count"'):
        lines = lines[1:]
        if lines and lines[0].strip() == "":
            lines = lines[1:]
    return "\n".join(lines)


# ── TF-IDF index building ───────────────────────────────────────────────────

def build_index(entries: list[dict], progress: bool = True) -> dict:
    """Download all pages, compute TF-IDF, return the index dict.

    Returns a dict ready to serialize as search-index.json.
    """
    doc_vectors: list[Counter] = []  # per-doc term → count
    docs_meta: list[dict] = []       # url, title, desc, preview per doc
    total = len(entries)

    for i, entry in enumerate(entries):
        if progress and (i % 50 == 0 or i == total - 1):
            print(f"\r  fetching {i+1}/{total}  ", end="", file=sys.stderr, flush=True)
        try:
            md = fetch_page_md(entry["url"])
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            print(f"\n  skip {entry['url']}: {e}", file=sys.stderr)
            docs_meta.append({
                "url": entry["url"],
                "title": entry["title"],
                "desc": entry["desc"],
                "preview": "",
            })
            doc_vectors.append(Counter())
            continue

        # Extract substantial text: skip code fences, headings, link-only lines
        text_lines = []
        preview_lines = []
        in_fence = False
        for line in md.splitlines():
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            stripped = line.lstrip("#").strip()
            if not stripped or stripped.startswith("[") and stripped.endswith(")"):
                continue
            text_lines.append(line)
            if len(preview_lines) < 8 and not stripped.startswith("#"):
                preview_lines.append(stripped)
        text = " ".join(text_lines)
        preview = " ".join(preview_lines)[:500]

        tokens = tokenize(text)
        doc_vectors.append(Counter(tokens))
        docs_meta.append({
            "url": entry["url"],
            "title": entry["title"],
            "desc": entry["desc"],
            "preview": preview,
        })

    if progress:
        print("", file=sys.stderr)

    # Compute document frequencies
    N = len(doc_vectors)
    df: Counter = Counter()  # term → number of docs containing it
    for vec in doc_vectors:
        df.update(set(vec.keys()))

    # Compute TF-IDF weights and build sparse index
    # IDF = log((N + 1) / (df + 1)) + 1  (smooth)
    # TF  = 1 + log(count)               (sublinear)
    # Weight = TF * IDF, stored per (term, doc_idx)
    index: dict[str, dict[str, float]] = {}

    for term, doc_freq in df.items():
        idf = math.log((N + 1) / (doc_freq + 1)) + 1
        postings: dict[str, float] = {}
        for doc_idx, vec in enumerate(doc_vectors):
            count = vec.get(term, 0)
            if count == 0:
                continue
            tf = 1 + math.log(count)
            postings[str(doc_idx)] = round(tf * idf, 4)
        index[term] = postings

    return {
        "version": 1,
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "doc_count": N,
        "docs": docs_meta,
        "index": index,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        return

    print("teleport_index.py — building full-text search index", file=sys.stderr)
    print(f"  manifest: {LLMS_MANIFEST}", file=sys.stderr)

    # 1. Refresh llms.txt if needed (or just read it)
    if not LLMS_MANIFEST.exists():
        print("  downloading llms.txt ...", file=sys.stderr)
        data = _http_get(LLMS_URL)
        REFERENCES.mkdir(parents=True, exist_ok=True)
        LLMS_MANIFEST.write_text(data, encoding="utf-8")
        print(f"  {LLMS_MANIFEST} saved", file=sys.stderr)

    # 2. Parse manifest
    entries = parse_llms_txt(LLMS_MANIFEST)
    print(f"  {len(entries)} pages indexed in llms.txt", file=sys.stderr)

    # 3. Build index
    print("  downloading pages and building index ...", file=sys.stderr)
    t0 = time.time()
    index_data = build_index(entries)
    elapsed = time.time() - t0
    print(f"  built index of {index_data['doc_count']} docs "
          f"({len(index_data['index'])} terms) in {elapsed:.1f}s",
          file=sys.stderr)

    # 4. Save
    REFERENCES.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = INDEX_FILE.stat().st_size / 1024
    print(f"  saved {INDEX_FILE} ({size_kb:.0f} KB)", file=sys.stderr)
    print(f"\nBuilt search index from {index_data['doc_count']} pages. "
          f"Add references/search-index.json to git and commit.", file=sys.stderr)


if __name__ == "__main__":
    main()

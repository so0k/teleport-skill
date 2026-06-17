# Maintaining the search index

Background for the `teleport-docs` skill: how `search` works and how to refresh it. You don't
need this to use the skill day-to-day — read it only when search results feel stale or you're
maintaining the repo.

## How search works

- `search` reads a **pre-built index** at `references/search-index.json` covering the full text
  (prose **and** code blocks — config keys, CLI flags, file names, error strings) of all ~765
  docs pages. It runs **offline** — no network call — and ranks results with **BM25**, which
  normalizes for page length so a long page (e.g. the Changelog) doesn't dominate by sheer size.
- If `references/search-index.json` is missing, `search` transparently **falls back** to a
  lexical search over the page titles/descriptions in the cached `references/llms.txt`. That
  still finds pages by title, just not by body content.
- The index ships in the repo, so a fresh clone works immediately — no build step required.

## Freshness: what can drift, and what can't

- **Page content never goes stale**: `fetch` always pulls the live `…​.md` from goteleport.com.
- **What can drift** is the index's view of *which pages exist and their ranked terms* — it's a
  point-in-time snapshot (see the `built` timestamp inside `search-index.json` and printed in
  `search` output). After Teleport adds, renames, or removes pages, the index lags until rebuilt.

Symptoms that a rebuild is worthwhile: `search` misses a page you know exists, returns a URL that
now 404s, or previews look out of date.

## Refreshing

```bash
# Fast: re-download the page list (llms.txt) only — one network request.
python3 scripts/teleport_docs.py refresh

# Full rebuild: regenerate llms.txt AND the BM25 content index.
python3 scripts/teleport_docs.py refresh --index
```

**`refresh --index` is expensive — run it deliberately, not casually.** It:

- fetches **all ~765 pages** over the network (the `.md` endpoint for each), throttled to ~0.2s
  between requests with retry/backoff on errors — so it takes **several minutes** of wall-clock;
- tokenizes every page and computes BM25 weights (`k1=1.2`, `b=0.75`) across the whole corpus;
- writes `references/search-index.json` (**~4 MB**), deterministically (sorted keys) so the
  committed file is byte-reproducible.

The build runs `scripts/teleport_index.py`, which you can also invoke directly. When maintaining
the repo, commit the regenerated `references/search-index.json` (it's marked
`linguist-generated` in `.gitattributes`, so diffs stay quiet).

## Tunables

In `scripts/teleport_index.py`: `BM25_K1` / `BM25_B` (ranking), `_REQUEST_SLEEP` (politeness
delay between fetches), and `STOP_WORDS` (shared with the searcher — keep them identical, or
query terms stop matching indexed terms).

# Changelog

Notable changes to the `teleport-docs` skill. The search index
(`references/search-index.json`) is regenerated with `teleport_docs.py refresh --index`;
each entry below notes when the index format or contents changed so consumers can tell
whether a re-pull is worthwhile.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## Unreleased

### Added
- **Code blocks are now indexed.** Content inside ` ``` ` / ` ~~~ ` fences (config keys,
  CLI flags, file names, error strings) is tokenized into the search index — previously it
  was dropped, so terms that appear only in examples (e.g. `mysqld`, `pg_hba.conf`,
  `hostssl`) were unfindable. Code is still kept out of the human-readable preview.

### Changed
- **Ranking switched from raw TF-IDF to Okapi BM25** (`k1=1.2`, `b=0.75`). The `b`
  length-normalization term stops long pages (notably the Changelog) from dominating
  results purely by size. Index format bumped to **version 2** and gains an `avg_doc_len`
  field. Weights are baked per-(term, doc) at build time, so the searcher is unchanged.
- Hardened the code-fence parser: handles ` ``` ` and ` ~~~ `, a language on the opener,
  and a closer whose run is ≥ the opener's (CommonMark) — so Teleport's ` ```code … ```` `
  and nested fences no longer desync the parser.
- Index size: ~3.7 MB → ~4.0 MB (more terms indexed); rebuild is deterministic
  (`sort_keys`), so the committed blob is byte-reproducible.

### Fixed
- Unified the stop-word list between the index builder and the searcher (they had diverged,
  silently dropping some query terms and degrading recall).
- `_to_md_url` no longer appends `.md` after a `#fragment` / `?query` (which produced 404s).

## 2026-06-16 — TF-IDF content search

### Added
- **Pre-built content search index** (`scripts/teleport_index.py` →
  `references/search-index.json`): full-text search over all ~765 pages, offline, with
  content previews. Replaces the title/description-only lexical search, which missed
  queries whose terms live in page bodies. Lexical title search is kept as a fallback when
  the index is absent. (PR #1.)
- `refresh --index` rebuilds both `llms.txt` and the search index.

## 2026-06-16 — Initial release

### Added
- Lightweight skill wrapping Teleport's own published endpoints: the `llms.txt` page index
  and per-page `.md` (clean, token-counted markdown). Helper CLI `teleport_docs.py` with
  `search` / `fetch` / `related` / `refresh`, an escalation-ladder `SKILL.md`, and grounding
  rules. Routes IaC/expression generation to the Terraform provider resource references and
  the predicate-language reference to avoid hallucinated config/expressions.
- Eval scenarios under `evals/` (rollout topics, schema-exactness, and content-dependent
  body-only queries).

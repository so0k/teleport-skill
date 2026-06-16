# teleport-docs — an Agent Skill for the Teleport documentation

A [Claude Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) that gives an AI
coding agent authoritative, progressively-discovered access to the official
[Teleport](https://goteleport.com) documentation.

It is modeled after the **AWS Documentation MCP server** (search + "read returns clean
LLM markdown"), but delivered as a lightweight, maintainable Skill rather than a running MCP
server — because Teleport already publishes everything an agent needs:

- **[`/docs/llms.txt`](https://goteleport.com/docs/llms.txt)** — a ready-made index of ~765
  pages (`Title`, URL, one-line description, grouped by section).
- **Per-page `.md` twins** — append `.md` to any docs URL (e.g.
  [`/docs/get-started.md`](https://goteleport.com/docs/get-started.md)) for clean, token-counted
  markdown. No HTML scraping, no MDX processing.
- **Pre-built TF-IDF search index** — `references/search-index.json` indexes the full text of
  all ~765 pages (~3.6 MB). Search is offline, content-level, and needs no model or network call.

So there's no scrape, no chunking, and no semantic index to maintain — the skill wraps
Teleport's own endpoints.

## What it does

The skill teaches the agent an escalation ladder via one small helper CLI
(`scripts/teleport_docs.py`, Python 3 stdlib only):

| Command | Purpose | AWS Docs MCP analogue |
|---|---|---|
| `search "<query>"` | TF-IDF content search over pre-built index (offline, previews included) | `search_documentation` |
| `fetch <url> [--max-chars N --start I] [--section H]` | clean markdown for one page, windowed | `read_documentation` |
| `related <url>` | sibling pages in the same index section | `recommend` |
| `refresh [--index]` | re-download `llms.txt`; `--index` also rebuilds the search index | — |

The agent searches → fetches only the relevant page(s) → answers with cited
`goteleport.com/docs/...` URLs, grounding every claim in fetched docs instead of memory.

## Install

Clone into your agent's skills directory:

```bash
git clone https://github.com/so0k/teleport-skill.git ~/.claude/skills/teleport-docs
# The search index is shipped in the repo — no build step needed.
# If you want the latest content, rebuild:
python3 ~/.claude/skills/teleport-docs/scripts/teleport_docs.py refresh --index
```

Then ask your agent a Teleport question (e.g. "how do I deploy `tbot` on GitHub Actions?")
and the skill triggers automatically.

## Maintenance

- **Search index** is shipped pre-built in the repo (`references/search-index.json`).
  No build step required. Rebuild with `teleport_docs.py refresh --index` after major doc updates.
- **Page content** is always current — `fetch` reads the live `.md` endpoints.
- Tracks the **latest** major Teleport version (the live site).

## Try the CLI directly

```bash
python3 scripts/teleport_docs.py search "tbot github actions machine id"
python3 scripts/teleport_docs.py fetch https://goteleport.com/docs/machine-workload-identity/deployment/github-actions.md --max-chars 4000
```

## License

MIT — see [LICENSE](LICENSE). Teleport documentation content is © Gravitational, Inc. and is
fetched live from goteleport.com. This repo contains the skill wrapper, a cached copy of
the public docs index (`llms.txt`), and a pre-built TF-IDF search index
(`references/search-index.json`) which includes short page-text previews from the live
docs endpoints.

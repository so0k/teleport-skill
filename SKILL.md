---
name: teleport-docs
description: >-
  Authoritative, grounded answers from the official Teleport documentation
  (goteleport.com/docs). Use whenever a question is about how Teleport works or how to
  configure it — Machine ID / Workload Identity and `tbot`, RBAC roles and access controls,
  SSO/auth connectors, database / application / Kubernetes / desktop / server (SSH) access,
  MCP access and the Agentic Identity Framework, Access Requests, Identity Governance &
  Security, the Terraform/Kubernetes operators and other infrastructure-as-code, Teleport
  Connect, or the `tsh`/`tctl`/`tbot` CLIs and `teleport.yaml` config. Reach for this even
  when the user doesn't say "the docs" — if they're asking what Teleport does or how to set
  something up in Teleport, ground the answer here instead of relying on memory, because
  Teleport's behavior and flags change across releases.
metadata:
  source: https://goteleport.com/docs/llms.txt
  page_endpoints: "https://goteleport.com/docs/<path>.md (clean markdown, token-counted)"
  tracks: "latest major version (the live site; currently v18)"
---

# Teleport docs

Answer Teleport questions from the official docs, not from memory. Teleport adds resource
kinds, role fields, and CLI flags every release and renames things across major versions, so
a remembered answer is often quietly out of date. This skill lets you search the docs and pull
only the page (or section) a given question needs, keeping your context small.

Run the helper from this skill's directory:

```
python3 scripts/teleport_docs.py <command>
```

## The loop: search → fetch → (related)

Escalate only as far as the question needs.

1. **Search by content** — find the right page(s). Search matches the actual **page content**,
   not just titles, so a query about a specific config key, CLI flag, or error string finds the
   page even when its title never mentions that term. Lead with the distinctive nouns
   (product/feature/CLI names, exact field/flag/error strings), not filler. (If the content
   index isn't present it transparently falls back to a title/description search.)
   ```
   python3 scripts/teleport_docs.py search "tbot github actions machine id" --limit 8
   ```

2. **Fetch a page** — read the clean markdown for a result. Output is windowed (default ~5000
   chars) to stay context-bounded; if it prints a `--- truncated at char N ---` line, continue
   with `--start N`. For a long reference page, jump straight to one section with `--section`.
   ```
   python3 scripts/teleport_docs.py fetch <url-from-search> --max-chars 6000
   python3 scripts/teleport_docs.py fetch <url> --start 6000          # next window
   python3 scripts/teleport_docs.py fetch <url> --section "Prerequisites"
   ```
   `fetch` accepts a full `…​.md` URL, a `/docs/...` path, or a bare slug, and adds `.md` if
   missing — so paste a result URL as-is.

3. **Related pages** (optional) — when one page isn't enough, list its siblings in the same
   index section to fan out to adjacent topics.
   ```
   python3 scripts/teleport_docs.py related <url>
   ```

## Generating config, IaC, or predicate expressions

Teleport YAML, Terraform/Kubernetes-operator resources, and `where`/`condition` predicate
expressions are the things models most often hallucinate — invented field names, the wrong
nesting, attributes guessed as blocks, or expression syntax borrowed from the wrong context.
Don't write these from memory. Before emitting a resource or an expression, fetch the exact
schema and quote it:

- **Terraform / IaC resource shape** — fetch the specific provider resource page, which lists
  every attribute, its type, and required/optional status (and a working example). The pages are
  `reference/infrastructure-as-code/terraform-provider/resources/<resource>.md` (e.g.
  `…/resources/access_monitoring_rule.md`, `…/resources/access_list.md`, `…/resources/role.md`).
  Search for the resource name to find the page, then `fetch` it.
- **Predicate expressions** (`where` clauses, Access Monitoring Rule `condition`, label
  expressions, resource-filter `--query`) — fetch
  `reference/access-controls/predicate-language.md`. The syntax is **context-specific**, so read
  the section for your context rather than assuming. For example, an Access Monitoring Rule
  `condition` draws from fields like `access_request.spec.roles` and `user.traits` and uses
  functions `contains` / `contains_any` / `contains_all` / `regexp.match` (e.g.
  `access_request.spec.roles.contains("on-call-db")`) — which is **not** the same operator/field
  set used to scope allow/deny rules inside a role. Confirm the field names and function forms
  on the page before composing the expression.

## Grounding rules

These keep answers trustworthy — they're the reason to use the skill at all:

- **Ground every claim in a fetched page.** Don't answer Teleport config/behavior questions
  from training; search and read first. If `search` returns nothing useful, say so and refine
  the query rather than guessing.
- **Cite the source URL** (the `goteleport.com/docs/...` page) for the facts you used, so the
  user can verify and read more.
- **Quote exact identifiers** — role fields, `teleport.yaml` keys, `tsh`/`tctl`/`tbot` flags,
  resource kinds — from the page text, since these are the things memory gets subtly wrong.
- **Docs are read-only**, and there's no need to save them into project memory — recall fresh
  each time so you track the current release.

## Version note

The page endpoints serve the **current major version** (the live site, currently v18). If the
user pins an older version, say that you're reading latest; the site also serves versioned
paths (e.g. `/docs/ver/16.x/...`) if you need to confirm an older release.

## Keeping search fresh

`fetch` always reads the live page, so page **content** is always current. Only `search`'s
view of *which pages exist* can drift as docs are added or renamed. If `search` misses a page
you'd expect, the index can be rebuilt — see
[`references/maintaining-the-index.md`](references/maintaining-the-index.md) for how it works
and what a rebuild costs (it makes a lot of network calls).

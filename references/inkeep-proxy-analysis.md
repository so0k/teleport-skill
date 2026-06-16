# Inkeep Proxy on goteleport.com/docs — Architecture & Alternatives

This documents the Inkeep-powered search on [goteleport.com/docs](https://goteleport.com/docs),
observed during the effort to go beyond lexical title-search for the `teleport-docs` skill.

## Why this exists

The Inkeep search on the docs site is **significantly better** than the `llms.txt`-based
lexical search originally used by this skill. It searches full page bodies with
semantic/neural ranking, returns rich excerpts, and navigates product/version filters.

We explored **calling it directly** from the skill's Python scripts (no browser, no API key).
That path is blocked by a Proof-of-Work (PoW) challenge gate, described below.

This document records the architecture, observed endpoint shapes, the PoW gating mechanism,
alternatives considered, and **maintainability risks** of each approach.

---

## Architecture

```
Browser (Docusaurus site)
  │
  ├─ GET /inkeep-proxy/v1/challenge
  │    → {algorithm, challenge, maxnumber, salt, signature}
  │
  ├─ Solve PoW (find number N such that
  │    SHA-256(N || salt || challenge) meets target)
  │
  └─ POST /inkeep-proxy/graphql
       Headers: { X-Inkeep-Challenge: ..., X-Inkeep-Solution: N }
       Body: GraphQL { search(searchInput: { searchQuery, searchMode, filters }) }
```

The backend proxy:

1. Serves a **challenge** with a short-lived salt (`?expires=…` in the salt).
2. Requires the client to solve a SHA-256 Proof-of-Work (find a `number` ≤ `maxnumber`
   that makes a hash pass the target).
3. Accepts the solved `number` + original challenge fields as headers on the GraphQL
   request.
4. On verification, forwards the request to Inkeep's API (with the **server-side API key**
   that is never exposed to the browser).

The PoW gate is **not** authentication — it's rate-limiting / abuse prevention. The
actual Inkeep API key lives server-side and is never sent to the client.

---

## Observed Endpoints

### 1. Challenge endpoint

**`GET https://goteleport.com/inkeep-proxy/v1/challenge`**

Response shape (live query, 2026-06-16):

```json
{
    "algorithm":   "SHA-256",
    "challenge":   "12bcc6538b54f5308144f675083939a9fc5f07e4d9e76e442323fdbcedf01d3d",
    "maxnumber":   50000,
    "salt":        "a07cd93e43b19eaeaa8d6cf2?expires=1781702946",
    "signature":   "08df0eecf7345c2aaa537835bec7ebe3f91e14242bbb7c46b50352c8d229a81a"
}
```

Key observations:

- `maxnumber` = 50,000 — the brute-force search space is only ~50k iterations (cheap).
- `salt` carries an expiry (`?expires=…` epoch seconds) — challenges are time-limited.
- `signature` is likely an HMAC over `(challenge, salt)` to prevent client tampering.
- Verification is a **POST** (returned 405 on GET); the exact verification endpoint
  shape was not probed further since it's handled transparently by the proxy.

### 2. GraphQL endpoint

**`POST https://goteleport.com/inkeep-proxy/graphql`**

Schema (introspection, 2026-06-16):

```graphql
type Query {
  search(searchInput: SearchInput!): SearchResult!
  getSearchRootRecords(ids: [ID!]!): …
  getChatSession(id: ID!): …
  hello: String
}

input SearchInput {
  searchQuery:     String!        # the user's query
  organizationId:  ID             # org-scoped (omitted by proxy)
  integrationId:   ID             # integration-scoped (omitted by proxy)
  searchMode:      SearchMode     # AUTO | KEYWORD | INTELLIGENT
  filters:         SearchFiltersInput
}

enum SearchMode { AUTO, KEYWORD, INTELLIGENT }

input SearchFiltersInput {
  product:         String         # e.g. "Teleport"
  productVersion:  String         # e.g. "18.x"
  sources:         [String!]      # content source filtering
  sourceIds:       String
  limit:           Int
  attributes:      JSON
}

type SearchResult {
  searchHits: [SearchHit!]!
  searchQuery: String!
}
```

The `search` query is the primary interface. Fields like `organizationId` and
`integrationId` are filled by the proxy server-side, so the client never sees them.

The GraphQL endpoint **rejects requests without valid PoW headers**.

### 3. Analytics endpoint

**`POST https://goteleport.com/inkeep-proxy/analytics`**

Used by the Inkeep widget for search analytics. Not relevant for programmatic search.

---

## Inkeep JS Client Bundle

The Docusaurus site bundles Inkeep's `InkeepModalSearchAndChat` widget via a dynamic
import in `main.*.js`:

```js
// Approximate reconstruction from the minified bundle
inkeepConfig: {
  apiKey: "…",              // NOT exposed — filled server-side or via build-time injection
  integrationId: "…",
  organizationId: "…",
  baseSettings: {
    // PoW proxy is configured here
    chatApiBaseUrl: "/inkeep-proxy",
    searchApiBaseUrl: "/inkeep-proxy",
  }
}
```

The Inkeep JS SDK (loaded dynamically from Inkeep's CDN) handles:

1. Fetching the challenge from `/inkeep-proxy/v1/challenge`
2. Solving the PoW (SHA-256 brute-force, 0–maxnumber)
3. Attaching `X-Inkeep-Challenge` and `X-Inkeep-Solution` headers to GraphQL requests
4. Rendering the search modal UI

The PoW solver in the JS bundle is **minified and served dynamically** — it is not a
static script. The challenge formula (exact byte layout for SHA-256 input, the target
threshold, and the signature scheme) is not documented and can change any time.

---

## No Inkeep CLI Tooling

- **`@inkeep/agents-cli`** — exists on npm, but is a **project management CLI** for
  Inkeep dashboard users (managing AI agents within the Inkeep platform). It is **not** a
  documentation search CLI.
- **Inkeep REST API** — requires an `apiKey`. No unauthenticated endpoint exists.
  Teleport's proxy is the only way to access Inkeep without an API key, and it's gated
  by PoW.
- **Inkeep SDK** — the JavaScript SDK (`@inkeep/uikit`) is designed for browser
  embedding (React components). It could theoretically run in Node.js with PoW support,
  but depends on DOM APIs and assumes browser environment.

---

## Alternatives Considered

### A. Python PoW solver (stdlib only)

**Approach:** Reproduce the PoW challenge solver in Python using `hashlib`, `json`, and
`urllib.request`. Query the GraphQL endpoint with the solved challenge.

**Status: REJECTED (fragile)**

**Why:**

- The PoW formula (exact byte layout fed into SHA-256, the target threshold check, how
  `signature` is used) is embedded in minified JavaScript served **dynamically** from
  Inkeep's CDN. It is not documented.
- The formula can change silently with any Inkeep SDK update (or any CDN-side
  configuration change). Hardcoding the formula creates brittle coupling to an opaque
  implementation detail.
- Even if reverse-engineered correctly today, the JS bundle version rotates. The PoW
  algorithm is an anti-abuse mechanism, not a stable API contract.

**Maintainability risk: HIGH.** Any Inkeep SDK update breaks the solver silently.
Teleport doesn't control when goteleport.com pushes a new Docusaurus build with the
updated Inkeep version. No changelog, no deprecation notice, no way to detect breakage
before users hit it.

### B. QuickJS embedded in Go binary

**Approach:** Compile a small Go binary that embeds QuickJS (a lightweight, embeddable
JS engine). Execute the actual Inkeep PoW JS client bundle inside QuickJS, solving the
challenge exactly as the browser does. Use Go's `net/http` for GraphQL communication.

**Status: TABLED (technically viable, high complexity)**

**Why tabled:**

- Requires shipping a compiled Go binary per platform (linux/amd64, darwin/arm64, etc.)
  or requiring the Go toolchain.
- The JS PoW solver is loaded from Inkeep's CDN at bundle-init time — the binary would
  need to fetch and eval it, meaning *network dependency still exists* at query time
  (defeating the "offline search" requirement from SKILL.md).
- The JS bundle's DOM dependency tree (it references `window`, `document`, etc.) needs
  shimming, adding maintenance burden.
- QuickJS embedding is non-trivial: CGO, build toolchain complexity, platform-specific
  linking.

**Maintainability risk: MODERATE.** The JS solver runs correctly (QuickJS is
spec-compliant for ECMAScript 2020), but the JS bundle URL / shape can change, and DOM
shims are fragile. The Inkeep JS SDK itself could change the challenge-flow API.

### C. TF-IDF content search (CHOSEN)

**Approach:** Pre-build a TF-IDF index from all ~765 doc pages and ship it as a ~3.6 MB
JSON file in the repo. Search is offline, zero network calls, stdlib Python only.

**Status: IMPLEMENTED** (PR #1, `feat/tfidf-content-search`)

**Trade-offs:**

- No semantic/neural ranking — pure statistical term weighting.
- Index must be rebuilt to capture doc changes (`refresh --index`).
- But: zero runtime dependencies, zero network calls, deterministic results, ships in
  the repo.

---

## Recommend Against Future PoW-based Approaches

The Inkeep proxy is a well-designed anti-abuse layer, _not_ a public API. Any approach
that tries to bypass it programmatically:

1. Violates the implicit contract (PoW exists to prevent exactly this — automated
   scraping of the search API).
2. Will break silently when the challenge algorithm changes.
3. Creates an ongoing maintenance obligation with no upstream coordination.

The **llms.txt → TF-IDF** pipeline we landed on is the right trade-off for a skill
bundle: it gives content-level search (good enough to replace title grep) without
binding to an undocumented, dynamic anti-abuse mechanism.

---

## References

- Inkeep docs: https://docs.inkeep.com/ (API requires `apiKey`)
- `@inkeep/agents-cli` README: https://www.npmjs.com/package/@inkeep/agents-cli
  (project management, not doc search)
- Teleport docs Docusaurus source: https://github.com/gravitational/teleport
  (repo also contains the docs site; the Inkeep proxy is likely in the web app layer)

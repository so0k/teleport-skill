# The teleport-docs Skill: A Scientific Story

*A teaching corpus for a skill-creator brown-bag. Audience: early skill-creator adopters still learning the concepts. The story is told as science — premise → hypothesis → experiment → validation → **failure** → pivot — with the decision points that changed the design. Every load-bearing claim is anchored to a verbatim quote from the session transcripts, the Hermes agent DB, or git/PR history.*

> **Provenance.** Reconstructed 2026-06-23 by mining local Claude Code session transcripts (`~/.claude/projects/-Users-vincentdesmet-teleport/f88dd9d6…`), the Hermes agent's SQLite session DB on the LAN VM (`~/.hermes/state.db`, `messages`/`sessions`), and the git/PR history of `so0k/teleport-skill`. Companion file: `first-pass.md` (kept local; not published).

---

## 0. The twist that makes this a good story: it was built across TWO machines and TWO model families

This is not one agent in one session. The skill's most interesting feature was authored by a **different model on a different machine**, then reviewed and corrected on this one. Keep this seam in mind throughout:

```
  so0k  (local Mac, Claude)                       Hermes  (LAN VM, GPT-5.5, via Discord)
  ──────────────────────────                      ─────────────────────────────────────
  06:34  explore premise
  06:37  sparse-checkout the docs
  07:17  ship lexical skill + create repo ──push──▶ (so0k/teleport-skill, public)
                                                    11:19  "Vibe Coding → Agentic Engineering"
                                                           (framing session, no code)
                                                    12:29  "Teleport Docs Search Explained" #1
                                                           → reverse-engineer Inkeep, reject it,
                                                             choose TF-IDF, BUILD it
  (PR appears) ◀──────────────fork PR #1──────────  13:12  open PR #1 from sakul-learning fork
  13:31  review PR #1 diff
         (Claude multi-agent review +
          body-only benchmark: 15–0–1)  ──review──▶ 13:28  "Explained #2": work the review,
                                                           file BM25 as a follow-up issue
  15:33  push eval commit 50b930c to the
         PR branch (maintainer write)   ──────────▶ 23:38  "Explained #3": rebase, finalize,
                                                           pickle/FTS5 side-quest
         ↓ (PR #1 merged; later, local side)
  code-block indexing (PR #8) → BM25 length-norm (c4f97a0) → SKILL.md slim-down
```

- **so0k side** = Vincent's Mac, Claude (Opus/Sonnet). Built the original lexical skill, *reviewed* the TF-IDF PR with a Claude multi-agent workflow, contributed the **eval regression bar**, and later implemented **BM25 + code-block indexing + the SKILL.md slim-down**.
- **Hermes side** = a LAN VM running an autonomous agent on **`gpt-5.5`** (reasoning effort medium, 40-iteration cap), driven entirely over a **Discord gateway** (`source=discord`, login `sakul-learning`, git author `lucas` (email redacted for public publishing)). It authored **PR #1 (the TF-IDF content search)**.

The headline teaching point: **the human was the architect and reviewer; two different agents did the implementation; and *evals/review* — not a smarter model — caught the one real design flaw.**

---

## 1. TL;DR arc (eight beats)

1. **Premise — "don't index, borrow the publisher's index."** Teleport ships a ready-made `llms.txt` manifest (765 pages) plus a clean `.md` twin of every page. The first skill did lexical search over the *one-line title+description* in that manifest. No page bodies, no vector store, no server. *"Highest ROI given Teleport already did the indexing work."*

2. **The human challenges the premise (over Discord, to a different agent).** *"this Skill.md uses a … lexical search over a one line site map.. it can't be as good as the doc search feature."* This kicks off the content-search work on the Hermes VM.

3. **Dead-ends first: Inkeep + embeddings, both rejected on *maintainability/shippability*, not quality.** The live site's search is **Inkeep** behind a SHA-256 Proof-of-Work gate; reverse-engineering it is *"a brittle maintenance trap."* Embeddings can't be shipped as a static index (*"the client also needs the model to vectorize the query"*). Both rejected.

4. **Pivot to owned, offline TF-IDF.** *"TF-IDF is just arithmetic… No model, no training, no GPU."* A ~3.6 MB JSON index (765 docs, 15,550 terms) ships in-repo with a lexical fallback. → **PR #1**, authored by the GPT-5.5 Hermes agent.

5. **The agent KNEW about BM25 and deliberately deferred it.** It floated BM25 by name, then rejected it for index size (*"requires storing per-doc term frequencies… which blows up the index"*), shipping **sublinear TF** (`1+log(count)`) with **no length normalization** — judging it "good enough" even while watching the Changelog rank high.

6. **Review catches the deferred flaw with data.** so0k's Claude multi-agent review ran a body-only benchmark (**TF-IDF 15 wins – lexical 0 – 1 tie** over 16 queries mined from all 1,111 `.mdx` pages) and *measured* the regression: the multi-hundred-page **Changelog (2,891 terms) outranks the focused `tbot` reference for `machine id tbot`.** Filed as a follow-up BM25 issue.

7. **Raw counts lie → BM25 lands (local side).** Okapi **BM25 (k1=1.2, b=0.75)** length-normalization, baked into postings at build time (commit `c4f97a0`). Changelog dethroned: top-4 for `machine id tbot` become all Machine/Workload-Identity pages.

8. **Hardening + honesty.** Code-block content gets indexed (so `mysqld`/`pg_hba.conf` become findable; 15.5k→19.8k terms, PR #8); SKILL.md is slimmed to ~112 lines with index internals moved behind a reference; a 14-scenario eval set encodes every past failure. Final honest read: vs a `web_search` baseline, correctness **ties** — the skill's real edge is **speed/determinism/offline**, ~29% faster.

---

## 2. Cast & artifacts

- **The repo:** `so0k/teleport-skill` (the skill is `teleport-docs`), public, created 2026-06-16 07:17Z on the local machine.
- **The data source — the publisher's own manifest:** `goteleport.com/docs/llms.txt`, a valid `llms.txt` of **765** `- [Title](url.md): description` lines under `## Section` headings, plus a clean markdown twin at `<url>.md` prefixed with `{"token_count": N}`. *"purpose-built LLM endpoints, no HTML scraping needed."*
- **The two builders:**
  - **so0k** (this Mac, Claude Opus/Sonnet) — original lexical skill, PR review, eval bar, BM25, code-indexing, slim-down. Human owner: **Vincent De Smet**.
  - **Hermes** (LAN VM, **`gpt-5.5`**, Discord gateway) — authored PR #1 (TF-IDF). gh login `sakul-learning`, git author `lucas` (email redacted for public publishing). *Not* the same as `sakul-learning/awesome-agentcore`, an unrelated course repo (see first-pass §3).
- **Key files:**
  - `SKILL.md` — frontmatter (`name`/`description` for routing) + the `search → fetch → related` protocol + grounding rules + a "Generating config, IaC, or predicate expressions" preciseness section. Slimmed to ~112 lines.
  - `scripts/teleport_docs.py` — helper CLI: `search` / `fetch` (windowed page + continue hint) / `related` (siblings) / `refresh` (re-cache llms.txt; `--index` rebuilds).
  - `scripts/teleport_index.py` — builds the offline index (`search-index.json`).
  - `references/search-index.json` — shipped index (v2 BM25, ~3.97 MB, deterministic `sort_keys`).
  - `references/maintaining-the-index.md` — where BM25 params / index location / refresh cost now live (out of SKILL.md).
  - `references/inkeep-proxy-analysis.md` — records the rejected Inkeep option (the road not taken).
  - `evals/evals.json` — 14 scenarios: ids 0–8 schema/rollout exactness, ids 9–13 body-only content-dependent.
  - `docs/CHANGELOG.md` — iteration history for skill consumers (staleness signaling).

---

## 3. The narrative, act by act

### Act A — The premise: lexical search over the manifest, WITHOUT page content *(local, so0k)*

**Hypothesis.** Model the skill after the AWS Docs MCP pattern — *lexical search + "get docs returns LLM copy"* — and let the publisher do the indexing. If Teleport already exposes a structured manifest and per-page LLM text, no scraping or semantic index is needed.

**What we tried.** Explore agents confirmed the manifest exists; a lightweight skill was built over the live `.md` endpoints (3 options considered: lightweight skill / MCP server / Hindsight semantic bank — lightweight chosen). Repo created and pushed at 07:17Z.

**The latent flaw.** `search` matched only the *one-line title+description* per page — *"no page bodies, so it's cheap … an index lookup, not a content search."* This blind spot wouldn't surface until evals.

**Evidence.**
> "Explore the teleport docs with the goal to build progressively discovered Skills … (lexical search, get docs returns llm copy)" — opening prompt
> "Ships a valid llms.txt … 765 `- [Title](url.md): description` lines … Every page has a clean markdown twin … purpose-built LLM endpoints, no HTML scraping needed."
> "Lightweight Skill: … No semantic index, no server, no CLI to maintain. Update = re-fetch llms.txt. Highest ROI given Teleport already did the indexing work."

### Act B — The framing: "Vibe Coding → Agentic Engineering" *(Hermes, 11:19Z)*

Earlier the same morning, on the Hermes VM, the human had Hermes synthesize a guide that became the *vocabulary* for everything after. It contains no teleport code, but it's the brown-bag's thesis.

**Quotable framing (open the talk with these):**
> "Vibe coding is hoping. Agentic engineering is engineering."
> "You are not writing the code directly 99% of the time — you are orchestrating agents who do, and acting as oversight." (Karpathy)
> **"Agent = Model + Harness"** — "the harness (context structure, tooling, evaluation) matters more than the model itself."
> "Generation is solved. Verification, judgment, and direction are the new craft."
> Three-layer context model (maps directly onto skills): **Static** (AGENTS.md, system prompts) / **Dynamic** ("Agent skills, RAG-retrieved docs, tool outputs") / **Evals & Guardrails** ("Test suites, deployment checks").
> "Automated tests become your primary contract with the AI." … "Without tests, AI cheerfully declares 'done' on broken code."

The teleport work is this thesis made concrete: the human set intent and the eval bar; the agent generated; review/evals verified.

### Act C — Reverse-engineering the real search, and rejecting it *(Hermes "Explained #1", 12:29Z)*

The human challenged the premise over Discord and let the agent explore. The full Socratic design dialogue (verbatim human prompts):
1. *"clone so0k teleport skill … can you find how the doc search on goteleport docs website works? this Skill.md uses a … lexical search over a one line site map.. it can't be as good as the doc search feature"*
2. *"what does it take to PoW solve in Python — does this require external libs (not just stdlib)? alternative is a small golang script … shipped binary"*
3. *"doesn't the inkeep browser client js potentially change the challenge / algo? … the best SKILL doesn't use python hit js execution (browser js) — or a QuickJS embedded solution (if single binary)"*
4. *"if you do the embedding, how do you distribute the semantic embedding database … the client also needs to run the same embedding model … unless you serve this as an MCP server? … what is TF-IDF and or sklearn or sentence-transformers"*
5. *"let's go and do the PR"*

**What happened.** The agent found the site uses **Inkeep** (hosted AI search, GraphQL behind a SHA-256 Proof-of-Work gate, `maxnumber: 50000`). It proved the PoW was brute-forceable in stdlib but *"the exact PoW formula isn't obvious … buried in Inkeep's minified JS."* so0k closed off each branch on **maintainability**:
> "the Inkeep JS can change whenever they want — hardcoding the algo is a brittle maintenance trap."

And closed off embeddings on **distribution**:
> The agent agreed embeddings are only shippable "as an MCP server" — you can't ship a static vector DB the client can't query without the model.

**The pivot.** The human's *"what is TF-IDF?"* produced the winning design:
> "TF-IDF is just arithmetic: **TF** = how often word W appears in doc D … **IDF** = `log(total_docs / docs_containing_W)` … No model, no training, no GPU."
> Distribution: download all ~765 `.md` pages at `refresh` time, compute weights, ship `references/search-index.json` (~2–5 MB), search with the same stdlib math. **"No auth, no PoW, no browser, no model."**

> ⚠️ **Teaching note:** TF-IDF was chosen over embeddings *for shippability, not retrieval quality.* The decision driver was "what can a skill ship as a static file with zero runtime deps," not "what scores best." That constraint — *a skill is a file other agents download* — is the whole reason this is a TF-IDF story and not a vector-DB story.

### Act D — The deliberate BM25 deferral (the judgment beat) *(Hermes "Explained #1")*

**This corrects the naïve "raw counts lie" reading.** The agent did *not* forget about length normalization — it weighed BM25 explicitly and chose to defer it:
> (design) "Use **BM25 scoring** (variant of TF-IDF, just arithmetic)."
> (implementation) "For BM25 scoring (better than raw TF-IDF) … `IDF × (TF×(k1+1)) / (TF + k1×(1 - b + b×doc_len/avgdl))` — But this requires storing per-doc term frequencies … which blows up the index. For a simpler approach that's pure stdlib … **Just TF-IDF.**"

It even **observed the skew live and judged it acceptable**:
> "The #1 results are spot-on for all three. **The changelog shows up a lot (it's a very long page with many terms), but the weights naturally push the targeted pages to the top.**"

Shipped scoring (sublinear TF + smoothed IDF, **no length normalization**):
```
IDF = log((N + 1) / (df + 1)) + 1   # smoothed
TF  = 1 + log(count)                # sublinear — dampens raw frequency
weight = round(TF * IDF, 4)         # summed per doc; no b·|d|/avgdl term
```
**PR #1 opened 13:12Z**, cross-fork from `sakul-learning` (765 docs, 15,550 terms, 3,631 KB), with a ~500-char preview stored per page so search is self-contained.

> ⚠️ **Teaching note:** This is the most valuable beat. A capable agent made a *reasonable* engineering tradeoff (simplicity/index-size over relevance) and even eyeballed the output as fine. The tradeoff was wrong — but you only know that with a **measurement**. That's the bridge to Act E.

### Act E — Review catches it with data *(local Claude review → Hermes "Explained #2", 13:28Z)*

so0k reviewed PR #1 with a **Claude multi-agent workflow**: parallel code review + an **empirical body-only benchmark** that mined queries whose terms live only in page bodies (from a local checkout of all 1,111 `.mdx` pages) and ran both engines, then adversarially verified.

**Result (from the review, relayed by Hermes):**
> "on 16 body-only queries, TF-IDF won **15–0–1** (wins–lexical–both miss), with **9** queries where lexical had complete misses (rank 0) that TF-IDF caught at rank 1 — e.g. `EKPub hash for TPM join token`, `generation mismatch / locked renewable cert`, `pg_hba.conf hostssl`, `session.participants where-clause`."

**And the measured regression that the agent had deferred:**
> "No L2/length normalization (measured relevance regression). Raw `sum(TF*IDF)` with no cosine/BM25 norm means the multi-hundred-page **Changelog (2,891 terms) outranks the focused `tbot` reference for `machine id tbot`.** Apply L2/pivoted-length normalization or switch to **BM25 (k1=1.2, b=0.75)**, then rebuild. (`teleport_index.py L188-190`.)"

Hermes (gpt-5.5) **acknowledged and deferred again** — it filed the fix as a GitHub follow-up issue (`gh issue create`) rather than implementing it in-session, alongside two others (SQLite FTS5 caching; `_load_index` truncated-JSON robustness). *(Issue number is recorded inconsistently across sessions — #3 in "Explained #3"'s live `gh issue list`, #4 in "Explained #2" — the BM25 follow-up itself is unambiguous.)*

> ⚠️ **Teaching note:** The human's contribution here was **not code** — it was the *measurement and the regression bar.* "Automated tests become your primary contract with the AI" (Act B) is literally what happened: so0k pushed commit `50b930c "Add content-dependent eval scenarios as the regression bar for TF-IDF search"` to the PR branch (maintainer write), and the agent rebased onto it.

### Act F — Live proof of the failure *(Hermes "Explained #3", 23:38Z)*

The over-counting is directly observable in the agent's own test output:
> Query **`tbot github actions deploy`** → #1 is the GitHub-Actions/tbot page (43.1), but **#2 is the Teleport Changelog (38.1)** — beating "Machine and Workload Identity Getting Started" (33.9) and even "Deploy tbot" (27.7).
> Issue title, verbatim: **"relevance: add length normalization (BM25) to prevent long pages from dominating search results."**

This session also shows the collaboration texture: a **pickle vs SQLite-FTS5 side-quest** for issue #2 (*"pickle (protocol 5): 46 ms → 15 ms, 3.1× load speedup"*; *"the bigger win … is sqlite3 with FTS5 … the search runs inside SQLite as a single FTS5 query"*), posted as an issue comment. PR #1 was driven from `CHANGES_REQUESTED` to a clean re-review state (deterministic index via `sort_keys=True`+`.gitattributes`, retry/backoff, honest fallback messages, `try/except` on `_load_index`).

### Act G — The BM25 pivot lands *(local, commit `c4f97a0`)*

Back on the local side, raw sublinear TF·IDF is replaced with **Okapi BM25 (k1=1.2, b=0.75)**: `k1` saturates term frequency (a term appearing 20× isn't 20× as relevant); `b=0.75` divides TF by a blend of doc length and corpus average so long pages can't dominate by size. Weights are baked per-(term, doc) at **build time**, so the searcher code and runtime cost are unchanged; index bumped to **version 2** (adds `avg_doc_len`).
> "for `machine id tbot` the top 4 are now all Machine/Workload Identity pages; **the Changelog is gone from the top.**"
> Index: version 2, `avg_doc_len 1205.6`, **3.97 MB**.

### Act H — Index the code blocks *(local, PR #8 / commit `133ad7c`)*

The indexer had dropped everything inside ``` fences, so tokens appearing *only* in code/config vanished — verified on master: `mysqld` (in a config block on the self-hosted MySQL page) was **absent from the index entirely**. The fix tokenizes code content into the page text (keeping it out of the human preview), hardening fence detection.
> "Fix verified: `mysqld`, `hostssl`, `tbot`, `spiffe` all `in_index=True` … Index grew **15.5k → 19.8k terms**."

Why it matters: the skill's whole value is retrieving exact identifiers — config keys, CLI flags, file names, error strings — which live disproportionately in code blocks (and in the very body-only eval queries the feature must win, like `pg_hba.conf`/`hostssl`).

### Act I — The honest final read *(local eval)*

Four content/schema scenarios, each run as two parallel Sonnet subagents: one *with* the BM25+code-indexed skill, one with *no skill but encouraged to use `web_search`* (riding Google's index over goteleport.com — a genuinely strong competitor).
> "**13/13 vs 13/13** — identical correctness to a web_search baseline, but the skill is **29% faster** (76s vs 107s mean) at ~4k more tokens … the skill's edge is **speed/determinism/offline-search, not raw capability.**"

> ⚠️ **Teaching note:** The team chose to *describe the skill by its true edge* rather than overclaim. Naming the honest advantage (speed/determinism/offline) is more useful than a fake correctness win.

---

## 4. Eval-driven design *(primary teaching angle)*

The evals are the spine. Five principles emerged:

**(1) A global skill contaminates your baseline.** The first eval was a lie: all three "baseline" subagents secretly invoked the skill (it lived in `~/.claude/skills/`, visible to every subagent, with a "pushy" description). *"those baselines are really with-skill runs and must be redone."* Fix: physically move the skill aside (`/tmp/teleport-docs-hidden`) **and** hide the local docs checkout a baseline was caught grepping. **Isolate the variable.**

**(2) Choosing the baseline IS the experiment.** A *web-enabled* baseline ties the skill (**19/19**) — it just looks up goteleport.com. That tests nothing about grounding. Switching to a **training-only, no-tools** baseline ("Claude in the wild") immediately exposed a real gap (**12/12 vs 6/12**), because the model hallucinated schema it can't verify from memory.

**(3) Let the eval encode the failure you just found.** Every failure became a permanent regression assertion:
- A real `terraform apply` bug the user hit → **eval-5** (AMR condition) with a **negative** assertion (absent: `access_request.roles` — missing `.spec`) + **positive** (present: `access_request.spec.roles`). It caught the baseline inventing `access_request.roles` and `auto_approve`.
- Audit-enum confusion → **eval-7** caught `frequency = "quarterly"` (a string) vs the true integer `3`.
- The title-only blind spot → five **body-only** scenarios (ids 9–13) added *explicitly to survive the next change*: "Use these to confirm the relevance improvement holds (esp. after adding length normalization)" — i.e. the BM25 follow-up was anticipated in the eval set before it was built.

**(4) The benchmark IS the review.** so0k's PR review wasn't prose opinion — it was a measured **15–0–1** body-only benchmark plus a live reproduction of the Changelog/`tbot` regression. The agent's deferral was overturned by *data*, not authority.

**(5) Cost discipline.** All fan-out eval subagents ran on `model: 'sonnet'` per policy — *"the point of the eval is the output design, which Sonnet exercises fine"* — reserving Opus for grading/analysis.

| Failure | Eval / mechanism | What it caught |
|---|---|---|
| AMR wrong field path | eval-5 (negative+positive) | baseline `access_request.roles`, invented `auto_approve` (4/4 vs 1/4) |
| Audit enum type | eval-7 | baseline `frequency = "quarterly"` vs truth `3` |
| TF attrs-vs-blocks | eval-6 | HCL block-vs-attribute hallucination |
| Title-only recall | evals 9–13 + review benchmark | body-only terms ranked 0 by lexical, 1 by content search (15–0–1) |
| Length over-counting | review's live `machine id tbot` repro | Changelog (2,891 terms) out-ranks the `tbot` reference → BM25 |

---

## 5. Skill anatomy & progressive disclosure *(primary teaching angle)*

**The consumer is an LLM, so the skill teaches a *protocol*, not a corpus.** SKILL.md = YAML frontmatter (`name`, `description` for routing) + an ordered loop:
```
search  → BM25/lexical over the offline index
fetch   → windowed .md page (+ "continue" hint for paging)
related → sibling pages
refresh → re-cache llms.txt (--index rebuilds)
```
The protocol escalates *only as far as the question needs* — manifest → page → related. That *is* progressive disclosure: the agent doesn't pull full pages until search says which page.

**A targeted preciseness section.** Beyond prose Q&A, SKILL.md routes the agent to `terraform-provider/resources/<name>.md` and `reference/access-controls/predicate-language.md` *before* emitting any resource or condition — the highest-hallucination zone (wrong field paths, attrs-guessed-as-blocks, predicate syntax from the wrong context). *"Don't write these from memory."*

**Slimming = progressive disclosure applied to the skill file itself.** SKILL.md trimmed 123 → ~112 lines with **0 internals leakage**: BM25 params, `search-index.json` location, and refresh cost moved into `references/maintaining-the-index.md` behind a one-line pointer.
> "An LLM consumer needs to know HOW to invoke it and what it's good for, not how the index is built or where the file lives. Exposing internals wastes context tokens."

Search is now described to the consumer as simply *"matches page content, with a title-search fallback."*

**Build-time vs runtime split.** `teleport_index.py` builds; `teleport_docs.py` queries. BM25 weights are computed at build time and baked into postings, so the deterministic (`sort_keys`) ~4 MB `search-index.json` ships in-repo and consumers never build it — *"pure math, no model, no GPU, no vector DB."*

**A CHANGELOG for staleness signaling.** `docs/CHANGELOG.md` records each step (initial skill → content-dependent evals → TF-IDF PR #1 → code-block indexing → BM25), noting when the index *format/contents* changed, so consumers know whether re-pulling is worthwhile.

---

## 6. Teaching takeaways (transferable lessons)

1. **Start from the corpus's own manifest.** Before building an index, check whether the publisher already did it. Teleport's `llms.txt` + per-page `.md` removed the need for scraping or a vector store.
2. **A skill is a file other agents download — design for shippability.** TF-IDF beat embeddings here *because it ships as a static, dependency-free JSON*, not because it retrieves better. Let the distribution constraint drive the design.
3. **A capable agent's reasonable tradeoff can still be wrong — measure it.** Hermes knew BM25, deferred it for simplicity, and eyeballed the output as fine. Only a benchmark proved the Changelog over-counts. Eyeballs aren't evals.
4. **A global skill contaminates your baseline.** Skills in `~/.claude/skills/` surface to every subagent. For an honest A/B, move the skill aside *and* hide any local ground-truth corpus a baseline could grep.
5. **Choosing the baseline IS the experiment.** A web-enabled baseline ties any docs skill; a training-only baseline exposes grounding. Pick the baseline that isolates the property you actually claim.
6. **Let evals encode the failure you just found.** Every regression bar in this skill is a fossilized past failure (a real `terraform apply` bug → eval-5; the length skew → the body-only suite written *before* BM25 existed).
7. **Raw counts lie — normalize.** Raw term-frequency rewards document *length*: the Changelog won `tbot` by sheer size. BM25's `b` (length norm) + `k1` (TF saturation) is the standard fix. Frequency ≠ density ≠ relevance.
8. **Index what users actually query.** Identifiers live in code blocks; dropping fenced content made `mysqld` unfindable — directly undercutting the skill's purpose.
9. **Hide internals from the LLM consumer.** SKILL.md should teach the *workflow*, not the implementation. Slimming to 112 lines with 0 internals leakage is progressive disclosure applied to the skill file.
10. **Be honest about the edge.** Against a strong `web_search` baseline the skill *tied* on correctness; the win was speed/determinism/offline. Say that plainly.

---

## 7. The collaboration pattern itself (the meta-lesson for the team)

This whole episode is a worked example of the Act-B thesis — **"Agent = Model + Harness"** and **"Generation is solved; verification, judgment, and direction are the new craft":**

- The **human acted as architect and reviewer**, not typist: set intent over Discord, closed off dead-ends (Inkeep, embeddings) on *maintainability* grounds, and contributed the **eval regression bar** (commit `50b930c`) rather than the search code.
- **Two different agents/models** did the implementation work (GPT-5.5 Hermes for TF-IDF; Claude locally for review, BM25, code-indexing, slim-down) — the harness (manifest, eval bar, PR review, follow-up issues) mattered more than which model was used.
- **Verification caught the one real flaw.** The smarter move wasn't a better model; it was a measurement.

---

## 8. Open threads / honest gaps

- **Hermes design dialogue is partly summarized.** "Explained #1/#2" preserve verbatim human prompts and key agent reasoning; "Explained #3"'s core Inkeep→TF-IDF dialogue survives mainly as a **post-compaction summary**, not turn-by-turn. The conclusions are consistent across all three sessions.
- **BM25 follow-up issue number is inconsistent** across sessions (#3 vs #4); the *fix* is unambiguous and landed as commit `c4f97a0`. Issue/PR numbering (#2 FTS5, #3/#4 BM25, #6 code-block, PRs #1/#8) was not re-verified against the live tracker.
- **No merge event for PR #1 was observed in the Hermes rows** — it was left awaiting re-review there; the local git history confirms the TF-IDF work did land (`28dbf63`) and was later superseded by BM25 (`c4f97a0`).
- **Exact model id for "Explained #1/#3"** is not stored per-message; `gpt-5.5` is confirmed for "Explained #2" from the `sessions` table, and the agent toolage (terminal/browser/gh) is consistent across all three.
- **Stop-word unification** (107-word indexer set vs 32-word searcher set) was diagnosed in review; whether it was fully unified vs left as a known follow-up isn't explicit in the mined events.
- **The 2026-06-23 retrospective session** (`c6c00adf`) only did transcript recon before being interrupted — it produced no design artifacts and confirmed **no `teach` skill is installed locally** (plan accordingly).
- **`sakul-learning` disambiguation:** the teleport fork is unrelated to `sakul-learning/awesome-agentcore` (an AgentCore course index) despite the shared org name (first-pass §3).

# Teaching notes & working state

## Audience & voice (hard rules — from the user)
- Audience: brown-bag of early skill-creator adopters. One+ reads English as a
  **second language**. Target **8th–9th grade** reading level. **Short sentences.**
- Talk to the viewer: **"you" / "we"**. Avoid third person.
- **No unexplained jargon.** Simplify hard words. **"substrate" is BANNED** — say
  "the platform" or "the work around the agent".
- Structure every lesson **Why → What → How** = **Problem → Solution approach →
  Mechanics**. Never open with a flat feature list. Lead with the pain.
- ONE running example: the `teleport-docs` skill. Each idea leads to the next.
- **Diagrams** for storytelling, built progressively. Keep tension: pose the question
  before the reveal.

## Grounding
- The primary source corpus is `../provenance/CORPUS.md` — a quote-anchored scientific
  story of how the real skill was built. Reuse its quotes; they are load-bearing.
- The shipped skill is `../SKILL.md`; helper is `../scripts/` (in the repo).
- Don't trust parametric knowledge — cite RESOURCES.md or the corpus.

## Corrected premise (from user, do not lose)
- The real pain: we PLAN rollouts with agents and depend on them to generate Terraform/
  YAML configs. Plans are high-risk; agents make subtle field mistakes. We want GROUNDED
  plans. Grounding source for the eval pain: `../evals/evals.json` (eval 0 = Entra SSO
  rollout; evals 5/6/8 = real Terraform field bugs).
- The origin analogy to lead with: **AWS Docs MCP** — it provides a `search` tool + a
  `fetch` for live docs. That two-move loop is how this design started. (We later ship as
  a skill, not an MCP — that's the Lesson 9 payoff.)

## Planned lesson arc (syllabus)
1. The grounding problem — planning/Terraform is high-risk; AWS Docs MCP search+fetch
   pattern; ground every field. (Agent = Model + Harness.)
2. Borrow the publisher's index — llms.txt + .md twins; the search→fetch→related loop.
3. The title-only blind spot — searching one line per page misses the content.
4. Evals that sample the blind spot — mine body-only questions with a workflow; benchmark.
5. Pick the engine — why TF-IDF beats embeddings *for shippability* (Inkeep & vectors rejected).
6. Raw counts lie — the Changelog over-counts; BM25 length normalization (k1, b).
7. Index what people query — code blocks (mysqld, pg_hba.conf) were invisible.
8. Reality check — skill vs. a Google-indexed model; ties on correctness, wins on speed.
9. Step back — skill vs. MCP server (hosting/uvx vs. thin ship; client-dumb embeddings).

Status: Lessons 1–8 done. index.html at 8/9. Glossary updated through Lesson 8.
Served on LAN: http://192.168.50.19:8000/teach/ (bg id b3z9yo10d).
NEXT (FINAL): Lesson 9 skill-vs-MCP — the bookend (we copied AWS Docs MCP in L1, shipped
a skill instead). Cover: MCP needs HOSTING or `uvx`/local run; skills are thin files you
ship. Embeddings/semantic (chromadb) belong on the MCP side (model at query time). Decision
table: public vs internal docs, who runs it, freshness, semantic need, reuse/ROI.
REINFORCE progressive discovery here per user: a skill keeps a SHORT SKILL.md index that
references out to advanced topics/workflows (corpus §5 slim-down, 123→112 lines, internals
behind references/). Close with ⏱️ worth-it/honesty. Consider a course-wrap recap + a
learning-record once the user demonstrates understanding.

Note on red→green cadence: use the box where a lesson closes a MEASURED failure with an
eval (L4 done, L6 BM25, L7 code-blocks, L8 reality-check). Design-tradeoff lessons
(L5 engine choice, L9 skill-vs-MCP) carry the thread via the ⏱️ worth-it/honesty box
instead — do NOT fake a regression box (that would violate the honesty we teach).

## TERMINOLOGY (user correction — do not mix these up)
- **Progressive discovery / disclosure** = how a harness (Claude Code) surfaces relevant
  info in SMALL BITS so the LLM can decide to dive deeper. A skill keeps a SHORT SKILL.md
  index and REFERENCES OUT to advanced topics/workflows. Taught in Lesson 2; reinforce in
  the skill-anatomy beat (Lesson 9 / slimming SKILL.md). NOT the iteration thread.
- **Agile iteration (short feedback loops)** = ship minimal → test → improve. THIS is the
  "each round sources more accurate data" thread (borrow index → body → BM25 → code
  blocks). Pairs with red→green. Used in L4, L5, L6 (fixed 2026-06-23 after I mislabeled
  it "progressive discovery").

## Two recurring threads (user-requested, KEEP GOING every lesson)
- **Agile iteration** — minimal design → test → improve; each round more accurate data.
- **🔴→🟢 regression locked in** — reusable component (assets/components.html + course.css
  .redgreen). Ends every lesson from L4 on: Red = the failure measured; Green = the eval
  that freezes it. Test-first: body-only suite written BEFORE BM25.
- **⏱️ Worth it? (ROI caveat)** — reusable .roi box. Ancillary work vs doing the job ×
  reuse count. Honest ending allowed: skill only TIES web_search on correctness (edge =
  speed/determinism/offline). Don't oversell. Retrofitted into L3; lives in L4; belongs in
  L8 (reality check) and L9 (skill vs MCP) prominently.
- Reusable components documented in assets/components.html. Reuse, don't re-inline.
- Contamination crisis + "choosing the baseline IS the experiment" → save for L8.

User edited Lesson 1's diagram to fix ASCII box alignment — keep diagrams tidy.

## Reusable assets
- `assets/course.css` — shared stylesheet (Tufte-ish, print-friendly). Link from every lesson.
- `assets/diagram.css` — (planned) progressive diagram helpers.

## Open follow-ups
- Confirm whether attendees want a hands-on build session (lessons 5–7 could become a lab).

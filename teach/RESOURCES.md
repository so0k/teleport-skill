# Build a docs Skill — Resources

Trusted sources for this course. Knowledge in lessons is drawn from here (or from the
quote-anchored `../provenance/CORPUS.md`), not from parametric guesses. All URLs below
were verified to resolve on 2026-06-23.

> Host note: `docs.claude.com/...` links 302-redirect to `platform.claude.com/...`.
> We list the resolved `platform.claude.com` form; the `docs.claude.com` form also works.

## Knowledge

### Agent Skills — what they are & how to write them
- [Equipping agents for the real world with Agent Skills — Anthropic Engineering (Oct 16 2025)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
  The canonical "why": Skills as folders of instructions + scripts + resources, progressive
  disclosure, open standard across Claude.ai / Claude Code / Agent SDK. Use for: Lessons 1–2 framing.
- [Agent Skills — overview (official docs)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
  The spec: skill structure and runtime architecture. Use for: precise "what's in a skill."
- [Skill authoring best practices (official docs)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
  The definitive how-to: `name`/`description` frontmatter rules, progressive disclosure,
  "keep SKILL.md under 500 lines, references one level deep," eval-driven development.
  Use for: Lessons 2, 4, 9. **The single best source for writing a `SKILL.md`.**
- [Extend Claude with skills — Claude Code docs](https://code.claude.com/docs/en/skills)
  Claude Code-specific mechanics of installing/managing skills. Use for: the hands-on lab.

### The data source — llms.txt
- [The /llms.txt file — the spec](https://llmstxt.org/)
  The manifest format our skill is built against: an `/llms.txt` markdown index (+ optional
  `/llms-full.txt`). Use for: Lesson 2 (borrow the publisher's index).
- [/llms.txt — a proposal to help LLMs use websites — Jeremy Howard, Answer.AI (Sep 3 2024)](https://www.answer.ai/posts/2024-09-03-llmstxt.html)
  The author's original announcement and motivation. Use for: provenance of the idea.

### Retrieval math — TF-IDF, BM25, evaluation
- [Tf-idf weighting — Introduction to Information Retrieval §6.2.2 (Manning, Raghavan, Schütze)](https://nlp.stanford.edu/IR-book/html/htmledition/tf-idf-weighting-1.html)
  Authoritative textbook treatment of `tf-idf = tf × idf`. Use for: Lesson 5.
- [The Probabilistic Relevance Framework: BM25 and Beyond — Robertson & Zaragoza (2009)](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)
  The canonical academic reference for BM25 (PDF on Robertson's own staff page). Use for:
  Lesson 6, the formal derivation and parameters.
- [Practical BM25, Part 2: the algorithm and its variables — Elastic Blog](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)
  Plain practical explainer of `k1` (term-frequency saturation) and `b` (length
  normalization) — exactly our index's knobs. Use for: Lesson 6, the intuitive version.
- [Evaluation in information retrieval — Intro to IR, Chapter 8](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-in-information-retrieval-1.html)
  Precision/recall, building a test collection, ranked vs unranked evaluation. Use for:
  Lesson 4 (the eval craft). Free full book: https://nlp.stanford.edu/IR-book/

### The road not taken — MCP, vector DBs, embeddings
- [What is the Model Context Protocol (MCP)? (official)](https://modelcontextprotocol.io/docs/getting-started/intro)
  The "USB-C port for AI" intro; client/server model. Use for: Lesson 9 (skill vs MCP).
- [Introducing the Model Context Protocol — Anthropic (Nov 25 2024)](https://www.anthropic.com/news/model-context-protocol)
  Origin + the N×M integration-problem framing. Use for: Lesson 9 provenance.
- [Chroma — Getting Started (official docs)](https://docs.trychroma.com/docs/overview/getting-started)
  The open-source vector DB: collections, automatic embedding, persistent vs in-memory,
  Chroma Cloud. Use for: Lesson 9, the hosted-semantic-search alternative.
- [Embeddings — Claude (official docs)](https://platform.claude.com/docs/en/build-with-claude/embeddings)
  What text embeddings are; semantic search by nearest neighbor; query-vs-document input
  types. Note: Anthropic ships no embedding model (recommends Voyage AI) — a teachable
  caveat about why you can't ship a static vector index. Use for: Lessons 5 and 9.

### The framing — vibe coding vs agentic engineering
- [Andrej Karpathy coins "vibe coding" (X, Feb 2 2025)](https://x.com/karpathy/status/1886192184808149383)
  Origin of the term ("fully give in to the vibes… forget the code even exists").
  *Note: X blocks automated fetch; URL + quote confirmed via search.*
- [Not all AI-assisted programming is vibe coding — Simon Willison (Mar 19 2025)](https://simonwillison.net/2025/Mar/19/vibe-coding/)
  Sharpens the distinction — disciplined AI-assisted engineering vs. vibe coding. Use for:
  Lesson 1 / closing framing ("generation is solved; verification is the craft").

## Wisdom (Communities)
*Where to test your skills on real people once you've built one.*

- [Anthropic Discord](https://www.anthropic.com/discord)
  Official community; channels for Claude Code, Skills, and MCP. Use for: feedback on a
  skill you built, "is this the right pattern?" questions.
- [r/ClaudeAI](https://reddit.com/r/ClaudeAI)
  Active subreddit; skills/MCP show-and-tell and troubleshooting. Use for: pattern critique.
- [MCP community (modelcontextprotocol.io)](https://modelcontextprotocol.io/)
  Server registry + GitHub discussions. Use for: when you decide to build the MCP path and
  want to see how others structure servers.

## Gaps
- No single authoritative write-up of the *exact* "ship a static search index in a skill
  vs. host an MCP server" tradeoff exists yet — this course's Lesson 9 + `CORPUS.md` is the
  closest synthesis. If a strong external piece appears, add it here.
- No verified-fetchable primary for the Karpathy quote (X blocks fetch); Willison corroborates.

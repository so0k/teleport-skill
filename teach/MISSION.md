# Mission: Build a grounded, eval-validated docs Skill

## Why
You plan real Teleport rollouts with LLM agents and depend on them to generate
**Terraform / YAML configs** — but the agents make subtle mistakes (wrong field paths,
invented fields, HCL blocks vs. attributes), and a high-risk plan that looks polished is
the dangerous kind. You want a brown-bag that teaches platform engineers to turn docs
into a **Claude Agent Skill** that grounds every field in a real page — modeled on the
**AWS Docs MCP** pattern (search + fetch) — and to *prove* it works with evals instead
of vibes. By the end, each attendee can ship a real skill, defend its design with
measurements, and make the honest call on **skill vs. MCP server** for their own corpus.

## Success looks like
- An attendee can build a working docs skill: a static search index + a `SKILL.md`
  protocol (`search → fetch → related`) that ships as a thin, dependency-free file.
- They can write **content-dependent evals** — sampling "tricky" questions whose
  terms live only in a page's *body*, not its title or one-line description — using a
  dynamic workflow, and read the benchmark like a scientist.
- They can run an honest **reality check**: how the skill compares to a model that
  leans on Google's index of the same public docs, and why the answer differs for
  *internal* docs.
- They can decide **ship-a-static-index (skill)** vs. **host-an-MCP-server
  (embeddings/vector search)** and justify it on hosting, freshness, and quality.

## Success metrics
- Each lesson lands one tangible win in <10 minutes, at an 8th–9th grade reading level.
- Every load-bearing claim cites a source (the corpus quotes, or a RESOURCES.md link).
- The running example never leaves Teleport — concepts compound on one story.

## Constraints
- **Audience:** early skill-creator adopters; at least one reads English as a second
  language. Short sentences, "you/we", no unexplained jargon. "Substrate" is banned.
- **Structure:** every lesson is Why → What → How (Problem → Solution → Mechanics).
  Never open with a flat feature list. Lead with the pain the platform engineer feels.
- **One running example:** the `teleport-docs` skill, grown lesson by lesson.
- **Diagrams** tell the story and build up progressively. Hold the answer; pose the
  question first to keep curiosity alive.

## Out of scope (for now)
- Building a production MCP server end-to-end (we *decide* about it; we don't ship it).
- Teleport itself as a product — it is the example corpus, not the subject.
- Deep ML theory of embeddings beyond "what changes the build-vs-host decision."

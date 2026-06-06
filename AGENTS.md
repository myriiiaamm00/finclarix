# AGENTS.md

This file documents how AI coding agents were used to build FinClariX, why
that choice made sense for this project, and how the human team and the agent
divided responsibility. It is the canonical reference for FinTech Assignment
2's requirement to explain "what coding agent(s) you used and why" and "how
you orchestrate your agents" — `CLAUDE.md` (the operational guidance file the
agent reads on every session) and the README's *AI Agents and Orchestration*
section both point back here rather than repeating this narrative.

## Which Coding Agent Was Used

FinClariX's implementation was built primarily with **Claude** — specifically
through Claude Code / the Claude Agent SDK (surfaced to the team via Cowork),
guided session-to-session by a project-level **`CLAUDE.md`** file that gives
the agent persistent context about the codebase: its architecture, its
guiding philosophy ("deterministic baseline first, AI as enhancement only"),
the analysis pipeline, and — critically — hard-won lessons like the
render-time-localisation rule that prevents a specific class of
language-switching bugs from being reintroduced.

## Why Claude Was a Good Choice for This Project

A few characteristics of this specific project made an LLM-based coding agent
a particularly good fit, and Claude in particular:

- **The product itself is about turning dense technical text into plain,
  empathetic language for a non-expert audience** — FinClariX's own system
  prompt for clause explanations ("a financially sharp friend... real talk,
  not a lecture") and its whole multilingual/UX philosophy required a lot of
  *iterative wording and tone work* across 14 languages and several layers of
  fallback messaging. An agent that's strong at natural language — drafting,
  critiquing, and refining copy in context — was directly useful for the
  product's core feature, not just its plumbing.
- **The codebase has several interacting "soft constraints"** (must work with
  zero API keys; AI must only ever enhance, never gate; language switches must
  update everything instantly; no new paid dependencies; all code/comments in
  English) that are easy to violate accidentally while iterating quickly. A
  persistent `CLAUDE.md` file plus an agent capable of holding that context
  across a long, multi-session build meant these constraints could be
  re-stated once and then *checked against* on every subsequent change,
  rather than re-derived from scratch each time.
- **Claude Code's file-aware, multi-file editing workflow** matched the
  project's modular `src/` structure well — most feature work touched three
  to five files at once (e.g. adding the translation layer meant a new module,
  an `i18n.py` key addition across 14 language tables, and an `app.py`
  refactor), and having an agent that could navigate, read, and edit across
  that surface in one coherent pass was significantly faster than doing it
  file-by-file by hand.
- **It's the tool the team already had hands-on experience orchestrating**,
  which mattered for staying within the assignment's scope and timeline —
  familiarity with how to brief it, review its output, and catch its mistakes
  is itself part of "good agent orchestration."

## How the Agent Was Orchestrated

The development loop followed a consistent pattern across the project's ~17
recorded commits:

1. **Spec the change in plain language** — a feature request or bug report
   was described to the agent in conversational terms (e.g. "implement
   zero-cost dynamic translations using free APIs", or later, a bug report
   with screenshots showing that switching to Chinese didn't actually change
   the displayed explanations).
2. **Let the agent investigate before writing code** — for non-trivial
   changes (especially bug fixes), the agent was directed to first read the
   relevant modules, form a hypothesis about the root cause, and explain it
   back in plain terms *before* editing anything. This caught at least one
   significant issue early: the language-switch staleness bug turned out to
   be an architectural problem (translated strings baked into
   `st.session_state` at analysis time) rather than a translation-API problem
   — a distinction that changed the entire fix.
3. **Constrain the blast radius explicitly** — instructions consistently
   included scope boundaries ("don't make large unrelated changes", "no new
   paid dependencies", "all code and comments in English", "only documentation,
   no new features"). The agent was expected to flag when a fix required
   touching more than the obvious files (e.g. the translation refactor
   required changes across `app.py`, `i18n.py`, and a new `free_translate.py`
   module) and to explain *why* before proceeding.
4. **Verify before declaring done** — for logic changes, the agent was asked
   to run lightweight verification itself (syntax checks via `ast.parse`,
   `grep` sweeps for stale references, small simulation scripts proving a
   bug-fix actually changes behaviour across a sequence of interactions)
   rather than relying solely on the human team re-testing from scratch every
   time. This is documented per-change in the commit history and was
   especially valuable for the language-switching fix, where the bug only
   manifested across *multiple* user interactions (analyse → switch language),
   which is easy to under-test manually.
5. **Human review and final sign-off on every change** — see below.

## Human Team Role and Final Review

The two-person human team (Myriam B. Guijarro Santiago and Zhentong Zhou)
retained ownership of *what* to build and *whether it was actually right*,
while delegating *how to implement it* to the agent. Concretely:

- **Product and scope decisions stayed human**: what the MVP should include,
  which business-plan features to prioritise for this stage, what the tone and
  visual identity should be, and — visible in the commit history — several
  rounds of UI/branding redesign driven by human taste and judgement rather
  than agent suggestion.
- **The agent's output was always tested against the real app, by a human, in
  the browser** — not just trusted because it compiled or passed an automated
  check. The language-switching bug, for instance, was only caught because a
  team member tested the live app (with screenshots as evidence) after an
  earlier "fix" had been marked complete; that report is what triggered the
  deeper investigation described above.
- **The team made the final call on trade-offs the agent surfaced** — for
  example, choosing the free/unofficial Google Translate endpoint as the
  default (with DeepL as an easy opt-in) was an explicit human decision after
  the agent laid out the cost/quality/reliability trade-off; similarly for UI
  decisions like removing the in-sidebar API-key input and silencing the
  "AI disabled" notice.
- **Every change was committed and reviewable** — the team kept the
  collaboration history granular and descriptive enough that it's possible to
  trace, commit by commit, which prompts produced which changes and why.

## Safety and Documentation Roles

Two responsibilities were treated as standing instructions to the agent
throughout the build, rather than one-off requests:

- **Safety / "don't break what works"**: the agent was repeatedly instructed
  to preserve specific invariants — the app must run with zero API keys, AI
  must never gate core functionality, no new *paid* dependencies, and (once
  discovered) the render-time-localisation rule that prevents the
  language-switch staleness bug from recurring. These rules were written into
  `CLAUDE.md` precisely so they'd persist across sessions and get checked
  against on every future change, rather than being re-explained — and
  potentially forgotten — each time.
- **Documentation**: the agent was responsible for keeping `CLAUDE.md`,
  `README.md`, and (for this assignment) `AGENTS.md` synchronised with the
  actual state of the code — including this very documentation pass, which
  was scoped explicitly as "documentation and assignment-readiness cleanup
  only, no new features" to keep the change reviewable and low-risk. Treating
  documentation upkeep as an explicit, recurring agent task — rather than an
  afterthought — is what keeps a fast-moving, agent-assisted codebase
  legible to both the human team and external graders.

---
name: technical-design
description: Produce an ARCHITECTURE.md for a software component by interviewing the user first and writing only what was actually decided. Covers purpose and scope, design principles, boundaries, components, data, API contract, retry, rollback, recovery, concurrency, latency, throughput, limits, security (identity, input, secrets), observability (logs, tracing), edge cases and invariants. Use whenever asked to write, generate, or update an architecture document, a technical design document, a design doc, or an ARCHITECTURE.md — for a script, CLI, service, API, library, data pipeline or Claude skill.
---

# Technical design document

Produces an `ARCHITECTURE.md` that a future engineer — or a future agent — can implement or
modify a component from, without having to guess what was intended.

The document is always written **in English**, whatever the language of the conversation.

---

## The one rule

**Write only what is known. Never invent.**

Every factual statement in the generated document must trace back to one of exactly three sources:

1. an answer the user gave during the interview,
2. a file read or a command run during grounding,
3. a documented property of a named technology (an HTTP status code, a REST endpoint, a language
   feature) — verifiable, not guessed.

Anything else is invention, and invention in an architecture document is worse than an omission: an
omission is visible, a plausible invented paragraph gets implemented.

This is not a style preference. An architecture document is read as a decision record. A section
that reads as decided but was extrapolated will be built.

### What to do instead of inventing

| Situation | What to write |
|---|---|
| The topic genuinely does not apply | `**N/A** — <why it does not apply, and what would change that>` |
| The user has not decided yet | `**Not decided** — <what is missing, and what depends on it>` |
| You inferred it rather than being told | Write it, then report it in chat at the end (never bury it) |

Never leave a heading with an empty body, and never pad a section to look complete.

---

## Workflow

Run these four phases in order. **Do not write the file before Phase 3.**

### Phase 1 — Ground

Read the project before asking anything. Questions built on real findings are answerable; generic
questions waste the user's time and produce generic documents.

Time-box this. Look for:

- `README*`, existing docs, `CLAUDE.md`
- the dependency manifest — `package.json`, `pyproject.toml`, `requirements.txt`, `*.csproj`,
  `go.mod`, `Cargo.toml`, `pom.xml`
- entry points: `main`, `__main__`, `Program.cs`, `index.*`, `bin/`, `scripts/`, `cmd/`
- configuration and environment: `.env.example`, `appsettings*.json`, `config/`, Helm/compose files
- CI: `.github/workflows/`, `azure-pipelines.yml`, `.gitlab-ci.yml`
- tests, to learn what behaviour is already pinned down
- for an empty or greenfield project: say so and interview from scratch

Also check what the environment actually provides when it will shape a decision — an installed CLI,
an available runtime, a configured credential. A question whose options are all impossible on this
machine is a wasted question.

Report what you found in two or three lines before the first question, so the user can correct a
wrong reading immediately.

### Phase 2 — Interview

Read `references/interview.md` for the question bank and the rules for asking well.

Ask with **AskUserQuestion**, in rounds of up to four questions. Between four and six rounds is
normal; more than six means the questions have stopped changing the document.

Non-negotiable during this phase:

- **Write nothing.** No file, no draft, no partial document.
- **Ground every option** in what Phase 1 found. Never offer an approach the project cannot use.
- **Give real trade-offs**, not labels. The user is choosing between consequences.
- **Always leave an escape** — an option meaning "you decide" or "not sure". When it is taken, either
  decide and flag it in chat, or record `**Not decided**`.
- **Stop when the answers stop mattering.** A question whose answers all produce the same document
  should not be asked.

### Phase 3 — Write

Read `references/sections.md` for what each section must contain, and `references/template.md` for
the skeleton.

Target: `ARCHITECTURE.md` at the project root, unless the user named another path or the component
lives in a subdirectory of a multi-component repo.

**If the file already exists**: read it first, tell the user in a few lines what would change, and
get confirmation before overwriting. Never silently replace an existing architecture document —
it may contain decisions nobody remembers making.

### Phase 4 — Verify

Re-read what you wrote against this checklist before handing it over:

- [ ] Every claim traces to an answer, a file, or a documented technology property
- [ ] No component, file, flag or field is described that does not exist and is not planned
- [ ] Every `N/A` carries a reason; every `Not decided` says what is missing
- [ ] Non-goals are stated explicitly, not merely implied
- [ ] Invariants are numbered, and each one is testable
- [ ] The edge case table gives a **behaviour** for every case, not just a name
- [ ] No secret, token, password or connection string appears anywhere
- [ ] The document is in English
- [ ] Every one of the 21 required topics has a heading

Then report in chat — not in the document:

- anything you decided rather than asked, with the reasoning, so the user can veto it
- every `Not decided` marker, as a short to-do list

---

## Required sections

All 21 topics below must have a heading in the generated file, in this order. Sections that do not
apply keep their heading and say `N/A` with a reason.

| § | Section | Answers |
|---|---|---|
| 1 | Purpose and scope | What it does, and explicitly what it does not |
| 2 | Design principles | The few rules that explain why the design looks like this |
| 3 | Boundaries | What is inside, what is outside, what it talks to and in which direction |
| 4 | Components | The parts, each with one responsibility, and who is allowed to do what |
| 5 | Data | Entities, ownership, where they live, lifecycle, schema |
| 6 | API contract | The interface: inputs, outputs, errors, versioning |
| 7 | Failure and recovery | 7.1 Retry · 7.2 Rollback · 7.3 Recovery · 7.4 Concurrency |
| 8 | Performance and limits | 8.1 Latency · 8.2 Throughput · 8.3 Limits |
| 9 | Security | 9.1 Identity · 9.2 Input · 9.3 Secrets |
| 10 | Observability | Signals and what each answers · 10.1 Logs · 10.2 Tracing |
| 11 | Edge cases | Case → behaviour, grouped by when it is caught |
| 12 | Invariants | Numbered rules a future change must not break |

---

## Reference files

Read these on demand, one at a time — not upfront.

| File | Read it when |
|---|---|
| `references/interview.md` | Starting Phase 2 — the question bank, per section |
| `references/sections.md` | Starting Phase 3 — what each section must contain, with examples |
| `references/template.md` | Writing the file — the skeleton to fill |

---

## Style

The reader is an engineer or an agent about to change the system. Write for them.

- **State decisions, and why.** "X, because Y" — the reason is what survives contact with a
  situation the document did not foresee.
- **Be concrete.** Real field names, real flags, real status codes, real paths. A document that
  could describe any system describes none.
- **Prefer tables** for anything enumerable: fields, endpoints, error classes, edge cases.
- **Record the traps.** Anything that cost time to discover — a counter-intuitive API behaviour, a
  header that must be exact, an error message that misleads — belongs in the document. This is often
  its single most valuable content.
- **No filler.** No "it is important to note", no restating a heading as a sentence, no section
  written to fill a template slot.

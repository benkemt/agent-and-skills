# agent-and-skills

A collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) built to
support an **agentic loop development process**: a chain in which each skill produces the artifact
the next one consumes, so a feature can travel from an idea to an executable backlog without a human
retyping it in between.

**The loop today** — two skills, one handoff:

```
           idea / need
                │
                ▼
   ┌──────────────────────────┐
   │     technical-design     │  interview, then write only what was decided
   └────────────┬─────────────┘
                │  ARCHITECTURE.md
                ▼
   ┌──────────────────────────┐
   │  architecture-to-ticket  │  slice into ordered, self-contained tickets
   └────────────┬─────────────┘
                │  tickets/NN-*.md
                ▼
   ┌──────────────────────────┐
   │   an agent works them    │  one ticket at a time; context stays small
   └──────────────────────────┘
```

`ado-create-items` is **not part of the loop yet** — see [Where this is going](#where-this-is-going).

---

## ⚠️ Not production ready

**Every skill in this repository is under active development.** They are experiments in my own
workflow, not released tooling. Expect breaking changes, unfinished skills, missing tests and
behaviour that changes without notice. Nothing here carries a compatibility promise — do not rely on
it for anything you cannot afford to redo.

---

## The skills

### `technical-design` — write the architecture document

Produces an `ARCHITECTURE.md` for a software component (script, CLI, service, API, library, data
pipeline, or another Claude skill) by **interviewing the user first** and writing only what was
actually decided.

It covers purpose and scope, design principles, boundaries, components, data, API contract, retry,
rollback, recovery, concurrency, latency, throughput, limits, security (identity, input, secrets),
observability (logs, tracing), edge cases and invariants.

Its governing rule is *write only what is known, never invent*: a topic that does not apply is marked
`**N/A**` with a reason, one that is undecided is marked `**Not decided**` with what is missing.
An architecture document is read as a decision record, and a plausible invented paragraph gets built.

**Use it when** you are asked to write, generate or update an architecture document, a technical
design document, a design doc, or an `ARCHITECTURE.md`.

**Files:** `SKILL.md`, plus `references/` for the interview question bank, the per-section guidance
and the document template.

---

### `architecture-to-ticket` — turn the document into a backlog

Reads an `ARCHITECTURE.md` and produces a `tickets/` directory: one numbered Markdown ticket per unit
of work, in dependency order, each self-contained enough that someone who has never read the
architecture can execute it. It finishes with a **coverage map** proving every point of the document
landed in a ticket.

Its governing rule is *every point in the architecture gets a ticket, nothing else gets one*. A missed
section never gets built; an invented ticket gets built with the same authority as the rest. Where the
document is silent the skill flags the gap in chat rather than filling it.

**Use it when** you are asked to create a task list, a ticket list, a backlog, an implementation plan
or work items from an architecture or design document.

**Files:** `SKILL.md`, plus `references/` for slicing/sizing/ordering rules and the ticket file format.

---

### `ado-create-items` — push a backlog to Azure DevOps

> **Not part of the agentic loop at the moment.** It is developed separately, and will be folded in
> later in a different role than the one it was first designed for — see
> [Where this is going](#where-this-is-going).

Creates a tree of linked work items in Azure DevOps from a `workitems.json` manifest. It guarantees
that the parent/child hierarchy is reproduced exactly, that items are created in the order the team
will execute them, and that **a run can be repeated without creating duplicates** whatever failed the
first time.

The write path is a deterministic script rather than a model turn-by-turn loop, so a failed run leaves
a state file to converge from instead of a half-created tree. The skill deliberately does not author
content, judge content quality, delete anything, or manage state transitions.

**Use it when** you have a written backlog and want it pushed into an ADO project.

> **Status: design only.** `ARCHITECTURE.md` is the finished implementation contract; the
> implementation under `scripts/` does not exist yet. Its own `tickets/` directory is generated
> locally by `architecture-to-ticket` and is git-ignored.

---

## How they are used together

The loop is the point. Each skill's output is the next skill's input, and each hands off a reviewable
file rather than conversational context:

1. **`technical-design`** interviews you and commits `ARCHITECTURE.md` — the decision record.
2. **`architecture-to-ticket`** slices that file into `tickets/NN-*.md` — the execution order, with a
   coverage map proving nothing in the document was dropped.
3. An agent works the tickets one at a time; each is self-contained, so context stays small.

Both steps can be re-run: the document is re-interviewed, the tickets are regenerated. That
replayability is what makes the loop safe to hand to an agent.

---

## Where this is going

Azure DevOps is currently outside the loop. The intended next step **reverses the direction of the
integration**: instead of the loop ending with a push to ADO, it will *start* from ADO.

The planned flow:

1. **Pull** the Features and User Stories that already exist in Azure DevOps — the team's real,
   groomed backlog, written by the people who own the product.
2. **Combine** them with the project's `ARCHITECTURE.md`. The ADO items say *what* to build and why;
   the architecture says *how* it was decided to be built. Neither is sufficient alone.
3. **Generate** the tickets from both sources together, so each ticket is grounded in a real backlog
   item rather than in a document read in isolation.
4. **Link** every generated ticket back to the ADO work item it came from, so implementation work
   stays traceable to the Feature or User Story that justified it, in both directions.

`ado-create-items` is being built with that role in mind. Its current design — a reviewable manifest,
a deterministic write path, and a state file that makes every run replayable — is the groundwork for
the read-and-link direction, not just the write one.

---

## Installing

Copy or symlink a skill directory into `~/.claude/skills/` (personal) or `.claude/skills/`
(project-scoped), then invoke it by name or let Claude pick it up from its description.

```bash
# personal, all projects
cp -r skills/technical-design ~/.claude/skills/
```

---

## Repository layout

```
skills/
├── technical-design/          # in the loop:  interview → ARCHITECTURE.md
│   ├── SKILL.md
│   └── references/            # interview.md, sections.md, template.md
├── architecture-to-ticket/    # in the loop:  ARCHITECTURE.md → tickets/
│   ├── SKILL.md
│   └── references/            # decomposition.md, ticket-format.md
└── ado-create-items/          # not in the loop yet: manifest → ADO work items
    ├── ARCHITECTURE.md        # implementation contract
    ├── .gitignore             # tickets/ are generated locally, not committed
    └── scripts/               # (not implemented yet)
```

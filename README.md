# agent-and-skills

A collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) built to
support an **agentic loop development process**: a chain in which each skill produces the artifact
the next one consumes, so a feature can travel from an idea to an executable backlog without a human
retyping it in between.

**The loop today** — three skills, two handoffs:

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
   │ ticket-to-implementation │  one ticket at a time → code, or a written gap
   └────────────┬─────────────┘
                │  code + a status: done, or need more information
                ▼
        the next ticket
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

### `ticket-to-implementation` — execute one ticket

Takes a single ticket, reads it together with the `ARCHITECTURE.md` sections it cites and the code its
dependencies produced, builds every detail of its **Job to do**, then verifies each acceptance
criterion by *running* it. It returns the ticket in one of exactly two states — `**Status:** done`
with every box ticked, or `**Status:** need more information` with the gaps written into the ticket
itself. There is no "mostly done".

Its governing rule is *never assume*: anything the ticket and the architecture leave unsettled that is
visible from outside the code — a name another ticket will call, a format, a message, an exit code, a
stored value — stops the run instead of being guessed. A guess is indistinguishable from a decision
once it is in the code. Choices that stay internal to the module are made and recorded in a comment.

The second rule is that *`done` is a claim about reality, not about effort*: it may only be written
after the commands that prove it have run. Blocking questions go in the file rather than in chat, so
the next run starts from the ticket and not from a lost transcript.

**Use it when** you are asked to implement, do, execute or finish a ticket, a task file or a backlog
item — or are handed a path to a numbered ticket.

**Files:** `SKILL.md`, plus `references/` for the blocker-versus-judgment test and the status header,
checkbox and blocking-comment formats.

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

> **Status: in progress, and the loop's first subject.** `ARCHITECTURE.md` is the finished
> implementation contract; `scripts/` is being built from it one ticket at a time by
> `ticket-to-implementation`. The schema, the example manifest and the CLI skeleton exist — the
> pipeline stages behind them are still stubs. Its own `tickets/` directory is generated locally by
> `architecture-to-ticket` and is git-ignored.

---

## How they are used together

The loop is the point. Each skill's output is the next skill's input, and each hands off a reviewable
file rather than conversational context:

1. **`technical-design`** interviews you and commits `ARCHITECTURE.md` — the decision record.
2. **`architecture-to-ticket`** slices that file into `tickets/NN-*.md` — the execution order, with a
   coverage map proving nothing in the document was dropped.
3. **`ticket-to-implementation`** works them one at a time, each in its own context, and stamps the
   ticket `done` or `need more information` when it finishes.

Every step can be re-run: the document is re-interviewed, the tickets are regenerated, a blocked
ticket is answered and run again. That replayability is what makes the loop safe to hand to an agent.

The three skills share one rule, which is the reason the chain holds: **each writes only what it was
given, and marks what it was not.** `technical-design` marks an undecided topic rather than inventing
a decision; `architecture-to-ticket` reports a gap rather than inventing a ticket;
`ticket-to-implementation` stops on a silence rather than inventing a contract. An invention anywhere
in the chain is indistinguishable from a decision by the time it reaches the code, so each step hands
the question back to you instead of resolving it quietly.

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
├── ticket-to-implementation/  # in the loop:  one ticket → code, or a written gap
│   ├── SKILL.md
│   └── references/            # clarity-gate.md, status-and-comments.md
└── ado-create-items/          # not in the loop yet: manifest → ADO work items
    ├── ARCHITECTURE.md        # implementation contract
    ├── .gitignore             # tickets/ are generated locally, not committed
    ├── assets/                # workitems.example.json
    └── scripts/               # apply.py, schema.json — built ticket by ticket
```

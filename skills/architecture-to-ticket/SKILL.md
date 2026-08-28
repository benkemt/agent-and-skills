---
name: architecture-to-ticket
description: Turn an ARCHITECTURE.md into an executable backlog — one numbered Markdown ticket per unit of work, in dependency order, inside a tickets/ directory, with a coverage map proving every point of the document has a ticket. Use whenever asked to create a task list, a ticket list, a backlog, an implementation plan or work items from an architecture document, a technical design document or a design doc.
---

# Architecture to tickets

Reads an `ARCHITECTURE.md` and produces `tickets/` — one Markdown file per unit of work, numbered in
the order they must be executed, each self-contained enough that someone who has not read the
architecture can execute it.

The tickets are always written **in English**, whatever the language of the conversation.

---

## The one rule

**Every point in the architecture gets a ticket. Nothing else gets one.**

Two failures, both fatal:

- **A missed point.** A section, a table row, an edge case or an invariant with no ticket will not be
  built. The document said it and the backlog dropped it — nobody notices until production does.
- **An invented point.** A ticket for work the architecture never asked for gets built with the same
  authority as the rest. An architecture document is a decision record; the backlog must not add
  decisions to it.

The skill is **done only when the coverage map (Phase 4) accounts for every point of the document**.
Not "most sections". Every numbered section, every row of every edge-case table, every numbered
invariant.

### When the architecture is silent

The document will have holes. Do not fill them.

| Situation | What to do |
|---|---|
| A point is stated but the how is unspecified | Write the ticket; state the choice as an open decision in its **Job to do**, with a recommendation |
| The document contradicts itself | Write the ticket, quote both readings, and flag it in chat |
| Work is obviously needed but nowhere in the document | Do **not** invent a ticket. Report it in chat as a gap for the user to decide on |

Flag every one of these in chat at the end. Never bury them in a ticket file.

---

## Workflow

Four phases, in order. **Do not write a ticket file before Phase 3.**

### Phase 1 — Locate

Find the architecture document, without asking if you can avoid it:

1. `ARCHITECTURE.md` in the current working directory.
2. If absent, search one to two levels down (`*/ARCHITECTURE.md`, `*/*/ARCHITECTURE.md`), and check
   the usual alternates: `docs/ARCHITECTURE.md`, `DESIGN.md`, `TECHNICAL-DESIGN.md`.
3. **Several matches** — ask with AskUserQuestion which one to work from. Never process more than one
   per run; two architectures produce two independent backlogs.
4. **No match** — stop and say so. Offer the `technical-design` skill, which writes the document this
   one consumes.

The user may also name a path directly; that always wins over the search.

**Output location:** `tickets/`, as a **sibling of the architecture file** — an architecture at
`skills/foo/ARCHITECTURE.md` produces `skills/foo/tickets/`. If `tickets/` already exists and is not
empty, read it first, say in a few lines what would change, and get confirmation before overwriting.

### Phase 2 — Inventory

Read the whole document, then build a checklist **before slicing anything**. Enumerate, at the
finest granularity the document uses:

- every numbered section and sub-section;
- every row of every table — field tables, endpoint tables, retry tables, mapping tables;
- every edge case, with its stated behaviour;
- every numbered invariant;
- every explicitly stated non-goal (these become constraints inside tickets, never tickets of their
  own);
- every "trap" the document records — a header that must be exact, a counter-intuitive API
  behaviour, a misleading error message. These are the highest-value content in the document and the
  first thing lost in a careless decomposition.

Keep the checklist. Phase 4 checks against it, and it is what the coverage map is built from.

### Phase 3 — Slice, order, write

Read `references/decomposition.md` for the slicing and ordering rules, and
`references/ticket-format.md` for the ticket skeleton and the index skeleton.

Slice into tickets, order them by dependency, then write:

```
tickets/
  README.md                       # the index: order table, parallel tracks, coverage map
  01-<kebab-slug>.md
  02-<kebab-slug>.md
  …
```

Numbers are **two-digit, zero-padded, in execution order**, and are the ticket's identity — a ticket
is referred to as "ticket 14" everywhere.

**Write the tickets first, `README.md` last.** The index's coverage map can only be honest once the
tickets exist.

### Phase 4 — Verify coverage

Re-read the generated backlog against the Phase 2 checklist. The skill is not done until all of
these hold:

- [ ] Every item on the Phase 2 checklist appears in the coverage map, against a real ticket number
- [ ] Every numbered invariant is covered, and each has a ticket that makes it *verifiable*
- [ ] Every edge-case row is covered by a ticket that states its behaviour
- [ ] Every ticket has a **Job to do** an implementer can execute without opening the architecture
- [ ] Every ticket has acceptance criteria that are checkable, not aspirational
- [ ] Every dependency named in a ticket points at a lower number, and the graph is acyclic
- [ ] No ticket describes work the architecture does not ask for
- [ ] Every recorded trap survives into the ticket that needs it
- [ ] The numbering is contiguous from 01, with no gaps and no duplicates

Then report in chat — not in the files:

- gaps: work the document does not cover, for the user to decide on;
- contradictions found, with both readings;
- any judgment call you made that the architecture did not settle, so the user can veto it.

---

## Reference files

Read on demand, not upfront.

| File | Read it when |
|---|---|
| `references/decomposition.md` | Starting Phase 3 — how to slice, size and order tickets |
| `references/ticket-format.md` | Writing the files — the ticket and index skeletons |

---

## Style

The reader is the person or agent who will execute the ticket, and they will not read the
architecture first. Write for them.

- **Lift the specifics.** Copy the relevant table, payload, message format or exit code **into** the
  ticket. A ticket that says "implement retries per §8.1" forces a document round-trip; a ticket
  carrying the retry table does not.
- **Cite anyway.** Every ticket names the sections it implements, so the rationale is one click away.
- **One deliverable per ticket.** If the goal needs the word "and" twice, it is two tickets.
- **Acceptance criteria are checkable.** "Handles errors" is not a criterion. "A simulated 429 with
  `Retry-After: 2` waits ~2s and retries, up to 5 attempts" is.
- **State the why when the document does.** A rule with its reason survives a situation the document
  did not foresee; a bare rule gets "simplified" away.
- **No filler.** No estimates, no story points, no sprint assignment, no priority field — the
  architecture does not know those and neither do you.

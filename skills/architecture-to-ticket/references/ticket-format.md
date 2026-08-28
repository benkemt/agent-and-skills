# Ticket and index format

Read while writing the files in Phase 3.

---

## File naming

```
tickets/
  README.md                 # the index — written last
  01-scaffold-structure.md
  02-json-schema.md
  …
  27-invariant-test-suite.md
```

- Two-digit zero-padded prefix, contiguous from `01`, in execution order.
- Then a kebab-case slug naming the deliverable — `09-http-client-and-retry.md`, not
  `09-ticket-nine.md`. The filename is read far more often than the file.
- Numbers are identity: once written, a ticket is "ticket 09" in every dependency line and in the
  coverage map. Do not renumber to insert work; append, and let the dependency line carry the order.

---

## Ticket skeleton

````markdown
# NN — <deliverable, as a noun phrase>

**Depends on:** <ticket numbers, or `—`>
**Reference:** ARCHITECTURE.md §X.Y (<section name>), §Z (<section name>)

## Goal

One or two sentences: what this delivers, and why it exists. If the architecture gives a reason —
"ADO's default backlog rank follows creation order, so this is a stated requirement, not a nicety" —
that reason belongs here.

## Job to do

The executable description. Numbered steps for a sequence, tables for anything enumerable, fenced
blocks for exact formats. Lift the specifics from the architecture: the real field names, the real
payload, the real message strings.

Call out the traps inline, with their reason:

- **`Hierarchy-Reverse` points to the parent** and is posted from the child. The forward direction
  would require patching an already-created item — two calls instead of one.

State the constraints that bound this ticket — the invariant it must not break, the non-goal it must
respect — rather than assuming the implementer read §1.

Where the architecture left a choice open, say so and recommend one:

> The document does not say whether X or Y. Use X — <reason>. Record the choice in a comment.

## Acceptance criteria

- [ ] Concrete, checkable statement
- [ ] The specific failure named by the document, with its exit code
- [ ] A negative check — what must not happen
- [ ] The invariant this ticket could break
````

**Sections are fixed.** Same five parts, same order, every ticket. A reader who has done one ticket
knows where to look in all the others. Add nothing — no estimate, no priority, no assignee, no
status field: a Markdown file in git is not an issue tracker, and half-maintained metadata is worse
than none.

---

## Index skeleton — `tickets/README.md`

Written last, once every ticket exists. Four parts, in this order.

### 1. Header

Two or three lines: what these tickets build, that they are numbered in execution order, that each
is self-contained, and a link back to `../ARCHITECTURE.md` as the contract they implement.

### 2. Order of execution

One row per ticket — the whole backlog on one screen:

```markdown
| # | Ticket | Depends on | Delivers |
|---|---|---|---|
| 01 | [Scaffold the structure](01-scaffold-structure.md) | — | file tree, dependency stance |
| 02 | [Write `schema.json`](02-json-schema.md) | 01 | JSON Schema for the manifest |
```

`Delivers` is a few words naming the artifact or behaviour — not a restatement of the title.

### 3. Parallel tracks

Two or three lines naming which tickets are strictly serial and which tracks can run at the same
time, with the ticket where they converge:

```markdown
Tickets 01–04 are the only strictly serial run. After that, three tracks progress in parallel and
meet at 18:

- **validation** 05 → 06 → 07
- **transport** 08 → 09 → 10
- **state** 11 → 12 → 13 → 14
```

### 4. Coverage map

**This is the part that proves the skill is done.** One row per point of the architecture, mapped to
the tickets covering it:

```markdown
| ARCHITECTURE.md | Covered by |
|---|---|
| §1 Purpose and scope, non-goals | 05, 14, 18, 26 |
| §4.4 Hierarchy rules | 07, 20 |
| §8.1 Retry policy | 09 |
| §10 Edge cases — validation | 06, 07, 27 |
| §11 Invariants 1–11 | 27 (each one an executable test) |
```

Rules:

- **Every** numbered section appears, including rationale sections — those map to the tickets they
  constrain, which is how a reader checks the constraint was carried through.
- A long edge-case table is split by its own grouping (caught at validation / before creation /
  at runtime), never collapsed into one row.
- Invariants get a row saying which ticket makes them **verifiable**, not merely which ticket
  happens to obey them.
- A section with an empty right-hand column is a bug. Fix the backlog, not the map.

---

## Wording

- Present tense, imperative: "Compute the hash", not "The hash will be computed".
- The reader is an implementer, not a stakeholder. No business justification, no benefit statements.
- Quote the document's own wording for anything normative — a rule reworded is a rule
  reinterpreted.
- Keep a ticket under roughly 80 lines. Longer usually means it is two tickets.

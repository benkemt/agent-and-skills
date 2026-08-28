---
name: ticket-to-implementation
description: Execute one implementation ticket end to end — read the ticket and the ARCHITECTURE.md it cites, build every detail it specifies, verify every acceptance criterion by running it, then mark the ticket done; or stop before writing code and record inside the ticket what is missing. Use whenever asked to implement, do, execute, work or finish a ticket, a task file or a backlog item, or when handed a path to a numbered ticket Markdown file.
---

# Ticket to implementation

Takes **one ticket** and returns it in one of exactly two states:

| End state | Meaning |
|---|---|
| `**Status:** done` | Every detail of **Job to do** is built, and every acceptance criterion was verified by a command that ran |
| `**Status:** need more information` | The ticket does not say enough; the gap is written into the ticket and nothing was guessed |

There is no third outcome. Not "mostly done", not "done with caveats", not a silent partial commit.
A ticket left in any other state is the skill failing, not finishing.

---

## The two rules

**1. Never assume.** The ticket and the architecture are the only sources of truth. Anything they do
not settle and that changes observable behaviour is a stop, not a guess. A guess is indistinguishable
from a decision once it is in the code — the next reader will build on it as if someone chose it.

**2. `done` is a claim about reality, not about effort.** Write it only after running the checks. If
an acceptance criterion cannot be executed as written, the ticket is `need more information` — say
which criterion and why.

Corollary: **the acceptance criteria are the floor, not the ceiling.** A ticket whose criteria all
pass but whose **Job to do** has an unimplemented paragraph is not done. Implement the job; the
criteria only prove it.

---

## Workflow

Six phases. **Phase 2 gates Phase 3 — no code before the clarity gate passes.**

### Phase 0 — Locate the ticket

The input may be a path, a number (`04`), a slug (`cli-skeleton`), or a description.

1. A path given by the user always wins.
2. Otherwise glob `**/tickets/NN-*.md` and match on number, then on slug.
3. **Several matches** — ask with AskUserQuestion which one. Never implement two tickets in one run
   unless the user named several; then run them in dependency order and **stop the chain at the
   first ticket that blocks**, leaving the rest untouched.
4. **No match** — say so and stop. Do not invent a ticket.

### Phase 1 — Read for the contract

Read, in this order, before deciding anything:

- **the whole ticket**, including every acceptance criterion;
- **the sections it cites** in `ARCHITECTURE.md` (the `**Reference:**` line). Read them in full, not
  just the quoted extract — the ticket lifts specifics, the architecture holds the rationale and the
  invariants;
- **the invariants section** of the architecture, always, whether or not the ticket cites it;
- **the tickets it depends on**, and the code they produced. What already exists sets the
  conventions this ticket must match — file layout, error handling, naming, dependency stance.

If a dependency's deliverable is **absent from the code**, stop and report it in chat. That is a
sequencing problem, not missing information — it does not belong in the ticket file, and a status
line that lags behind the code is not evidence either way.

### Phase 2 — The clarity gate

Before writing a line of code, walk **every sentence of Job to do and every acceptance criterion**
and ask of each: *can I build exactly this, without inventing a fact?*

Read `references/clarity-gate.md` — it draws the line between a **blocker** (stop) and a **routine
implementation judgment** (proceed, and record the choice in a code comment). The short form:

> A gap is a blocker when the ticket and the architecture give no basis to choose, **and** the choice
> is visible from outside the code — a name in an interface, a format, a message, an exit code, an
> order of operations, a stored value. If the choice is invisible outside the module, it is yours to
> make.

If anything blocks, go to Phase 5 with `need more information`. Do not implement the unblocked half
first "to save time" — a half-built ticket read as done is the failure this gate exists to prevent.

### Phase 3 — Implement

Build every detail the ticket specifies, in the ticket's own terms.

- **Stay inside the fence.** Implement this ticket, not the next one. Where the ticket says stub,
  stub — and name the ticket that fills the stub in the docstring or comment.
- **Match the surrounding code.** Same idiom, same comment density, same error style, same
  dependency stance as the code the dependencies produced.
- **Carry the rationale.** Where the architecture gives a reason for a rule, put the reason in the
  code as a short comment. A rule with its reason survives a refactor; a bare rule gets "simplified"
  away.
- **Respect the invariants and non-goals** named in the architecture, including ones the ticket does
  not repeat.
- Never edit `ARCHITECTURE.md`. It is the contract, and this skill is the implementer of it. If the
  architecture looks wrong, say so in chat and keep building to it.
- Never edit another ticket, renumber tickets, or reword this ticket's requirements to match what
  you built.

If a blocker only becomes visible mid-implementation, stop there. Keep the work that is
unambiguously specified, leave the ambiguous part **unwritten** — never a guessed placeholder — and
go to Phase 5 with `need more information`, stating exactly what is built and what is not.

### Phase 4 — Verify

Take each acceptance criterion in turn and **run something that proves it**. Reading the code back
is not verification.

- A criterion about an exit code: run the command, check `$?`.
- A criterion about output: run it, read the output.
- A criterion about a file or a function existing: import it, call it, list it.
- A criterion phrased as a negative ("must not create anything"): run it and check nothing appeared.
- A criterion needing credentials or a live service that is not available: **that ticket is not
  done.** Record it as a blocker in Phase 5 rather than declaring it passed by inspection.

Then re-read **Job to do** line by line against the diff. Every instruction, table row and named
behaviour must map to something you wrote. This catches the detail that no acceptance criterion
happened to cover — the most common way a ticket is falsely closed.

### Phase 5 — Close the ticket

Read `references/status-and-comments.md` for the exact formats. In short:

**All criteria verified and every detail built** → add `**Status:** done` as the first metadata line
under the title, and tick every `- [ ]` to `- [x]`.

**Anything unbuilt, unclear or unverifiable** → add `**Status:** need more information`, leave the
checkboxes unticked, and append a `## Need more information` section that, for each gap, names where
in the ticket it sits, quotes what the ticket says, states what is missing, and says what answer
would unblock it. Questions must be answerable — "what should the timeout be?" not "please clarify".

Then report in chat: what was built, the command output that proves each criterion, and any routine
judgment call you made so the user can veto it.

---

## Re-running a blocked ticket

A ticket already marked `need more information` is the normal input to a second run.

1. Read the existing `## Need more information` section first — it is the agenda.
2. Check each question against the ticket body, the architecture and what the user said in chat.
3. **Any answer that arrived in chat gets folded into Job to do**, in the ticket's own voice, before
   implementing. The ticket must stay self-contained; an answer that lives only in a transcript is
   lost.
4. Still-open questions stay in the section. Delete the whole section only when every question is
   resolved, in the same edit that sets `**Status:** done`.

---

## Reference files

Read on demand, not upfront.

| File | Read it when |
|---|---|
| `references/clarity-gate.md` | Phase 2 — blocker versus routine judgment, with worked examples |
| `references/status-and-comments.md` | Phase 5 — exact status header, checkbox and comment formats |

---

## Anti-patterns

Each of these has produced a falsely closed ticket:

- **Ticking a box because the code looks right.** Run it.
- **Implementing the acceptance criteria only.** They are a test, not a specification.
- **Filling a silence with a sensible default.** Sensible to whom, and checked against what?
- **Widening the ticket** because an adjacent improvement was obvious. Note it in chat; leave it out.
- **Narrowing the ticket** because part of it was awkward. Build it, or block on it — not neither.
- **Writing the blocker into chat only.** The next run starts from the file, not the transcript.
- **Editing the ticket's requirements** so the built code matches. The ticket is the input.
- **Leaving a stub that pretends to work.** A stub is labelled with the ticket that fills it.

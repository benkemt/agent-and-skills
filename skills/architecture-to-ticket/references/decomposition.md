# Decomposition — slicing, sizing and ordering

Read at the start of Phase 3, once the Phase 2 inventory exists.

---

## 1. What one ticket is

**One ticket = one deliverable that can be executed and verified on its own.**

Test it three ways:

- **Executable** — someone can start it on a Monday morning with the ticket alone and know when they
  are finished.
- **Verifiable** — its acceptance criteria can be checked without executing the next ticket.
- **Single** — the goal fits in one sentence with no more than one "and".

Too big: *"Implement the API client and the retry policy and the authentication"*. Three concerns,
three failure modes, three reviewers. Split it.

Too small: *"Add the `--verbose` flag to argparse"*. That is a line inside the CLI ticket. A ticket
whose acceptance criteria are one checkbox is a checkbox.

The right size is usually **a few hours to two days** of work. If the architecture is 700 lines,
expect 20–30 tickets; if it is 150, expect 6–10. Do not pad to reach a number.

---

## 2. Where the seams are

Cut along the document's own structure, in this order of preference:

| Seam | Becomes |
|---|---|
| A file listed under **Components** | One ticket per artifact — the schema, the example asset, the entry-point doc |
| A stage in an **execution model** or pipeline diagram | One ticket per stage: validate, authenticate, pre-check, reconcile, plan, execute, report |
| A **contract** — schema, CLI surface, wire format | Its own ticket, always *before* anything that consumes it |
| A **cross-cutting mechanism** — retry, logging, locking, hashing | Its own ticket, so it is implemented once instead of five times |
| A **flag** with real behaviour behind it (`--update`, `--rebuild-state`, `--only`) | One ticket each — they are independently shippable and independently breakable |
| A **section that is pure rationale** (design principles, non-goals) | **No ticket.** These are constraints; carry them into the tickets they constrain |
| **Invariants** | Normally no ticket of their own — each is enforced inside the ticket that can break it, then all of them are pinned by the final test ticket |
| **Edge cases** | Rarely a ticket of their own — attach each to the stage that catches it, and mark the whole table covered by the test ticket |

Two rules that keep the seams honest:

- **A stage in a diagram is a ticket, not a phase of the project.** The diagram is already a
  dependency graph — use it.
- **Do not split by file.** Two functions in the same file can be two tickets; one function spanning
  two concerns is still two tickets.

---

## 3. Ordering

Number in the order the work must actually happen. The rules, in priority order:

1. **Scaffolding first.** The directory tree and the entry-point skeleton, so every later ticket has
   a place to put its code.
2. **Contracts before consumers.** The schema before the validator. The CLI surface before the
   stages that hang off it. The payload builder before the executor that posts it.
3. **Read paths before write paths.** Validation, authentication, pre-checks and planning all precede
   the first ticket that writes anything. This also means the backlog can be executed halfway and
   still be safe.
4. **Pure functions before the code that calls them.** Hashing, field mapping, HTML conversion — no
   I/O, trivially testable, and everything downstream depends on them.
5. **The happy path before its variations.** Create before update. The default run before `--only`.
   Success reporting before failure recovery, unless the failure path shares the same code.
6. **Recovery and diagnostics after the thing they recover.** `--rebuild-state` needs something to
   rebuild from.
7. **Model-facing or user-facing docs late** — they describe finished behaviour, so writing them
   early guarantees a rewrite.
8. **The test/verification ticket last.** It depends on everything.

**Dependencies must point backwards.** Every "Depends on" names a strictly lower number. If two
tickets genuinely need each other, they are one ticket, or the seam is in the wrong place.

**A forward reference is allowed in exactly one case:** a pure function whose exact shape is settled
by a later ticket (a hash that must cover post-conversion values, for instance). Say so explicitly in
the dependency line and keep the numbering by execution order.

### Parallel tracks

Real backlogs are not a single chain. After the scaffolding tickets, look for independent tracks —
typically *validation*, *transport/IO*, and *state* — that progress in parallel and converge at the
first ticket that writes. Name them in the index; it is the most useful thing the index tells a team.

---

## 4. What goes inside a ticket

The implementer will not open the architecture. Lift what they need:

**Always lift:**

- the exact table the ticket implements — field mappings, retry rules, exit codes, hierarchy rules;
- the exact wire format — a sample request body, a sample output block, byte-for-byte;
- the exact message or format strings the document specifies;
- **every trap** the architecture recorded that touches this ticket, with its reason:
  *"`Content-Type: application/json-patch+json` — not a typo and not optional; `application/json`
  returns a confusing 400."* A trap dropped from a ticket will be rediscovered at the same cost the
  document paid to record it.

**Always cite:** the section numbers, on a `**Reference:**` line, so rationale is reachable.

**Never lift:** the rationale essays. Cite them. A ticket is an instruction, not a copy of the
document.

**Carry the constraints:** if a non-goal or an invariant bounds this ticket, state it inside the
ticket — *"the skill never deletes a work item (Invariant 10)"* — rather than trusting the
implementer to have read §1.

---

## 5. Acceptance criteria

Every ticket ends with a checkbox list. Each box is a check someone can perform.

| Weak | Strong |
|---|---|
| Validation works | A manifest with three distinct schema errors prints three lines and exits 2 |
| Retries are handled | A simulated `429` with `Retry-After: 2` waits ~2s and retries, up to 5 attempts |
| State is safe | Killing the process mid-write leaves the previous state intact and parseable |
| Ordering is correct | Every parent precedes its children for a randomly shuffled input array |

Aim for **four to eight** boxes. Include, where the architecture implies them:

- the happy path, with a concrete input and its expected output;
- the specific failure the document names, with its exit code or status;
- any negative check — something that must **not** happen (no write in a dry run, no token in a log,
  no delete anywhere);
- the invariant this ticket could break.

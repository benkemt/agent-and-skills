# Interview — question bank

Read at the start of Phase 2. This is a bank to draw from, not a script to read out. Pick the
questions that will actually change the document for *this* project, and skip the rest.

---

## How to ask

**Batch into rounds of up to four.** One `AskUserQuestion` call per round, grouped by theme so the
user stays in one mental context.

**Ground every option in Phase 1.** If the project is a Python CLI with no HTTP server, do not offer
"REST endpoint versioning" as an option. If `az` is installed and logged in, an auth option that uses
it is real; one requiring a PAT the user does not have is noise.

**Options are consequences, not labels.** Each option's description says what the user is signing up
for — what gets easier, what gets harder, what breaks later. Two options that differ only in name are
one question wasted.

**Two to four options.** More than four is a menu, not a decision.

**Always leave an escape.** "You decide / not sure", "Doesn't apply here". When taken:

- if a defensible default exists, decide it, write it, and flag it in chat at the end;
- if not, record `**Not decided**` in that section and list it in the to-do at the end.

**Use previews for anything concrete.** A snippet of the manifest, the log line, the error shape, the
directory tree. People choose better when they can see the result. Previews work on single-select
questions only.

**Stop when answers stop mattering.** Before asking, complete this sentence: "depending on the
answer, the document will say ___ instead of ___". If you cannot, do not ask.

---

## Round 1 — Foundations

Almost always worth asking. These shape every later section.

| Ask about | What you are trying to settle |
|---|---|
| **What the component is** | Script, CLI, service, API, library, pipeline, skill, job. Determines which later rounds are relevant at all. |
| **Who or what invokes it** | A human at a terminal, another service, CI, a schedule, an agent. Drives §6 API contract and §8 performance. |
| **Non-goals** | The most valuable answer in the whole interview and the one nobody volunteers. Ask directly: what should this explicitly *not* do? |
| **What it talks to** | Databases, APIs, queues, filesystems, external SaaS. Populates §3 boundaries and most of §11 edge cases. |

Good non-goals question shape: offer plausible adjacent capabilities and let the user exclude them —
"does it also delete?", "does it also author content?", "does it manage state transitions?".

---

## Round 2 — Contract and data

| Ask about | What you are trying to settle |
|---|---|
| **The interface** | CLI flags, HTTP routes, function signatures, message shapes. Ask for the real names. |
| **Inputs and where they come from** | Files, arguments, environment, request bodies, config. Which are required. |
| **Outputs and error shape** | Exit codes, status codes, the error object's structure, human vs machine-readable output. |
| **The data it owns** | Which entities it creates, which it merely reads, which it must never modify. Ownership is the question, not storage. |
| **Where data lives and for how long** | Database, file, memory, external system. Retention, and whether anything must be committed to git alongside. |
| **Schema and change** | Where the schema is defined, whether it is versioned, what happens to old data on change. |

If a component has no persistent data at all, say so once and skip the rest of §5 — do not ask three
questions to establish nothing.

---

## Round 3 — Failure, concurrency, recovery

The section users have thought about least, and the one that costs most when it is missing.

| Ask about | What you are trying to settle |
|---|---|
| **What happens on partial failure** | Stop / continue / roll back. Whether partial work is left behind, and whether that is safe. |
| **Which failures are retried** | Per class: timeouts, 5xx, rate limits, auth expiry, validation errors. And explicitly which are *never* retried. |
| **Whether undo is possible** | Real rollback, compensating action, or neither. If neither, what is guaranteed instead — usually convergence on re-run. |
| **Recovery procedure** | After a crash, a lost state file, a corrupted output: what does an operator actually do? |
| **Concurrency** | Can two instances run at once? Against the same target? What is shared, what is locked, what is idempotent. |

Useful framing that surfaces real answers: *"item 7 of 20 fails — what should happen?"* Concrete
beats abstract; people who cannot define a retry policy in the abstract answer this one instantly.

If the answer to rollback is "we can't", that is a real answer and belongs in the document with its
reason. It is not a gap.

---

## Round 4 — Security

| Ask about | What you are trying to settle |
|---|---|
| **Identity** | What principal it runs as; how it authenticates to each dependency; how a caller authenticates to it; authorization rules. |
| **Trust boundaries** | Which inputs are untrusted. Anything crossing a process, network or user boundary is untrusted by default. |
| **Input handling** | Validation location and strictness; injection surfaces (SQL, shell, path traversal, template, deserialization); what happens to invalid input. |
| **Secrets** | Which exist, where they come from, their lifetime, and where they must never appear — logs, error messages, state files, git, terminal output. |

Ask the "must never appear" question explicitly. It produces an invariant, and invariants about
secrets are the ones most worth having written down.

---

## Round 5 — Performance, limits, observability

Often the shortest round. Many components have no performance requirement, and saying so is fine.

| Ask about | What you are trying to settle |
|---|---|
| **Latency** | Is there a target or an expectation? What dominates the time — network, disk, compute, a human? |
| **Throughput** | Expected volume and shape: items per run, requests per second, batch size, parallelism. |
| **Limits** | Hard numbers: max input size, quotas, rate limits imposed by dependencies, timeouts, cardinality bounds. |
| **Logs** | Format (structured or plain), levels, what is logged at each, what is never logged. |
| **Tracing and correlation** | Whether there is a correlation or trace ID, whether it propagates across boundaries, or whether there is nothing. |
| **Other signals** | Metrics, health checks, alerts — and what question each is meant to answer. |

"No latency target — it runs when a human asks and takes as long as it takes" is a legitimate answer.
Write it as an `N/A` with that reason rather than inventing a number.

---

## Round 6 — Edge cases and invariants

Do not ask "what are the edge cases?". Nobody can answer that cold. Instead, propose the ones the
earlier rounds implied and ask the user to confirm, correct, or add:

> "From what you've described I'd document these: duplicate id in the input, a parent referencing an
> unknown id, the auth token expiring mid-run, the state file missing while the items exist. Which
> are wrong, and what am I missing?"

Same for invariants. Draft them from the decisions already made and put them up for confirmation:

> "These read as the rules a future change must not break — the script is the only writer, nothing is
> written unless validation passed, secrets never reach the state file. Correct? Anything else?"

This round often needs no `AskUserQuestion` at all — a plain proposal in chat gets a better answer,
because the user is correcting a concrete list rather than generating one.

---

## Questions worth asking in almost every interview

Whatever the project:

- **"What should this explicitly not do?"** — fills the non-goals list, which prevents more wasted
  work than any other section.
- **"What already cost you time to figure out?"** — surfaces the traps: the misleading error, the
  header that must be exact, the API that succeeds but silently does nothing. This is the content a
  reader cannot get anywhere else.
- **"What would you not want a future change to break?"** — writes §12 for you.
- **"What is currently undecided?"** — gives the `Not decided` markers honestly, instead of you
  filling them in.

# Sections — what each one must contain

Read at the start of Phase 3. For each section: the question it answers, what makes it good, and
what to avoid. Examples are drawn from real documents; adapt, do not copy.

A section that does not apply keeps its heading and reads:

```markdown
**N/A** — <why it does not apply, and what would change that>
```

A section the user has not decided reads:

```markdown
**Not decided** — <what is missing, and what depends on it>
```

---

## 1. Purpose and scope

**Answers:** what is this, and what is it deliberately not?

Two or three sentences on what the component does, then a numbered or bulleted list of what it
guarantees. Then a **Non-goals** subsection, always present.

Non-goals are the highest-value paragraph in the document. They prevent the scope creep that a
reader would otherwise assume is intended, and they answer "why doesn't it also…" before it is asked.

> **Good** — "The skill does not author content: titles and descriptions arrive already written. It
> does not delete: no work item is ever removed or moved to the recycle bin."

Avoid: describing the technology instead of the purpose ("a Python script using requests").

---

## 2. Design principles

**Answers:** why does this design look like this and not some other way?

Three to five principles. Each is a bolded claim followed by two or three sentences of reasoning.
The test: a principle must be able to *settle an argument* about a future change. If it cannot, it is
a platitude and does not belong.

> **Good** — "**The write path is a script, not a model.** Creating an item and attaching its parent
> is deterministic work. Driving it turn-by-turn through an LLM means accepting a half-created tree
> whenever a call fails, with no way to know what was written."

> **Bad** — "We value simplicity and maintainability." Settles nothing.

---

## 3. Boundaries

**Answers:** where does this system stop?

Three things:

- **Inside** — what this component owns and can change.
- **Outside** — adjacent systems it depends on but does not control, and what it assumes about each.
- **Direction** — who calls whom. A diagram helps here more than anywhere else in the document.

Also name **trust boundaries**: which crossings involve data that cannot be trusted. This connects
directly to §9.2 and stops that section being written in the abstract.

Do not restate §4 here. Boundaries are about the perimeter; components are about the interior.

---

## 4. Components

**Answers:** what are the parts, and who is allowed to do what?

A directory tree or a component table, with **one line of responsibility per part**. If a line needs
"and", the component may be doing two things.

State the privilege rules explicitly — which component is allowed to write, which is read-only, which
is the only one permitted to touch a given resource. These become invariants in §12.

> **Good** — "`apply.py` — the only component that writes to ADO."

Keep runtime artifacts separate from source files if the distinction is not obvious: a reader needs
to know which files exist in the repo and which appear at runtime.

---

## 5. Data

**Answers:** what data exists, who owns it, how long does it live?

- **Entities** — what they are, and which the component *owns* versus merely reads. Ownership is the
  question that matters; storage is a detail.
- **Location and format** — file, table, external system, memory. Where the schema is defined.
- **Lifecycle** — created when, updated when, deleted never or when. Retention. Whether it belongs in
  version control.
- **Change** — is the schema versioned? What happens to existing data when it changes?
- **Integrity** — atomic writes, partial-write behaviour, what makes a record trustworthy.

If the component holds no state, say so in one line with the reason and move on.

---

## 6. API contract

**Answers:** how is it called, what comes back, what does failure look like?

The interface, in whatever form it takes — CLI flags, HTTP routes, function signatures, message
schemas. Use a table. Include:

- **Inputs** — required vs optional, source, defaults. State when there is deliberately no default.
- **Outputs** — success shape, and the machine-readable form if one exists.
- **Errors** — exit codes or status codes, the error object's structure, which are retryable.
- **Compatibility** — what callers may rely on, and what may change without notice.

Show a real example of each: a real command, a real request, a real response. Real beats abstract in
every case.

> Worth stating explicitly where it applies: "`--dry-run` or `--apply` is mandatory; invoked with
> neither, it exits 4. Defaulting either way is wrong: defaulting to apply invites accidental writes,
> defaulting to dry-run invites 'I thought it had run'."

---

## 7. Failure and recovery

### 7.1 Retry

A table: failure class → behaviour. Cover at minimum the ones that apply among: timeouts, connection
errors, `429`/rate limiting, `5xx`, `401` auth expiry, `403`, `4xx` client errors.

For each: retry or not, how many attempts, what backoff, and — where it applies — whether a
server-supplied hint such as `Retry-After` is honoured.

State the **never retried** classes explicitly and why. A validation error does not resolve itself,
and retrying it wastes a quota that a genuine transient failure will need.

### 7.2 Rollback

Whether partial work can be undone. Three honest possibilities:

- **Real rollback** — a transaction, and its boundary.
- **Compensating action** — what is attempted, and when compensation itself can fail.
- **None** — and then, critically, *what is guaranteed instead*. Usually convergence: re-running the
  same command completes the work without duplicating it.

"There is no rollback" plus the reason plus the alternative guarantee is a complete, good answer.
Silence here is not.

### 7.3 Recovery

The operator procedure. After a crash mid-run, a lost state file, a corrupted output — what does
someone actually do, step by step?

Name what makes recovery possible: the durable record, the idempotency key, the reconciliation query.
If recovery requires a specific command, give it verbatim.

### 7.4 Concurrency

- What may run simultaneously, and what may not.
- Shared state, and how it is protected — lock file, database transaction, optimistic concurrency,
  single-writer by construction.
- What happens when the guard is hit: block, fail fast, queue.
- Whether operations are idempotent under concurrent execution, which is a different question from
  idempotent under sequential retry.

If concurrency is prevented by design — one manual invocation at a time — say that, and say what
enforces it.

---

## 8. Performance and limits

### 8.1 Latency

Target or expectation per operation, and **where the time goes**. Naming the dominant cost is more
useful than a number: "one HTTP round trip per item, so the wall time is item count × round trip;
local work is negligible."

`N/A` is common and legitimate here.

### 8.2 Throughput

Expected volume and shape: items per run, requests per second, batch size, degree of parallelism, and
the bottleneck. If the design deliberately forgoes parallelism, say why — often ordering or rate
limits.

### 8.3 Limits

Hard numbers, in a table. Both kinds:

- **Imposed** by dependencies — API rate limits, max payload size, field length caps, quotas.
- **Self-imposed** — validation ceilings, retry caps, timeouts, page sizes.

Give the number and what happens at it. "Title 1–255 characters, validated before any network call,
because the API's own message for this is unhelpful."

---

## 9. Security

### 9.1 Identity

- What principal the component runs as.
- How it authenticates to each dependency, and where those credentials originate.
- How callers authenticate to it, if it has callers.
- Authorization: what permissions are required, and the least-privilege position.
- Credential lifetime and what happens on expiry — this connects to §7.1.

### 9.2 Input

- Which inputs are **untrusted**. Default: anything crossing a process, network, or user boundary.
- Where validation happens and how strict it is. Prefer validation at the boundary, before any side
  effect.
- Injection surfaces present in this component: SQL, shell, path traversal, template, XML/YAML
  deserialization, HTML. For each, what prevents it.
- What happens to invalid input: rejected with which error, logged how, and whether it is echoed
  back — echoing untrusted input into a log or an HTML response is itself a surface.

### 9.3 Secrets

- Which secrets exist and what each unlocks.
- Where they come from: environment, vault, CLI token exchange, config file.
- Their lifetime, and rotation if it is a real concern.
- **Where they must never appear** — logs, error messages, state files, reports, terminal output,
  version control, crash dumps. Write this as a list; it becomes an invariant in §12.

If there are no secrets, say so explicitly — that is a meaningful property, not an empty section.

---

## 10. Observability

Open with the signals that exist and **what question each one answers**. A signal nobody would
consult during an incident is noise.

> "Three signals: the run report answers 'what did this run change?'; the state file answers 'what
> exists right now?'; stderr answers 'why did it stop?'. There are no metrics — the component is not
> long-running."

### 10.1 Logs

- Format: structured (JSON) or human-readable, and to which stream.
- Levels, and what belongs at each. Be concrete: what specifically is logged at `INFO` versus
  `DEBUG`.
- What is **never** logged: secrets, tokens, personal data, full payloads.
- Whether output is designed to be parsed by a machine as well as read by a human, and how the two
  modes are separated.

### 10.2 Tracing

- Whether there is a correlation or trace ID, how it is generated, and whether it propagates across
  boundaries.
- Span boundaries, if a tracing system is in use.
- How a single operation is followed end to end.

For a standalone script, honest and useful: `**N/A** — single-process, single-run. The run report and
the state file's timestamps are sufficient to reconstruct what happened.`

---

## 11. Edge cases

The section readers return to most. A **table**, not prose: case → behaviour.

Group by when the case is caught, because that tells the reader how much damage is possible:

- **Caught at validation** — nothing has been written yet.
- **Caught before the side effect** — the network was reached, nothing was changed.
- **Runtime** — something may already have happened.

Every row needs a *behaviour*, not just a name. "Duplicate id" is not an edge case; "duplicate id →
validation error listing every duplicate, exit 2, nothing written" is.

Include the cases that were expensive to learn: the call that succeeds but whose response is lost;
the state file that is truncated rather than absent; the error message that points at the wrong
cause. These earn the document its keep.

---

## 12. Invariants

**Answers:** what must a future change never break?

A numbered list. Each entry must be **testable** — a reviewer should be able to look at a diff and
say whether it holds.

> **Good** — "The bearer token never reaches the state file, the report, the plan output, or a log
> line."

> **Bad** — "The system should remain secure." Untestable.

Draw them from decisions already recorded elsewhere in the document; an invariant that appears
nowhere else is usually an aspiration. Eight to twelve is a healthy count. Open the section with the
line that gives it teeth:

> "A change that breaks one of these is a defect, however convenient it looks."

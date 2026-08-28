# Template — the ARCHITECTURE.md skeleton

Copy the structure below and fill it. `<angle brackets>` mark what to replace. Lines starting with
`>>` are instructions to you — delete every one of them from the generated file.

Keep all 21 topics. A topic that does not apply keeps its heading and reads `**N/A** — <reason>`;
one that is undecided reads `**Not decided** — <what is missing>`.

Drop the numbered subsections that genuinely do not exist for this component only if the parent
section is `N/A` as a whole — otherwise keep them and mark each individually.

---

```markdown
# Architecture — <component name>

<One or two sentences: what this document is, and who it is for.>

>> Include a contents list only if the document exceeds roughly 400 lines. Below that it is noise.

**Contents**

1. [Purpose and scope](#1-purpose-and-scope)
2. [Design principles](#2-design-principles)
3. [Boundaries](#3-boundaries)
4. [Components](#4-components)
5. [Data](#5-data)
6. [API contract](#6-api-contract)
7. [Failure and recovery](#7-failure-and-recovery)
8. [Performance and limits](#8-performance-and-limits)
9. [Security](#9-security)
10. [Observability](#10-observability)
11. [Edge cases](#11-edge-cases)
12. [Invariants](#12-invariants)

---

## 1. Purpose and scope

<Two or three sentences on what the component does.>

It guarantees:

- <guarantee>
- <guarantee>

### Non-goals

The component deliberately does not:

- **<thing>** — <why not>
- **<thing>** — <why not>

>> Always present. Never empty. If the user gave no non-goals, ask before writing this section.

---

## 2. Design principles

**<Principle as a claim.>** <Two or three sentences of reasoning: what it rules out, what it costs,
why the alternative was rejected.>

**<Principle.>** <Reasoning.>

**<Principle.>** <Reasoning.>

>> Three to five. Each must be able to settle an argument about a future change.

---

## 3. Boundaries

**Inside** — <what this component owns and may change.>

**Outside** — <adjacent systems it depends on but does not control, and what it assumes of each.>

| External system | Direction | This component assumes |
|---|---|---|
| <name> | calls it / is called by it | <assumption> |

**Trust boundaries** — <which crossings carry untrusted data. Feeds §9.2.>

>> A small diagram earns its place here more than anywhere else. Use a fenced block or inline SVG.

---

## 4. Components

```
<directory tree, or component list>
```

| Component | Responsibility |
|---|---|
| `<name>` | <one line — if it needs "and", it may be two components> |

**Privilege rules** — <which component may write, which is read-only, which is the sole owner of a
given resource. These become invariants in §12.>

---

## 5. Data

**Entities** — <what exists; which are owned versus merely read.>

| Entity | Owned | Lives in | Lifecycle |
|---|---|---|---|
| <name> | yes/no | <file, table, external system> | <created when, updated when, removed when> |

**Schema** — <where it is defined, whether versioned, what happens to existing data on change.>

**Integrity** — <atomic writes, partial-write behaviour, what makes a record trustworthy.>

---

## 6. API contract

<How it is invoked. Real syntax.>

| Input | Required | Source | Notes |
|---|---|---|---|
| <name> | yes/no | <arg, env, file, request body> | <default, or "no default, by design"> |

**Output** — <success shape; machine-readable form if one exists.>

**Errors**

| Code | Meaning | Retryable |
|---|---|---|
| <code> | <meaning> | yes/no |

**Compatibility** — <what callers may rely on; what may change without notice.>

>> Show at least one real invocation and one real response.

---

## 7. Failure and recovery

### 7.1 Retry

| Failure | Behaviour |
|---|---|
| <class> | <retry or not, attempts, backoff, hints honoured> |

**Never retried:** <classes, and why.>

### 7.2 Rollback

<Real rollback, compensating action, or none. If none: what is guaranteed instead.>

### 7.3 Recovery

<The operator procedure, step by step. What makes recovery possible. Commands verbatim.>

### 7.4 Concurrency

<What may run at once. Shared state and its protection. Behaviour when the guard is hit. Idempotency
under concurrent execution.>

---

## 8. Performance and limits

### 8.1 Latency

<Target or expectation, and where the time goes.>

### 8.2 Throughput

<Volume, batch size, parallelism, bottleneck.>

### 8.3 Limits

| Limit | Value | At the limit |
|---|---|---|
| <name> | <number> | <what happens> |

---

## 9. Security

### 9.1 Identity

<Principal it runs as. How it authenticates to each dependency and where credentials come from. How
callers authenticate. Permissions required. Credential lifetime and expiry behaviour.>

### 9.2 Input

**Untrusted inputs** — <list.>

**Validation** — <where, how strict, before which side effects.>

| Surface | Mitigation |
|---|---|
| <injection surface present here> | <what prevents it> |

**Invalid input** — <rejected with which error, logged how, echoed or not.>

### 9.3 Secrets

| Secret | Source | Unlocks |
|---|---|---|
| <name> | <env, vault, token exchange> | <what> |

**Must never appear in:** <logs, error messages, state files, reports, terminal output, version
control.>

>> If there are none, say so explicitly — that is a property, not an empty section.

---

## 10. Observability

| Signal | Answers |
|---|---|
| <name> | <the question someone would consult it for> |

### 10.1 Logs

<Format and stream. Levels and what belongs at each, concretely. What is never logged. Whether output
is machine-parseable and how the modes are separated.>

### 10.2 Tracing

<Correlation or trace ID, generation, propagation, span boundaries. Or `N/A` with the reason and what
serves the purpose instead.>

---

## 11. Edge cases

### Caught at validation — nothing is written

| Case | Behaviour |
|---|---|
| <case> | <behaviour, including exit code / status> |

### Caught before the side effect

| Case | Behaviour |
|---|---|
| <case> | <behaviour> |

### Runtime

| Case | Behaviour |
|---|---|
| <case> | <behaviour> |

>> Every row needs a behaviour, not just a name. Include the cases that were expensive to learn.

---

## 12. Invariants

A change that breaks one of these is a defect, however convenient it looks.

1. <testable rule>
2. <testable rule>
3. <testable rule>

>> Eight to twelve. Each must be checkable against a diff.
```

---

## After writing

Report in chat, not in the document:

- **Decided rather than asked** — anything inferred, with the reasoning, so the user can veto it.
- **Not decided** — every marker left in the file, as a short to-do list.

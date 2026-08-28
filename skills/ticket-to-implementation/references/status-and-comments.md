# Status header, checkboxes and the blocking comment

Read in Phase 5. These formats are fixed so a status can be read — and grepped — across a whole
`tickets/` directory without opening each file.

---

## The status line

First metadata line, directly under the title, above `**Depends on:**`:

```markdown
# 04 — CLI skeleton, argument parsing and exit codes

**Status:** done
**Depends on:** 01
**Reference:** ARCHITECTURE.md §9 (CLI contract), §8.3 (exit codes), Invariant 3
```

Exactly two values, lower case, verbatim:

| Value | Written when |
|---|---|
| `done` | Every detail of **Job to do** is built and every acceptance criterion was verified by a command that ran |
| `need more information` | Anything is unbuilt, unclear or unverifiable |

Rules:

- **No other value.** Not `in progress`, not `partial`, not `blocked`, not `done (see notes)`. The
  line exists to be trusted at a glance; a third value makes every reader open the file.
- **No status line at all** means untouched. Do not add `**Status:** todo` to tickets you are not
  implementing.
- One status line per ticket. On a re-run, **replace** the existing line — never add a second, and
  never keep a history of past statuses in the header.
- Tickets written by the `architecture-to-ticket` skill deliberately carry no status field. This
  skill owns that line: it is added by the implementer, on the ticket it just executed.

---

## Checkboxes

Tick acceptance criteria only in the same edit that writes `**Status:** done`:

```markdown
- [x] `apply.py m.json` exits 4 with a usage message naming both modes.
```

- **All or none.** A ticket is not done until all criteria pass, so partially ticked boxes claim a
  state that does not exist. When blocking, leave every box unticked and name the failing criteria in
  the comment instead.
- Never edit the text of a criterion. If a criterion is wrong or impossible, that is a blocker, not
  an edit.

---

## The blocking comment

Appended at the **end** of the ticket, after the acceptance criteria, separated by a rule. One
section, however many questions:

```markdown
---

## Need more information

Implementation stopped at the clarity gate; nothing was written.

### 1. The shape of the plan object is not defined

**Where:** Job to do, "the plan stage returns the plan"; acceptance criterion 4.
**The ticket says:** "> plan → (dry-run? print plan, exit 0) → execute"
**What is missing:** no ticket or architecture section states what a plan entry contains. Ticket 15
prints it and ticket 18 executes it, so choosing a shape here decides both.
**What would unblock it:** the field list of one plan entry — at minimum whether it carries the
decision (CREATE/SKIP/DRIFT), the manifest id, the resolved item and the parent's ADO id.

### 2. …
```

Each question carries all four parts:

| Part | Why it is there |
|---|---|
| **Where** | The answer goes back into that spot; a question with no anchor gets answered in the wrong place |
| **The ticket says** | The exact wording, quoted. Paraphrasing a gap is how a second gap is created |
| **What is missing** | The gap and, in one clause, what downstream work it decides |
| **What would unblock it** | The specific answer wanted. "Please clarify" is not a question |

Further rules:

- **Answerable, not rhetorical.** "What should the retry count be?" — with the options, if there are
  obvious ones. Never "the retry policy is unclear".
- **No recommendations dressed as questions.** If you have a preference, state it as a preference:
  "Recommend 5, matching §8.1" — the user still decides.
- **Say what was built.** When a blocker appeared mid-implementation, add one line before the
  questions: what is in the working tree and what was deliberately left unwritten.
- **Never invent an answer in the comment**, and never leave a guessed placeholder in the code with a
  TODO pointing at the comment. The unwritten part stays unwritten.
- The section is deleted in full when the last question is resolved, in the same edit that sets
  `**Status:** done`.

---

## Nothing else goes in the ticket

The ticket file gains exactly two things from this skill: the status line, and the blocking comment
when it blocks. Not implementation notes, not a changelog, not a list of files touched, not the
verification output. Those belong in chat and in the commit — a ticket that accumulates run history
stops being readable as a specification.

The one exception is Phase 5 of a re-run: an answer that arrived in chat is folded into **Job to do**
in the ticket's own voice, so the ticket stays self-contained.

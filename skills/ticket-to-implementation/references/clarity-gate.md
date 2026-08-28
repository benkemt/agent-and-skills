# The clarity gate

Read in Phase 2, before writing code. This file draws one line: **blocker** (stop, write the gap into
the ticket) versus **routine implementation judgment** (proceed, record the choice in a comment).

Getting this line wrong is expensive in both directions. Blocking on everything makes the skill
useless — every ticket has silences an implementer is expected to fill. Blocking on nothing produces
invented contracts that the next ticket builds on.

---

## The test

For each gap, ask both questions:

1. **Do the ticket and the architecture give any basis to choose?** A stated rule, an example, a
   convention in the code the dependencies produced, an invariant that only one option satisfies.
2. **Is the choice visible from outside the code?** A name another ticket will call, a file format, a
   message string, an exit code, an order of operations, a value written to disk or sent over a wire.

| 1. Basis to choose | 2. Externally visible | Verdict |
|---|---|---|
| No | Yes | **Blocker** — stop |
| No | No | Routine — choose, comment the choice, mention it in chat |
| Yes | Yes | Routine — follow the basis, cite it in the comment |
| Yes | No | Routine — follow the basis |

The second column is what makes the difference. An internal helper's name is yours. The name of the
function ticket 18 is told to call is not.

---

## Blockers — stop and write it into the ticket

- **A named behaviour with no definition.** "Fails the item and surfaces the ADO error verbatim" when
  neither the ticket nor the architecture says what "the item's failure record" contains, and a later
  ticket has to read it.
- **A contract another ticket depends on, left unnamed.** The ticket says the stage "returns the
  plan" and nothing anywhere says what a plan is. Ticket 15 will print it and ticket 18 will execute
  it — inventing the shape now decides both.
- **A format with no example and no rule.** An output the ticket calls "the report" with no sample,
  no field list and no `--json` shape anywhere in the architecture.
- **Two sources that contradict each other.** The ticket says exit 2, the architecture says exit 4,
  and the ticket does not acknowledge overriding it. Quote both readings; do not pick.
- **An acceptance criterion that cannot be executed as written.** It names a fixture, a service, a
  credential or a command that does not exist and the ticket does not say how to obtain it.
- **A magic value with no source.** A URL, an API version, a resource GUID, a retry count or a
  timeout that appears nowhere in the ticket, the architecture or the existing code.
- **A conflict with an invariant.** Following the ticket literally would break an invariant the
  architecture states. Report both; let the user resolve the contract.

## Routine — proceed and record the choice

- **Internal structure.** How many helper functions, which private module, whether a loop or a
  comprehension, class versus dict for internal state.
- **Names not crossing a boundary.** Local variables, private helpers, test names, fixture files.
- **Anything the surrounding code already settles.** If every other stage raises a shared error type
  and this one obviously should too, that is a basis — follow it and say so in the comment.
- **The obvious reading of a slightly loose sentence.** "Two-digit zero-padded" needs no clarification
  request. Neither does "trailing `.json` replaced by `.state.json`" applied to a path that has no
  `.json` — pick the sane extension of the rule, comment it, and mention it in chat.
- **Wording of messages the ticket does not quote**, as long as the ticket's requirement about them
  is met — a usage message "naming both modes" must name both modes; its exact prose is yours.
- **Ordering with no observable consequence.** Which of two independent validations runs first, when
  both are reported together anyway.

---

## Worked examples

**Ticket says:** *"Define a single exit-code enum used everywhere."* Nothing says whether the enum is
`IntEnum` or a set of module constants.
→ **Routine.** The values are fixed by the architecture's table; the container is internal. Choose
`IntEnum` because `sys.exit` needs an int, and comment why.

**Ticket says:** *"An unreadable or non-JSON manifest exits 4, not 2."*
→ **No gap.** Fully specified, including the counter-intuitive part and its reason.

**Ticket says:** *"Restrict to these items and their descendants"* with no statement of what happens
when an id in `--only` matches nothing.
→ **Blocker if this ticket owns the filter** — silently empty and hard error are both defensible and
the difference is visible to the user. → **Routine if this ticket only parses the flag into a list**
and a later ticket owns the filter; parse it, and leave the behaviour to that ticket.

**Ticket says:** *"exactly one of `--dry-run` / `--apply` must be given, unless `--rebuild-state` is
used"* and says nothing about `--rebuild-state --apply` together.
→ **Routine.** The sentence has one reading: with `--rebuild-state`, the mode requirement does not
apply. Implement the literal reading, comment it, and mention it in chat.

**Ticket says:** *"Log every HTTP request and response status"* in a ticket that builds no HTTP
client.
→ **Routine.** Provide the logging hook the later ticket will call; the log line's content is that
ticket's to define.

---

## When you block, block early and completely

List **every** gap in one pass. A ticket that comes back three times because each run surfaced one
question costs more than the run that asked four questions at once — and each round trip is a chance
for the ticket to drift.

And keep the standard symmetrical: a gap you are tempted to wave through because it is small is
exactly the kind that turns into an invented contract. If the two-question test says blocker, block.

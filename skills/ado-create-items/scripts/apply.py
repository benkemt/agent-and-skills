#!/usr/bin/env python3
"""Create a tree of linked Azure DevOps work items from a manifest.

CLI skeleton and process contract (ticket 04). The seven-stage pipeline of
``ARCHITECTURE.md`` §6 is laid out here as named functions; tickets 05-24 each
fill exactly one stage. See ``../ARCHITECTURE.md`` for the contract this script
must satisfy.

Dependencies
------------
This script targets the **Python 3.9+ standard library only** — ``urllib.request``,
``json``, ``hashlib``, ``argparse``, ``subprocess``, ``os`` — so it runs anywhere
``python3`` is available with no ``pip install`` step.

No third-party package may become a hard requirement. If ``jsonschema`` is used for
schema validation, it must be an *optional* import guarded by ``try/except
ImportError`` with a hand-rolled fallback validator, so the script never crashes on a
missing third-party package.
"""

import argparse
import json
import sys
from enum import IntEnum

PROG = "apply.py"


class ExitCode(IntEnum):
    """Process exit codes — ARCHITECTURE.md §8.3.

    The single source of truth for every exit in this script. Nothing exits with
    a bare integer.
    """

    OK = 0            # everything applied, or dry-run completed
    PARTIAL = 1       # some items failed or were blocked
    VALIDATION = 2    # validation error — nothing was written
    AUTH = 3          # authentication error — nothing was written
    USAGE = 4         # usage error: missing/duplicate mode, unreadable manifest, lock held


class StageError(Exception):
    """A stage aborting the run with a given exit code.

    Stages raise this instead of exiting, so ``main`` stays the only place that
    ends the process.
    """

    def __init__(self, code, message):
        super().__init__(message)
        self.code = ExitCode(code)
        self.message = message


class Context:
    """Run-wide state passed between stages.

    ``token`` is held in memory only. ``__repr__`` redacts it, so an accidental
    ``print(ctx)`` or a traceback can never leak the bearer token (invariant 9).
    """

    def __init__(self, args):
        self.args = args
        self.manifest = None      # ticket 05
        self.items = None         # ticket 05 — resolved item model
        self.token = None         # ticket 08
        self.state = None         # ticket 11
        self.decisions = None     # ticket 13
        self.plan = None          # ticket 14
        self.results = None       # ticket 18

    def __repr__(self):
        return "<Context manifest=%r token=%s>" % (
            self.args.manifest,
            "held" if self.token else "none",
        )


def log(args, message):
    """Emit a diagnostic line when ``--verbose`` is set (ticket 25).

    Everything passed here must already be redacted — see invariant 9.
    """
    if args.verbose:
        sys.stderr.write("[verbose] %s\n" % message)


# --------------------------------------------------------------------------- #
# Item model — ARCHITECTURE.md §4.1 (root block), §4.2 (item fields)
# --------------------------------------------------------------------------- #


class Item:
    """One entry of the manifest's ``items`` array, defaults already resolved.

    This is the single source for every downstream stage: nothing after the load
    stage re-reads ``defaults``, so the inheritance rules live here and nowhere
    else.

    ``index`` is the item's position in the declared ``items`` array. Ticket 14
    uses it as the stable tiebreaker when sorting siblings by ``order``, so it
    must survive loading — it is the manifest's own declaration order.

    ``raw`` keeps the untouched source entry; schema validation (ticket 06)
    reports against the manifest as written, not against the resolved view.
    """

    def __init__(self, index, raw, defaults):
        self.index = index
        self.raw = raw

        self.id = raw.get("id")
        self.type = raw.get("type")
        # `parent` holds a manifest id, never an ADO id (invariant 6). Absent or
        # null both mean a root item.
        self.parent = raw.get("parent")
        self.parent_ado_id = raw.get("parent_ado_id")

        title = raw.get("title")
        # Light normalisation only. A non-string title is left alone for
        # validation to report with the actual type.
        self.title = title.strip() if isinstance(title, str) else title

        # Content is never authored, rewritten, improved or translated (§1
        # non-goals): the description goes to ADO exactly as written, including
        # a placeholder like "[À compléter]". Same for `fields`, the escape
        # hatch — passed through verbatim.
        self.description = raw.get("description")
        self.fields = raw.get("fields")

        # Inheritance is per key, not all-or-nothing (§4.1): an item that sets
        # only `area_path` still inherits `iteration_path`.
        self.area_path = _inherit(raw, defaults, "area_path")
        self.iteration_path = _inherit(raw, defaults, "iteration_path")
        # Tags are merged with the defaults rather than replacing them (§4.2).
        self.tags = _merge_tags(defaults.get("tags"), raw.get("tags"))

        self.order = raw.get("order")

    def __repr__(self):
        return "<Item %d %s %r>" % (self.index, self.type, self.id)


def _inherit(raw, defaults, key):
    """The item's value if present, else ``defaults[key]``, else unset."""
    value = raw.get(key)
    return defaults.get(key) if value is None else value


def _merge_tags(default_tags, item_tags):
    """``defaults.tags`` then the item's tags, de-duplicated, order preserved.

    De-duplication is exact-match: a tag differing only in case is a different
    tag here, and validation is what judges tag content.
    """
    merged = []
    for source in (default_tags, item_tags):
        # A non-list here is a schema error; leave it to validation rather than
        # iterating a string into single characters.
        if not isinstance(source, list):
            continue
        for tag in source:
            if tag not in merged:
                merged.append(tag)
    return merged


def resolve_items(manifest):
    """Build the resolved item model from a raw manifest.

    Tolerant by design: this runs *before* validation (§6), so a malformed
    manifest must reach the validate stage and exit 2 with every problem listed,
    not die here with a traceback or a misleading exit 4. Anything unusable is
    skipped and left for validation to report from ``raw``.
    """
    if not isinstance(manifest, dict):
        return []

    defaults = manifest.get("defaults")
    if not isinstance(defaults, dict):
        defaults = {}

    raw_items = manifest.get("items")
    if not isinstance(raw_items, list):
        return []

    # The index is the position in the declared array, so skipping an unusable
    # entry never shifts another item's declaration order.
    return [
        Item(index, raw, defaults)
        for index, raw in enumerate(raw_items)
        if isinstance(raw, dict)
    ]


# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #


class _Parser(argparse.ArgumentParser):
    """A parser whose usage errors exit 4 rather than argparse's own 2.

    Exit 2 is reserved for manifest validation errors (§8.3), so every usage
    error — unknown flag, missing positional, bad mode combination — maps to
    ``ExitCode.USAGE``.
    """

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        raise SystemExit(int(ExitCode.USAGE))


def build_parser():
    """The command surface of ARCHITECTURE.md §9."""
    parser = _Parser(
        prog=PROG,
        usage="%(prog)s <manifest> (--dry-run | --apply) [options]",
        description="Create a tree of linked Azure DevOps work items from a manifest.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exactly one of --dry-run or --apply is required; there is no default.\n"
            "\n"
            "Exit codes:\n"
            "  0  everything applied, or dry-run completed\n"
            "  1  partial failure - some items failed or were blocked\n"
            "  2  validation error - nothing was written\n"
            "  3  authentication error - nothing was written\n"
            "  4  usage error (missing/duplicate mode, unreadable manifest, lock held)\n"
        ),
    )
    parser.add_argument(
        "manifest",
        help="path to workitems.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="read-only: validate, authenticate, pre-check, reconcile and print the plan",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="execute the plan",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="patch items whose content drifted from the manifest",
    )
    parser.add_argument(
        "--rebuild-state",
        action="store_true",
        help="rebuild the state file from the wi: tags in ADO, then exit",
    )
    parser.add_argument(
        "--state",
        metavar="<path>",
        default=None,
        help="state file location (default: the manifest path with .json replaced by .state.json)",
    )
    parser.add_argument(
        "--only",
        metavar="<id>[,<id>...]",
        default=None,
        help="restrict the run to these items and their descendants",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="emit the report as JSON on stdout instead of human-readable text",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="log every HTTP request and response status",
    )
    return parser


def default_state_path(manifest_path):
    """``workitems.json`` -> ``workitems.state.json`` (ARCHITECTURE.md §9)."""
    if manifest_path.endswith(".json"):
        return manifest_path[: -len(".json")] + ".state.json"
    return manifest_path + ".state.json"


def parse_args(argv):
    """Parse ``argv``, enforce the mandatory-mode rule, derive the defaults.

    Invariant 3: exactly one of ``--dry-run`` / ``--apply`` must be given, unless
    ``--rebuild-state`` is used. Neither, or both, is a usage error. Never default
    either way — defaulting to apply invites accidental writes, defaulting to
    dry-run invites "I thought it had run".
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.rebuild_state:
        if args.dry_run and args.apply:
            parser.error(
                "--dry-run and --apply are mutually exclusive; give exactly one of them"
            )
        if not args.dry_run and not args.apply:
            parser.error(
                "one of --dry-run or --apply is required; there is no default "
                "(--dry-run validates and prints the plan, --apply executes it)"
            )

    if args.state is None:
        args.state = default_state_path(args.manifest)

    if args.only:
        args.only = [part.strip() for part in args.only.split(",") if part.strip()]
    else:
        args.only = None

    return args


# --------------------------------------------------------------------------- #
# Pipeline stages — ARCHITECTURE.md §6
#
#   load -> validate -> authenticate -> pre-check -> reconcile -> plan
#        -> (dry-run? print plan, exit 0) -> execute -> report
#
# Each stage below is a stub filled by exactly one later ticket. A stage that
# cannot continue raises StageError with the exit code of §8.3.
# --------------------------------------------------------------------------- #


def load(ctx):
    """Read the manifest and resolve ``defaults`` into the item model.

    An unreadable or non-JSON manifest is a usage problem, not a content
    problem: exit 4, not 2. The message carries the path and the parse position,
    which is what actually locates the typo.

    Content problems are *not* raised here — they belong to the validate stage,
    which reports them all at once and exits 2.
    """
    path = ctx.args.manifest
    log(ctx.args, "loading manifest %s" % path)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            ctx.manifest = json.load(handle)
    except OSError as exc:
        raise StageError(
            ExitCode.USAGE,
            "cannot read manifest %s: %s" % (path, exc.strerror or exc),
        )
    except ValueError as exc:
        raise StageError(
            ExitCode.USAGE,
            "manifest %s is not valid JSON: %s" % (path, exc),
        )

    ctx.items = resolve_items(ctx.manifest)
    log(ctx.args, "loaded %d item(s)" % len(ctx.items))
    return ctx.manifest


def validate(ctx):
    """Stage 1 — schema (ticket 06) and graph (ticket 07) checks. No network.

    Reports every problem at once, then raises ``StageError(VALIDATION)``.
    """
    log(ctx.args, "validate: not implemented yet")


def authenticate(ctx):
    """Stage 2 — bearer token from the ``az`` session (ticket 08).

    Failure raises ``StageError(AUTH)`` with the remediation command. The token
    lives on ``ctx.token`` and nowhere else (invariant 9).
    """
    log(ctx.args, "authenticate: not implemented yet")


def pre_check(ctx):
    """Stage 3 — area and iteration paths exist in the project (ticket 10)."""
    log(ctx.args, "pre-check: not implemented yet")


def reconcile(ctx):
    """Stage 4 — state file plus content hashes -> CREATE / SKIP / DRIFT / UPDATE.

    Tickets 11, 12, 13.
    """
    log(ctx.args, "reconcile: not implemented yet")
    ctx.decisions = []
    return ctx.decisions


def plan(ctx):
    """Stage 5 — order the decisions for execution (ticket 14).

    Pre-order depth-first walk, siblings by ``order`` ascending, stable.
    """
    log(ctx.args, "plan: not implemented yet")
    ctx.plan = []
    return ctx.plan


def print_plan(ctx):
    """Render the plan for ``--dry-run`` (ticket 15). Writes nothing to ADO."""
    log(ctx.args, "print_plan: not implemented yet")


def execute(ctx):
    """Stage 6 — create and link, flushing state after each item (ticket 18)."""
    log(ctx.args, "execute: not implemented yet")
    ctx.results = []
    return ctx.results


def report(ctx):
    """Stage 7 — what was created, updated, skipped, failed, blocked (ticket 24).

    Returns the exit code: ``PARTIAL`` if anything failed or was blocked,
    otherwise ``OK``.
    """
    log(ctx.args, "report: not implemented yet")
    return ExitCode.OK


def rebuild_state(ctx):
    """``--rebuild-state`` — rebuild the state file from the ADO ``wi:`` tags.

    Ticket 21. Runs instead of the pipeline and returns the run's exit code.
    """
    log(ctx.args, "rebuild-state: not implemented yet")
    return ExitCode.OK


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def run(ctx):
    """Drive the pipeline for an already-built context. Returns an exit code."""
    args = ctx.args

    load(ctx)
    validate(ctx)
    authenticate(ctx)

    if args.rebuild_state:
        return rebuild_state(ctx)

    pre_check(ctx)
    reconcile(ctx)
    plan(ctx)

    if args.dry_run:
        print_plan(ctx)
        return ExitCode.OK

    execute(ctx)
    return report(ctx)


def main(argv=None):
    """Entry point. Returns the process exit code (ARCHITECTURE.md §8.3)."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return int(run(Context(args)))
    except StageError as exc:
        sys.stderr.write("%s: error: %s\n" % (PROG, exc.message))
        return int(exc.code)


if __name__ == "__main__":
    sys.exit(main())

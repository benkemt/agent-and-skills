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
import re
import sys
from enum import IntEnum
from pathlib import Path

try:
    # Optional: the schema is validated by hand when this is absent, so a
    # missing third-party package never stops a run (see the module docstring).
    import jsonschema
except ImportError:  # pragma: no cover - depends on the environment
    jsonschema = None

PROG = "apply.py"

# Resolved relative to this file, never to the working directory: the schema
# ships with the script and must be found wherever apply.py is invoked from.
SCHEMA_PATH = Path(__file__).parent / "schema.json"


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

    def __init__(self, code, message, reported=False):
        super().__init__(message)
        self.code = ExitCode(code)
        self.message = message
        # Set when the stage already printed its own diagnostics in the format
        # the contract specifies, so ``main`` must not add a line to them.
        self.reported = reported


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
# Schema validation — ARCHITECTURE.md §6.1 (schema level), §10 (validation table)
#
# Two error sources — `jsonschema` when it is installed, the hand-rolled walker
# below when it is not — but a single message formatter, so the output does not
# depend on what happens to be installed. Messages name the offending value and
# the rule; a schema library's raw jargon is not actionable.
# --------------------------------------------------------------------------- #

_JSON_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}


def load_schema():
    """Read ``schema.json``.

    Deliberately unguarded: the schema is part of the script, so its absence is
    a broken installation rather than a manifest problem, and none of the §8.3
    exit codes describes that. The traceback names the missing path, which is
    the useful answer to "why is my checkout incomplete".
    """
    with open(SCHEMA_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_schema(manifest):
    """Validate the raw manifest — before inheritance — against ``schema.json``.

    Returns every problem as a sorted list of ``(pointer, message)``. Reporting
    all of them at once is the point: one editing pass fixes the file.
    """
    schema = load_schema()
    if jsonschema is not None:
        errors = _errors_from_jsonschema(schema, manifest)
    else:
        errors = _errors_from_fallback(schema, manifest, schema)

    # The root object itself has no name; a rule about one of its keys reports
    # against that key, so only a whole-document error is left unnamed.
    named = {(pointer or "(root)", message) for pointer, message in errors}
    return sorted(named, key=lambda pair: (_sort_key(pair[0]), pair[1]))


def _errors_from_jsonschema(schema, manifest):
    """Collect every error via ``iter_errors``, reworded by the shared formatter."""
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for error in validator.iter_errors(manifest):
        pointer = _pointer(list(error.absolute_path))
        described = _message(error.validator, error.validator_value, error.instance,
                             error.schema, pointer)
        # A keyword the formatter does not cover: the library's own wording beats
        # inventing one, and it still names the offending value.
        errors.append(described or (pointer, error.message))
    return errors


def _errors_from_fallback(schema, instance, root, pointer=""):
    """Hand-rolled checker covering the keywords ``schema.json`` actually uses.

    It walks the schema rather than restating its rules, so the two branches
    cannot drift apart when the schema changes.
    """
    schema = _resolve(schema, root)
    errors = []

    if "type" in schema and not _type_matches(schema["type"], instance):
        return [_described(_message("type", schema["type"], instance, schema, pointer))]

    if "enum" in schema and instance not in schema["enum"]:
        return [_described(_message("enum", schema["enum"], instance, schema, pointer))]

    if isinstance(instance, str):
        for keyword in ("pattern", "minLength", "maxLength"):
            if keyword in schema and not _string_ok(keyword, schema[keyword], instance):
                errors.append(_described(_message(keyword, schema[keyword], instance, schema, pointer)))

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(_described(_message("minimum", schema["minimum"], instance, schema, pointer)))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(_described(_message("minItems", schema["minItems"], instance, schema, pointer)))
        if "items" in schema:
            for index, entry in enumerate(instance):
                errors.extend(_errors_from_fallback(
                    schema["items"], entry, root, "%s[%d]" % (pointer, index)))

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(_described(_message(
                    "required", schema["required"], instance, schema, pointer, key)))
        if schema.get("additionalProperties") is False:
            for key in sorted(set(instance) - set(schema.get("properties", {}))):
                errors.append(_described(_message(
                    "additionalProperties", False, instance, schema, pointer, key)))
        forbidden = _resolve(schema.get("not", {}), root).get("required")
        if forbidden and all(key in instance for key in forbidden):
            errors.append(_described(_message("not", schema["not"], instance, schema, pointer)))
        for key, subschema in schema.get("properties", {}).items():
            if key in instance:
                errors.extend(_errors_from_fallback(
                    subschema, instance[key], root, _join(pointer, key)))

    return errors


def _message(keyword, expected, value, subschema, pointer, key=None):
    """The single source of wording, shared by both branches.

    Returns ``(pointer, message)`` — a rule about a named key reports against
    that key, so it sorts next to the other errors on the same item.
    """
    if keyword == "required":
        missing = [key] if key else [k for k in expected if not _has(value, k)]
        if not missing:
            return None
        return (_join(pointer, missing[0]), "missing required key")

    if keyword == "additionalProperties":
        extras = [key] if key else sorted(set(value) - set(subschema.get("properties", {})))
        if not extras:
            return None
        return (_join(pointer, extras[0]),
                "unknown key — the manifest schema does not define it")

    if keyword == "not":
        # The only `not` in the schema is the parent/parent_ado_id exclusion.
        forbidden = (subschema.get("not") or {}).get("required") or []
        if sorted(forbidden) == ["parent", "parent_ado_id"]:
            return (pointer, "'parent' and 'parent_ado_id' are mutually exclusive")
        return None

    if keyword == "type":
        return (pointer, "expected %s, got %s (%s)" % (
            _type_names(expected), _type_of(value), _brief(value)))

    if keyword == "enum":
        return (pointer, "%s is not valid — expected one of %s" % (
            _brief(value), ", ".join(str(option) for option in expected)))

    if keyword == "maxLength":
        return (pointer, "too long: %d characters (max %d)" % (len(value), expected))

    if keyword == "minLength":
        if expected == 1 and value == "":
            return (pointer, "empty — at least 1 character is required")
        return (pointer, "too short: %d characters (min %d)" % (len(value), expected))

    if keyword == "minItems":
        if expected == 1 and not value:
            # §10: an empty run is more likely a bug than an intention.
            return (pointer, "empty — an empty run is more likely a bug than an intention")
        return (pointer, "too few entries: %d (min %d)" % (len(value), expected))

    if keyword == "minimum":
        return (pointer, "%s is below the minimum of %s" % (_brief(value), expected))

    if keyword == "pattern":
        if expected == "^[^;]+$":
            # The trap worth naming: ';' is ADO's tag separator.
            return (pointer, "tag contains ';' — ADO would split it in two")
        if expected == "^[a-z0-9]+(-[a-z0-9]+)*$":
            return (pointer, "%s is not a valid id — lower-case letters, digits and "
                             "single '-' separators only" % _brief(value))
        return (pointer, "%s does not match %s" % (_brief(value), expected))

    return None


def _described(described):
    """Unwrap a formatted error.

    The fallback branch only asks the formatter for keywords it covers, so a
    ``None`` here is a bug in this module rather than a manifest problem.
    """
    if described is None:
        raise AssertionError("schema keyword reached the fallback unformatted")
    return described


def _resolve(schema, root):
    """Follow a local ``$ref`` — the schema uses ``#/$defs/...`` only."""
    while isinstance(schema, dict) and "$ref" in schema:
        target = root
        for step in schema["$ref"].lstrip("#/").split("/"):
            target = target[step]
        schema = target
    return schema if isinstance(schema, dict) else {}


def _type_matches(expected, value):
    names = expected if isinstance(expected, list) else [expected]
    for name in names:
        python_type = _JSON_TYPES.get(name)
        if python_type is None:
            continue
        if name in ("integer", "number") and isinstance(value, bool):
            continue  # JSON booleans are not numbers
        if isinstance(value, python_type):
            return True
    return False


def _string_ok(keyword, expected, value):
    if keyword == "pattern":
        return re.search(expected, value) is not None
    if keyword == "minLength":
        return len(value) >= expected
    return len(value) <= expected


def _has(instance, key):
    return isinstance(instance, dict) and key in instance


def _type_names(expected):
    names = expected if isinstance(expected, list) else [expected]
    return " or ".join(names)


def _type_of(value):
    for name, python_type in _JSON_TYPES.items():
        if name in ("integer", "number") and isinstance(value, bool):
            continue
        if isinstance(value, python_type):
            return name
    return type(value).__name__


def _brief(value):
    """A short, quoted rendering of the offending value."""
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= 60 else text[:57] + "…"


def _join(pointer, key):
    return "%s.%s" % (pointer, key) if pointer else key


def _pointer(path):
    """Render a JSON path as ``items[3].tags[0]``.

    An empty path is the document itself and stays empty here, so a key joined
    onto it reads ``organization`` rather than ``(root).organization``.
    """
    rendered = ""
    for step in path:
        if isinstance(step, int):
            rendered += "[%d]" % step
        else:
            rendered = _join(rendered, step)
    return rendered


def _sort_key(pointer):
    """Sort by pointer in document order — ``items[2]`` before ``items[10]``.

    Plain string order would interleave the items of a manifest with ten or more
    entries, and the point of listing every error is a single top-to-bottom
    editing pass.
    """
    return [int(part) if part.isdigit() else part
            for part in re.split(r"(\d+)", pointer)]


def report_validation_errors(errors):
    """Print every error, one per line, aligned, in the contract's format."""
    width = max(len(pointer) for pointer, _ in errors)
    for pointer, message in errors:
        sys.stderr.write("VALIDATION  %-*s  %s\n" % (width, pointer, message))


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
    """Stage 1 — schema (this stage) and graph (ticket 07) checks. No network.

    Reports every problem at once, then raises ``StageError(VALIDATION)``.
    Nothing is written and no network call is made unless validation passed
    completely (invariant 2), so this runs before authentication.
    """
    log(ctx.args, "validating against %s" % SCHEMA_PATH)
    errors = validate_schema(ctx.manifest)
    if errors:
        report_validation_errors(errors)
        raise StageError(
            ExitCode.VALIDATION,
            "%d schema error(s)" % len(errors),
            reported=True,
        )
    log(ctx.args, "schema validation passed")


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
        if not exc.reported:
            sys.stderr.write("%s: error: %s\n" % (PROG, exc.message))
        return int(exc.code)


if __name__ == "__main__":
    sys.exit(main())

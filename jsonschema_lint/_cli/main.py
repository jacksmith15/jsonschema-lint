import sys
import traceback
import urllib
from pathlib import Path
from typing import Dict, Literal, Optional, Tuple

import click

from jsonschema_lint._cli.resolver import resolve_targets
from jsonschema_lint._cli.rule_loader import Rule
from jsonschema_lint.linter import Error, lint


@click.command("jsonschema-lint")
@click.option(
    "--schema",
    "-s",
    "schema_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Ignore .jsonschemarc files and use this schema for all specified files.",
)
@click.option(
    "--schema-store/--no-schema-store",
    type=bool,
    default=False,
    help="Use schemastore.org to identify correct schemas.",
)
@click.argument(
    "filter",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    nargs=-1,
)
def jsonschema_lint(filter: Tuple[Path, ...], schema_path: Optional[Path] = None, schema_store: bool = False):
    """Lint instances against schemas.

    May pass file paths as arguments to lint specific files, otherwise all files with a
    recognised extensions below the current directory are linted.

    A given instance's schema is identified by checking its directory and parent directories
    for a .jsonschema-lint file which contains a glob matching that file. Instances which
    do not have a matching entry in any .jsonschema-lint file are not linted.

    If the --schema-store flag is provided, schemastore.org will be checked for common
    filenames. Local .jsonschema-lint rules will always take priority over this.

    Alternatively, an exact schema may be passed using the --schema option. This will be
    used for all specified files.
    """
    num_errors = 0
    for rule, path in resolve_targets(filter, schema_path, schema_store):
        num_errors += lint_file(rule, path)
    sys.exit(min(1, num_errors))


def lint_file(rule: Rule, path: Path) -> int:
    """Lint a file, print errors, return the number of errors."""
    try:
        path = path.relative_to(Path.cwd())
    except ValueError:
        pass
    try:
        schema = rule.schema
    except urllib.error.URLError:
        click.echo(f"{path}:1:1:1:1: Could not load schema from {rule.resolved_schema_uri}")
        return 1
    mode = rule.mode or get_mode(path)
    errors = lint(schema=schema, document=path.read_text(), mode=mode)
    for error in errors:
        click.echo(format_error(path, error))
    return len(errors)


def get_mode(path: Path) -> Optional[Literal["json", "yaml"]]:
    mapping: Dict[str, Literal["json", "yaml"]] = {
        "json": "json",
        "yml": "yaml",
        "yaml": "yaml",
    }
    return mapping.get(path.suffix.lstrip("."))


def format_error(instance_path: Path, error: Error) -> str:
    return (
        f"{instance_path}:"
        f"{error.location.start.line}:{error.location.start.column}:"
        f"{error.location.end.line}:{error.location.end.column}: "
    ) + click.style(f"{error.message}", fg="red", bold=True)


def run_cli():
    try:
        jsonschema_lint()
    except Exception as exc:
        # Convert internal errors to exit code 2 (to distinguish from linter errors).
        if not isinstance(exc, click.ClickException):
            output = "".join(
                traceback.format_exception(
                    type(exc),
                    exc,
                    exc.__traceback__,
                )
            )
            sys.stderr.write(output)
            sys.exit(2)
        raise exc

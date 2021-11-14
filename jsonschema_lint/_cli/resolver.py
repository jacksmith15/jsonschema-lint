from pathlib import Path
from typing import Iterator, Optional, Tuple

from jsonschema_lint import compat
from jsonschema_lint._cli.rule_loader import Rule, RuleStack


def resolve_targets(
    filter: Tuple[Path, ...], schema_path: Optional[Path] = None, schema_store: bool = False
) -> Iterator[Tuple[Rule, Path]]:
    """Resolve instances and their corresponding schema rules."""
    filter = filter or default_targets()
    filter = tuple([path.absolute() for path in filter])
    for path in filter:
        rule_stack = RuleStack(cwd=path.parent, schema_store=schema_store, schema_override=schema_path)
        rule = rule_stack.rule_for(path)
        if rule:
            yield rule, path


def default_targets() -> Tuple[Path, ...]:
    result = list(Path.cwd().glob("**/*.json"))
    if compat.YAML_ENABLED:
        result.extend(Path.cwd().glob("**/*.yaml"))
        result.extend(Path.cwd().glob("**/*.yml"))
    return tuple(result)

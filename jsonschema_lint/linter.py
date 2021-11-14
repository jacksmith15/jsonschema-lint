import json
from dataclasses import dataclass
from typing import List, Literal, Tuple

from jsonschema import ValidationError
from jsonschema.validators import validator_for

from jsonschema_lint.compat import YAML_ENABLED
from jsonschema_lint.json_ast import nodes
from jsonschema_lint.json_ast import parse as json_parse
from jsonschema_lint.json_ast.errors import JSONASTError
from jsonschema_lint.json_ast.location import Location

if YAML_ENABLED:
    from yaml import safe_load as load_yaml

    from jsonschema_lint.yaml_ast import YAMLASTError
    from jsonschema_lint.yaml_ast import parse_all as yaml_parse
else:
    YAMLASTError = JSONASTError  # type: ignore[assignment, misc]

    def yaml_parse(document: str) -> List[nodes.Node]:
        raise RuntimeError("PyYAML is not installed")

    def load_yaml(*args, **kwargs):  # type: ignore[misc]
        raise RuntimeError("PyYAML is not installed")


@dataclass
class Error:
    location: Location
    message: str


def lint(schema: dict, document: str, mode: Literal["json", "yaml"] = None) -> List[Error]:
    try:
        mode, asts = _parse_document(document, mode=mode)
    except (JSONASTError, YAMLASTError) as exc:
        return [Error(location=exc.location, message=str(exc))]
    return sum([_get_schema_errors(schema, document, ast, mode) for ast in asts], [])


def _parse_document(
    document: str, mode: Literal["json", "yaml"] = None
) -> Tuple[Literal["json", "yaml"], List[nodes.Node]]:
    """Parse a YAML or JSON document to an AST.

    If mode is specified, use that format.
    Otherwise, try JSON first and fallback to YAML. If neither works, raise the error from
    JSON.
    """
    parsers = {"json": lambda doc: [json_parse(doc)], "yaml": yaml_parse}
    if mode:
        return mode, parsers[mode](document)
    try:
        return "json", parsers["json"](document)
    except JSONASTError as exc:
        if YAML_ENABLED:
            try:
                return "yaml", parsers["yaml"](document)
            except YAMLASTError:
                pass
        raise exc


def _get_schema_errors(schema: dict, document: str, ast: nodes.Node, mode: Literal["json", "yaml"]) -> List[Error]:
    instance = json.loads(document) if mode == "json" else load_yaml(document)
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    return [_convert_error(ast, exc) for exc in validator.iter_errors(instance)]


def _convert_error(ast: nodes.Node, exception: ValidationError) -> Error:
    node = ast.get(*exception.absolute_path)
    instance_repr = repr(exception.instance)
    message = exception.message.replace(instance_repr, _truncate(instance_repr, max_length=40))
    return Error(
        location=node.location,
        message=message,
    )


def _truncate(string: str, max_length: int) -> str:
    if len(string) > max_length:
        string = string[: max_length - 3] + "..."
    return string

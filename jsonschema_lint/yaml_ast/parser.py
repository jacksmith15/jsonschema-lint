from typing import List, Tuple

import yaml

from jsonschema_lint.json_ast import nodes
from jsonschema_lint.json_ast.location import Location, Position
from jsonschema_lint.yaml_ast import utils
from jsonschema_lint.yaml_ast.errors import YAMLASTError


def parse_all(document: str) -> List[nodes.Node]:
    return [_convert_pyyaml_node(document, node) for node in _compose(document, many=True) if not node.value == ""]


def parse(document: str) -> nodes.Node:
    return _convert_pyyaml_node(document, _compose(document))


def _compose(document: str, many: bool = False):
    default_position = Position(line=1, column=1, index=0)
    default_message = "Failed to parse YAML document"

    try:
        if many:
            return [node for node in yaml.compose_all(document)]
        return yaml.compose(document)
    except yaml.error.MarkedYAMLError as exc:
        message = exc.problem or default_message
        position = default_position
        if exc.problem_mark:
            position = utils.position_from_mark(exc.problem_mark)
        raise YAMLASTError(message=message.capitalize(), document=document, location=position)
    except yaml.error.YAMLError as exc:
        message = str(exc)
        raise YAMLASTError(message=str(exc).capitalize(), document=document, location=default_position)
    except Exception:
        raise YAMLASTError(message=default_message, document=document, location=default_position)


def _convert_pyyaml_node(document: str, node: yaml.nodes.Node) -> nodes.Node:
    if not node:
        raise YAMLASTError(message="Input is empty", document=document, location=Position(line=1, column=1, index=0))
    if isinstance(node, yaml.nodes.ScalarNode):
        raw = document[node.start_mark.index : node.end_mark.index]
        value = yaml.safe_load(raw)
        return nodes.Literal.detect(value)(
            location=utils.location_from_marks(start=node.start_mark, end=node.end_mark),
            value=value,
            raw=raw,
        )
    if isinstance(node, yaml.nodes.SequenceNode):
        items = [_convert_pyyaml_node(document, item) for item in node.value]
        return nodes.Array(
            location=utils.location_from_marks(start=node.start_mark, end=node.end_mark),
            children=items,
        )
    if isinstance(node, yaml.nodes.MappingNode):
        properties = [_convert_pyyaml_property(document, prop) for prop in node.value]
        return nodes.Object(
            location=utils.location_from_marks(start=node.start_mark, end=node.end_mark),
            children=properties,
        )
    raise RuntimeError(f"Got unexpected node {node}")


def _convert_pyyaml_property(document: str, prop: Tuple[yaml.nodes.Node, yaml.nodes.Node]) -> nodes.Property:
    identifier = _convert_pyyaml_node(document, prop[0])
    assert isinstance(identifier, nodes.Literal)
    value = _convert_pyyaml_node(document, prop[1])
    return nodes.Property(
        location=Location(start=identifier.location.start, end=value.location.end),
        identifier=identifier,
        value=value,
    )

from dataclasses import asdict
from typing import Type, Union

import pytest

from jsonschema_lint.json_ast import nodes
from jsonschema_lint.json_ast.location import Location, Position


_LOC = Location(start=Position(line=1, column=1, index=0), end=Position(line=1, column=2, index=1))

TREE = nodes.Object(
    location=_LOC,
    children=[
        nodes.Property(
            location=_LOC,
            identifier=nodes.String(value="list", raw='"list"', location=_LOC),
            value=nodes.Array(
                location=_LOC,
                children=[
                    nodes.String(value="string", raw='"string"', location=_LOC),
                ],
            ),
        )
    ],
)


@pytest.mark.parametrize(
    "path,expected",
    [
        ([], TREE),
        (["list", 0], nodes.String(value="string", raw='"string"', location=_LOC)),
        (["list", "key"], TypeError),
        (["foo"], KeyError),
        (["list", 1], IndexError),
        (["list", 0, 0], TypeError),
    ],
)
def test_node_get(path: list, expected: Union[nodes.Node, Type[Exception]]):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            _ = TREE.get(*path)
    else:
        assert TREE.get(*path) == expected


@pytest.mark.parametrize(
    "node,expected",
    [
        pytest.param(TREE, {"list": ["string"]}, id="success"),
        pytest.param(TREE.children[0], TypeError, id="invalid-type"),
    ],
)
def test_resolve(node: nodes.Node, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            _ = node.resolve()
    else:
        assert node.resolve() == expected


def test_dict():
    assert TREE.dict() == asdict(TREE)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, nodes.Null),
        (True, nodes.Boolean),
        ("string", nodes.String),
        (1, nodes.Integer),
        (1.0, nodes.Number),
        ({}, TypeError)
    ]
)
def test_literal_detect(value, expected: Union[Type[nodes.Node], Type[Exception]]):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            _ = nodes.Literal.detect(value)
    else:
        assert nodes.Literal.detect(value) == expected

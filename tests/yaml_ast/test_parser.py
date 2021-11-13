from fnmatch import fnmatch

import pytest

from jsonschema_lint.yaml_ast.errors import YAMLASTError
from jsonschema_lint.yaml_ast.parser import parse, parse_all


def test_parse_simple():
    document = """
foo:
- 1
- "ab\\"c"
- "\\u0123"
- 0.6e+4
bar: {"x": yes}
baz:
"""
    tree = parse(document)
    result = tree.resolve()
    assert result == {"foo": [1, 'ab"c', "\u0123", 6000.0], "bar": {"x": True}, "baz": None}


@pytest.mark.parametrize(
    "document,expected",
    [
        (" \n\r\r\n", "Input is empty"),
        ("{,:}", "Expected the node content, but found ','"),
        ("{}{}", "Expected '<document start>', but found '{'"),
        ("[", "Expected the node content, but found '<stream end>'"),
        ("{", "Expected the node content, but found '<stream end>'"),
        ("[]", []),
        ('{"foo":', "Expected the node content, but found '<stream end>'"),
    ],
)
def test_parse(document: str, expected):
    if isinstance(expected, str):
        with pytest.raises(YAMLASTError) as exc_info:
            _ = parse(document)
        exc = exc_info.value
        if "*" in expected:
            assert fnmatch(str(exc), expected)
        else:
            assert str(exc) == expected
    else:
        tree = parse(document)
        assert tree.resolve() == expected


def test_parse_all_simple():
    document = """---
foo: bar
---
qux: mux
---
"""
    trees = parse_all(document)
    result = [tree.resolve() for tree in trees]
    assert result == [{"foo": "bar"}, {"qux": "mux"}]

import json
from typing import List, Union

import pytest

from jsonschema_lint.json_ast.errors import JSONASTError
from jsonschema_lint.json_ast.tokenizer import tokenize


def test_tokenize_simple():
    document = """
{
    "foo": [1, "ab\\"c", "\\u0123", 0.6e+4],
    "bar": {"x": true},
    "baz": null

}

"""
    tokens = tokenize(document)
    result = json.loads("\n".join([token.value for token in tokens]))
    assert result == {"foo": [1, 'ab"c', "\u0123", 6000.0], "bar": {"x": True}, "baz": None}


@pytest.mark.parametrize(
    "document,expected",
    [
        (" \n\r\r\n\t", []),
        ("{,:}", ["{", ",", ":", "}"]),
        ('"foo"', ['"foo"']),
        ('"foo', "Unclosed string at line 1, column 1"),
        (r'"foo\"', "Unclosed string at line 1, column 1"),  # did not raise
        (r'"foo\\"', [r'"foo\\"']),  # raised
        (r'"foo\\\"', "Unclosed string at line 1, column 1"),
        (r'"foo\\\\"', [r'"foo\\\\"']),  # raised
        ('"\\u0123"', ['"\\u0123"']),
        ('"\\u012h"', 'Invalid unicode escape "\\u012h" at line 1, column 2'),
        ('"\\x"', 'Unexpected escape "\\x" at line 1, column 2'),
        ("0", ["0"]),
        ("123", ["123"]),
        ("1.2", ["1.2"]),
        ("notatoken", "Unexpected symbol 'n' at line 1, column 1"),
    ],
)
def test_tokenize(document: str, expected: Union[List[str], str]):
    if isinstance(expected, str):
        with pytest.raises(JSONASTError) as exc_info:
            _ = tokenize(document)
        exc = exc_info.value
        assert str(exc) == expected
    else:
        tokens = tokenize(document)
        assert [token.value for token in tokens] == expected


def test_token_locations():
    document = """{
    "valid": "string",
    "invalid": 1
}
"""
    tokens = tokenize(document)
    locations_by_value = {
        token.value: (
            (token.location.start.line, token.location.start.column, token.location.start.index),
            (token.location.end.line, token.location.end.column, token.location.end.index),
        )
        for token in tokens
    }
    for value, expected in {
        "{": ((1, 1, 0), (1, 2, 1)),
        '"valid"': ((2, 5, 6), (2, 12, 13)),
        '"string"': ((2, 14, 15), (2, 22, 23)),
        '"invalid"': ((3, 5, 29), (3, 14, 38)),
        "1": ((3, 16, 40), (3, 17, 41)),
    }.items():
        assert locations_by_value[value] == expected

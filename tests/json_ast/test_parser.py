from fnmatch import fnmatch

import pytest

from jsonschema_lint.json_ast.errors import JSONASTError
from jsonschema_lint.json_ast.parser import parse


def test_parse_simple():
    document = """
{
    "foo": [1, "ab\\"c", "\\u0123", 0.6e+4],
    "bar": {"x": true},
    "baz": null

}

"""
    tree = parse(document)
    result = tree.resolve()
    assert result == {"foo": [1, 'ab"c', "\u0123", 6000.0], "bar": {"x": True}, "baz": None}


@pytest.mark.parametrize(
    "document,expected",
    [
        (" \n\r\r\n\t", "Input is empty"),
        ("{,:}", "Unexpected COMMA token ','*"),
        ("{}{}", "Unexpected LEFT_BRACE token '{' at line 1, column 3. Expected one of ['EOF']."),
        ('{"foo": ,}', "Unexpected COMMA token ',' at line 1, column 9. Expected one of *."),
        ("[", "Unclosed array at line 1, column 1"),
        ("{", "Unclosed object at line 1, column 1"),
        ("[]", []),
        ("[1 2]", "Unexpected NUMBER token '2' at line 1, column 4. Expected one of ['COMMA', 'RIGHT_BRACKET']."),
        ('{"foo": 1 2}', "Unexpected NUMBER token '2' at line 1, column 11. Expected one of ['COMMA', 'RIGHT_BRACE']."),
        ('{"foo":', "Incomplete property at line 1, column 2"),
        ('{"foo", "bar"}', "Unexpected COMMA token ',' at line 1, column 7. Expected one of ['COLON']."),
    ],
)
def test_parse(document: str, expected):
    if isinstance(expected, str):
        with pytest.raises(JSONASTError) as exc_info:
            _ = parse(document)
        exc = exc_info.value
        if "*" in expected:
            assert fnmatch(str(exc), expected)
        else:
            assert str(exc) == expected
    else:
        tree = parse(document)
        assert tree.resolve() == expected

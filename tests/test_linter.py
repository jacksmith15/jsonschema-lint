from typing import List

from jsonschema_lint.json_ast.location import Location, Position
from jsonschema_lint.linter import Error, lint


def test_lint_simple():
    schema = {
        "type": "array",
        "items": {"type": "number", "enum": [1, 2, 3]},
        "minItems": 3,
    }
    document = '["spam", 2]'
    errors: List[Error] = lint(schema, document)

    assert errors == [
        Error(
            location=Location(start=Position(line=1, column=2, index=1), end=Position(line=1, column=8, index=7)),
            message="'spam' is not of type 'number'",
        ),
        Error(
            location=Location(start=Position(line=1, column=2, index=1), end=Position(line=1, column=8, index=7)),
            message="'spam' is not one of [1, 2, 3]",
        ),
        Error(
            location=Location(start=Position(line=1, column=1, index=0), end=Position(line=1, column=12, index=11)),
            message="['spam', 2] is too short",
        ),
    ]


def test_lint_ast_error():
    schema = {}
    document = '{"foo": "bar"'

    errors: List[Error] = lint(schema, document)

    assert errors == [
        Error(
            location=Location(start=Position(line=1, column=1, index=0), end=Position(line=1, column=14, index=13)),
            message="Unclosed object at line 1, column 1"
        )
    ]


def test_lint_yaml():
    schema = {
        "type": "array",
        "items": {"type": "number", "enum": [1, 2, 3]},
        "minItems": 3,
    }
    document = """---
- spam
- 2
"""
    errors: List[Error] = lint(schema, document, mode="yaml")

    assert errors == [
        Error(
            location=Location(start=Position(line=2, column=3, index=6), end=Position(line=2, column=7, index=10)),
            message="'spam' is not of type 'number'",
        ),
        Error(
            location=Location(start=Position(line=2, column=3, index=6), end=Position(line=2, column=7, index=10)),
            message="'spam' is not one of [1, 2, 3]",
        ),
        Error(
            location=Location(start=Position(line=2, column=1, index=4), end=Position(line=4, column=1, index=15)),
            message="['spam', 2] is too short",
        ),
    ]

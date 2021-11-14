import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, List, NoReturn

from jsonschema_lint.json_ast.errors import JSONASTError
from jsonschema_lint.json_ast.location import Location, Position


class TokenType(Enum):
    LEFT_BRACE = 0  # {
    RIGHT_BRACE = 1  # }
    LEFT_BRACKET = 2  # [
    RIGHT_BRACKET = 3  # ]
    COLON = 4  # :
    COMMA = 5  # ,
    STRING = 6  #
    NUMBER = 7  #
    TRUE = 8  # true
    FALSE = 9  # false
    NULL = 10  # null
    WHITESPACE = 98
    NEWLINE = 99

    MISMATCH = -1
    UNCLOSED_STRING = -2
    INVALID_STRING = -3
    INVALID_STRING_ESCAPE = -4
    INVALID_STRING_UNICODE_ESCAPE = -5


@dataclass
class Token:
    type: TokenType
    value: str
    location: Location


def tokenize(document: str) -> List[Token]:
    """Tokenize a JSON document."""
    return list(tokenize_iter(document))


def tokenize_iter(document: str) -> Iterator[Token]:
    """Tokenize a JSON document."""
    TT = TokenType
    tokens = {
        TT.LEFT_BRACE: re.escape("{"),
        TT.RIGHT_BRACE: re.escape("}"),
        TT.LEFT_BRACKET: re.escape("["),
        TT.RIGHT_BRACKET: re.escape("]"),
        TT.COLON: re.escape(":"),
        TT.COMMA: re.escape(","),
        TT.STRING: r'("(\\(["\\\/bfnrt]|u[a-fA-F0-9]{4})|[^"\\\0-\x1F\x7F]+)*")',
        TT.NUMBER: r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?",
        TT.TRUE: re.escape("true"),
        TT.FALSE: re.escape("false"),
        TT.NULL: re.escape("null"),
        TT.NEWLINE: r"(\r\n|\r|\n)",
        TT.WHITESPACE: r"[ \t]+",
        TT.INVALID_STRING: r'("(\\.|[^"\\\0-\x1F\x7F]+)*")',
        TT.UNCLOSED_STRING: r'("(\\.|[^"\\\0-\x1F\x7F]+)*)',
        TT.MISMATCH: r".",
    }
    token_regex = "|".join(f"(?P<{token_type.name}>{regex})" for token_type, regex in tokens.items())

    position = Position(line=1, column=1, index=0)

    for match in re.finditer(token_regex, document):
        assert match.lastgroup
        length = match.end() - match.start()

        kind = TokenType[match.lastgroup]
        value = match.group()
        if kind is TT.MISMATCH:
            raise JSONASTError.unexpected_symbol(
                document,
                position,
            )
        elif kind is TT.NEWLINE:
            position.index += length
            position.column = 1
            position.line += 1
            continue
        elif kind is TT.WHITESPACE:
            pass
        elif kind is TT.UNCLOSED_STRING:
            raise JSONASTError(
                f"Unclosed string at line {position.line}, column {position.column}",
                document,
                position,
            )
        elif kind is TT.INVALID_STRING:
            _invalid_string(document, position, value)  # Try to get a detailed error
        else:
            yield Token(
                type=kind,
                value=value,
                location=Location(
                    start=position,
                    end=position + length,
                ),
            )
        position += length


def _invalid_string(document: str, position: Position, value: str) -> NoReturn:
    """Validate JSON string token.

    Used to give more detailed errors regarding strings.
    """
    try:
        json.loads(value)
    except json.JSONDecodeError as exc:
        offset = exc.pos
        if str(exc).startswith("Invalid \\uXXXX escape:"):
            offset -= 1
            substring = value[offset : offset + 6]
            raise JSONASTError(
                f'Invalid unicode escape "{substring}" at line {position.line}, column {position.column + offset}',
                document,
                Location(
                    start=position + offset,
                    end=position + offset + 6,
                ),
            )
        if str(exc).startswith("Invalid \\escape:"):
            substring = value[offset : offset + 2]
            raise JSONASTError(
                f'Unexpected escape "{substring}" at line {position.line}, column {position.column + offset}',
                document,
                Location(
                    start=position + offset,
                    end=position + offset + 2,
                ),
            )
        raise JSONASTError(
            f"Invalid string {value} at line {position.line}, column {position.column + offset}",
            document,
            position + offset,
        )
    raise JSONASTError(f"Invalid string at line {position.line}, column {position.column}", document, position)

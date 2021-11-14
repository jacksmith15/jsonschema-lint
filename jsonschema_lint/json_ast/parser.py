import json
from dataclasses import dataclass
from enum import Enum
from typing import Generic, List, Optional, TypeVar

from jsonschema_lint.json_ast.errors import JSONASTError
from jsonschema_lint.json_ast.location import Location, Position
from jsonschema_lint.json_ast.nodes import Array, Literal, Node, Object, Property, String
from jsonschema_lint.json_ast.tokenizer import Token, TokenType, tokenize


class ObjectState(Enum):
    START = 0
    OPEN_OBJECT = 1
    PROPERTY = 2
    COMMA = 3


class PropertyState(Enum):
    START = 0
    KEY = 1
    COLON = 2


class ArrayState(Enum):
    START = 0
    OPEN_ARRAY = 1
    VALUE = 2
    COMMA = 3


NodeT = TypeVar("NodeT", bound=Node)


@dataclass
class ParseResult(Generic[NodeT]):
    node: NodeT
    index: int


def parse(document: str) -> Node:
    tokens = tokenize(document)
    if not tokens:
        raise JSONASTError("Input is empty", document, Position(line=1, column=1, index=0))

    result = parse_value(document, tokens)

    if result.index == len(tokens):
        return result.node

    raise JSONASTError.unexpected_token(document=document, token=tokens[result.index], expected=["EOF"])


def parse_value(document: str, tokens: List[Token], index: int = 0) -> ParseResult:
    result = (
        parse_literal(document, tokens, index)
        or parse_object(document, tokens, index)
        or parse_array(document, tokens, index)
    )
    if not result:
        raise JSONASTError.unexpected_token(
            document=document,
            token=tokens[index],
            expected=[
                TokenType.LEFT_BRACE,
                TokenType.LEFT_BRACKET,
                TokenType.STRING,
                TokenType.NUMBER,
                TokenType.TRUE,
                TokenType.FALSE,
                TokenType.NULL,
            ],
        )
    return result


def parse_literal(document: str, tokens: List[Token], index: int = 0) -> Optional[ParseResult[Literal]]:
    token = tokens[index]

    if token.type not in (
        TokenType.STRING,
        TokenType.NUMBER,
        TokenType.TRUE,
        TokenType.FALSE,
        TokenType.NULL,
    ):
        return None

    value = json.loads(token.value)
    return ParseResult(
        node=Literal.detect(value)(
            location=token.location,
            value=json.loads(token.value),
            raw=token.value,
        ),
        index=index + 1,
    )


def parse_array(document: str, tokens: List[Token], index: int = 0) -> Optional[ParseResult[Array]]:
    state = ArrayState.START

    start_token = tokens[index]
    children: List[Node] = []

    while index < len(tokens):
        token = tokens[index]

        if state is ArrayState.START:
            if token.type is not TokenType.LEFT_BRACKET:
                return None
            state = ArrayState.OPEN_ARRAY
            index += 1
        elif state is ArrayState.OPEN_ARRAY:
            if token.type is TokenType.RIGHT_BRACKET:
                return ParseResult(
                    node=Array(
                        location=Location(start=start_token.location.start, end=token.location.end),
                        children=children,
                    ),
                    index=index + 1,
                )
            else:
                result = parse_value(document, tokens, index)
                children.append(result.node)
                index = result.index
                state = ArrayState.VALUE
        elif state is ArrayState.VALUE:
            if token.type is TokenType.RIGHT_BRACKET:
                return ParseResult(
                    node=Array(
                        location=Location(start=start_token.location.start, end=token.location.end),
                        children=children,
                    ),
                    index=index + 1,
                )
            elif token.type is TokenType.COMMA:
                state = ArrayState.COMMA
                index += 1
            else:
                raise JSONASTError.unexpected_token(
                    document=document,
                    token=token,
                    expected=[TokenType.COMMA, TokenType.RIGHT_BRACKET],
                )
        elif state is ArrayState.COMMA:
            result = parse_value(document, tokens, index)
            children.append(result.node)
            index = result.index
            state = ArrayState.VALUE

    start = start_token.location.start
    raise JSONASTError(
        f"Unclosed array at line {start.line}, column {start.column}",
        document=document,
        location=Location(start=start, end=tokens[-1].location.end),
    )


def parse_object(document: str, tokens: List[Token], index: int = 0) -> Optional[ParseResult[Object]]:
    state = ObjectState.START

    start_token = tokens[index]
    children: List[Property] = []

    while index < len(tokens):
        token = tokens[index]

        if state is ObjectState.START:
            if token.type is not TokenType.LEFT_BRACE:
                return None
            state = ObjectState.OPEN_OBJECT
            index += 1
        elif state is ObjectState.OPEN_OBJECT:
            if token.type is TokenType.RIGHT_BRACE:
                return ParseResult(
                    node=Object(
                        location=Location(start=start_token.location.start, end=token.location.end),
                        children=children,
                    ),
                    index=index + 1,
                )
            else:
                result = parse_property(document, tokens, index)
                children.append(result.node)
                index = result.index
                state = ObjectState.PROPERTY
        elif state is ObjectState.PROPERTY:
            if token.type is TokenType.RIGHT_BRACE:
                return ParseResult(
                    node=Object(
                        location=Location(start=start_token.location.start, end=token.location.end),
                        children=children,
                    ),
                    index=index + 1,
                )
            elif token.type is TokenType.COMMA:
                state = ObjectState.COMMA
                index += 1
            else:
                raise JSONASTError.unexpected_token(
                    document=document,
                    token=token,
                    expected=[TokenType.COMMA, TokenType.RIGHT_BRACE],
                )
        elif state is ObjectState.COMMA:
            result = parse_property(document, tokens, index)
            children.append(result.node)
            index = result.index
            state = ObjectState.PROPERTY

    start = start_token.location.start
    raise JSONASTError(
        f"Unclosed object at line {start.line}, column {start.column}",
        document=document,
        location=Location(start=start, end=tokens[-1].location.end),
    )


def parse_property(document: str, tokens: List[Token], index: int = 0) -> ParseResult[Property]:
    state = PropertyState.START

    start_token = tokens[index]

    identifier: String

    while index < len(tokens):
        token = tokens[index]

        if state is PropertyState.START:
            if token.type is not TokenType.STRING:
                raise JSONASTError.unexpected_token(
                    document=document,
                    token=token,
                    expected=[TokenType.STRING],
                )
            identifier = String(
                location=token.location,
                value=json.loads(token.value),
                raw=token.value,
            )
            state = PropertyState.KEY
            index += 1
        elif state is PropertyState.KEY:
            if token.type is not TokenType.COLON:
                raise JSONASTError.unexpected_token(
                    document=document,
                    token=token,
                    expected=[TokenType.COLON],
                )
            state = PropertyState.COLON
            index += 1
        elif state is PropertyState.COLON:
            result = parse_value(document, tokens, index)
            return ParseResult(
                node=Property(
                    location=Location(start=start_token.location.start, end=token.location.end),
                    identifier=identifier,
                    value=result.node,
                ),
                index=result.index,
            )

    start = start_token.location.start
    raise JSONASTError(
        f"Incomplete property at line {start.line}, column {start.column}",
        document=document,
        location=Location(start=start, end=tokens[-1].location.end),
    )

from typing import TYPE_CHECKING, List, Union

from jsonschema_lint.json_ast.location import Location, Position

if TYPE_CHECKING:
    from jsonschema_lint.json_ast.tokenizer import Token, TokenType  # pragma: no cover


class JSONASTError(Exception):
    def __init__(self, message: str, document: str, location: Union[Position, Location]):
        super().__init__(message)
        self.message = message
        self.document = document
        if isinstance(location, Position):
            location = Location(start=location, end=location + 1)
        self.location = location

    @classmethod
    def unexpected_symbol(cls, document: str, position: Position):
        return cls(
            f"Unexpected symbol {document[position.index]!r} at line {position.line}, column {position.column}",
            document,
            position,
        )

    @classmethod
    def unexpected_token(cls, document: str, token: "Token", expected: List[Union["TokenType", str]]):
        expected_names = [token_type if isinstance(token_type, str) else token_type.name for token_type in expected]
        start = token.location.start
        message = (
            f"Unexpected {token.type.name} token {token.value!r} at line {start.line}, "
            f"column {start.column}. Expected one of {expected_names}."
        )
        return cls(
            message,
            document=document,
            location=token.location,
        )

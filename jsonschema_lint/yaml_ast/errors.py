from typing import Union

from jsonschema_lint.json_ast.location import Location, Position


class YAMLASTError(Exception):
    def __init__(self, message: str, document: str, location: Union[Position, Location]):
        super().__init__(message)
        self.message = message
        self.document = document
        if isinstance(location, Position):
            location = Location(start=location, end=location + 1)
        self.location = location

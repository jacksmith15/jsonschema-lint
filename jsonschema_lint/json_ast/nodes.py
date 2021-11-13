from dataclasses import asdict, dataclass
from typing import Generic, List, Type, TypeVar, Union

from jsonschema_lint.json_ast.location import Location


@dataclass
class Node:
    location: Location

    def dict(self):
        """Return the AST as a dict."""
        return asdict(self)

    def resolve(self):
        """Return a dict of the JSON described by the AST."""
        if isinstance(self, Literal):
            return self.value
        if isinstance(self, Array):
            return [child.resolve() for child in self.children]
        if isinstance(self, Object):
            return {prop.identifier.value: prop.value.resolve() for prop in self.children}
        raise TypeError(f"Invalid node type {type(self)} of {self}.")

    def get(self, *path: Union[str, int]) -> "Node":
        if not path:
            return self
        if isinstance(self, Object):
            key = path[0]
            for prop in self.children:
                if prop.identifier.value == key:
                    return prop.value.get(*path[1:])
            raise KeyError(f"No such property {key!r}")
        if isinstance(self, Array):
            index = path[0]
            if not isinstance(index, int):
                raise TypeError(f"Array indices must be integers, got {index!r}")
            return self.children[index].get(*path[1:])
        raise TypeError(f"Cannot child of {self}")


LiteralT = TypeVar("LiteralT", bool, str, int, float, None)


@dataclass
class Literal(Node, Generic[LiteralT]):
    value: LiteralT
    raw: str
    type: str = "literal"

    @staticmethod
    def detect(value: LiteralT) -> Type["Literal[LiteralT]"]:
        if value is None:
            return Null
        if isinstance(value, bool):
            return Boolean  # type: ignore[return-value]
        if isinstance(value, str):
            return String
        if isinstance(value, int):
            return Integer  # type: ignore[return-value]
        if isinstance(value, float):
            return Number
        raise TypeError(f"Invalid type {type(value)} of {value} for literal JSON value.")


@dataclass
class Boolean(Literal[bool]):
    type: str = "boolean"


@dataclass
class String(Literal[str]):
    type: str = "string"


@dataclass
class Integer(Literal[int]):
    type: str = "integer"


@dataclass
class Number(Literal[float]):
    type: str = "number"


@dataclass
class Null(Literal[None]):
    type: str = "null"


@dataclass
class Array(Node):
    children: List[Node]
    type: str = "array"


@dataclass
class Property(Node):
    identifier: Literal
    value: Node
    type: str = "property"


@dataclass
class Object(Node):
    children: List[Property]
    type: str = "object"

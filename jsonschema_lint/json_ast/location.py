from dataclasses import dataclass


@dataclass
class Position:
    line: int
    column: int
    index: int

    def __add__(self, other):
        if isinstance(other, int):
            return Position(line=self.line, column=self.column + other, index=self.index + other)
        raise TypeError  # pragma: no cover


@dataclass
class Location:
    start: Position
    end: Position

import yaml

from jsonschema_lint.json_ast.location import Location, Position


def position_from_mark(mark: yaml.error.Mark) -> Position:
    return Position(line=mark.line + 1, column=mark.column + 1, index=mark.index)


def location_from_marks(start: yaml.error.Mark, end: yaml.error.Mark) -> Location:
    return Location(start=position_from_mark(start), end=position_from_mark(end))

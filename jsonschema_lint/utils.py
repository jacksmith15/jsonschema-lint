import re
from pathlib import Path


def path_match(path: Path, glob: str) -> bool:
    """Like Path.match, but with support for recursive patterns (**)."""
    if path_pattern(glob).match(str(path)):
        return True
    return False


def path_pattern(glob: str, sep: str = "/") -> re.Pattern:
    absolute = glob.startswith(sep)
    if absolute:
        glob = glob[1:]
    else:
        if not glob.startswith("**/"):
            glob = f"**/{glob}"

    sep = re.escape(sep)

    # Iteratively replace wildcards surrounded by directory separators,
    # so that we can make those separators optional when next to a wildcard.
    result = (
        re.escape(glob)
        .replace(
            f"{sep}\\*\\*{sep}",
            rf"({sep}(.+?{sep})?)?",
        )
        .replace(
            f"\\*\\*{sep}",
            rf"({sep}?(.*?){sep})?",
        )
        .replace(
            f"{sep}\\*\\*",
            rf"({sep}(.*?){sep}?)?",
        )
        .replace(
            "\\*\\*",
            rf"({sep}?(.*?){sep}?)?",
        )
        .replace(
            f"{sep}\\*{sep}",
            rf"{sep}?[^{sep}]+?{sep}?",
        )
        .replace(
            f"{sep}\\*",
            rf"{sep}?[^{sep}]+?",
        )
        .replace(
            f"\\*{sep}",
            rf"[^{sep}]+?{sep}?",
        )
        .replace(
            "\\*",
            rf"[^{sep}]+?",
        )
        + "$"
    )
    # woof!

    if absolute:
        # Ensure absolute patterns only match absolute paths
        result = f"{sep}{result}"

    return re.compile("^" + result)

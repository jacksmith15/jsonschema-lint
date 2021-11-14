from pathlib import Path

import pytest

from jsonschema_lint.utils import path_match, path_pattern


@pytest.mark.parametrize(
    "pattern,path,expected",
    [
        ("file.json", "file.json", True),
        ("file.json", "foo.json", False),
        ("file.json", "dir/file.json", True),
        ("file.json", "/dir/file.json", True),
        ("*.json", "file.json", True),
        ("*.json", "file.foo", False),
        ("*.json", "dir/file.json", True),
        ("*.json", "/dir/file.json", True),
        ("**/*.json", "file.json", True),
        ("**/*.json", "dir/file.json", True),
        ("**/*.json", "/file.json", True),
        ("**/*.json", "/dir/file.json", True),
        ("/**/*.json", "file.json", False),
        ("/**/*.json", "dir/file.json", False),
        ("/**/*.json", "/file.json", True),
        ("/**/*.json", "/dir/file.json", True),
        ("**/dir/*.json", "dir/file.json", True),
        ("**/dir/*.json", "/dir/file.json", True),
        ("**/dir/*.json", "home/user/dir/file.json", True),
        ("**/dir/*.json", "/home/user/dir/file.json", True),
        ("/**/dir/*.json", "dir/file.json", False),
        ("/**/dir/*.json", "/dir/file.json", True),
        ("/**/dir/*.json", "home/user/dir/file.json", False),
        ("/**/dir/*.json", "/home/user/dir/file.json", True),
        ("dir/**/*.json", "dir/file.json", True),
        ("dir/**/*.json", "/dir/file.json", True),
        ("dir/**/*.json", "dir/subdir/file.json", True),
        ("dir/**/*.json", "/dir/subdir/file.json", True),
        ("/dir/**/*.json", "dir/file.json", False),
        ("/dir/**/*.json", "/dir/file.json", True),
        ("/dir/**/*.json", "dir/subdir/file.json", False),
        ("/dir/**/*.json", "/dir/subdir/file.json", True),
    ],
)
def test_path_match(pattern: str, path, expected: bool):
    path = Path(path)
    compiled_pattern = path_pattern(pattern)
    assert (
        path_match(path, pattern) is expected
    ), f"""Failed:
Expected: {expected}
Pattern: {pattern}
Path: {path}
Compiled Pattern: {compiled_pattern}
"""

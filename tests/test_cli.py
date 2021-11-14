import subprocess
from pathlib import Path

import pytest

ASSETS_DIR = Path(__file__).parent / "assets"

SIMPLE_DIR = ASSETS_DIR / "simple"


def test_it_uses_rc_file():
    result = subprocess.run(["jsonschema-lint"], cwd=SIMPLE_DIR, capture_output=True, text=True)
    output = "\n".join([result.stdout, result.stderr])
    assert result.returncode == 1, output
    assert (
        result.stdout
        == """
object/instances/002.json:1:1:1:15: Additional properties are not allowed ('qux' was unexpected)
numbers/instances/002.json:1:2:1:8: 'spam' is not of type 'number'
numbers/instances/002.json:1:2:1:8: 'spam' is not one of [1, 2, 3]
numbers/instances/002.json:1:1:1:12: ['spam', 2] is too short
numbers/instances/002.yaml:2:3:2:7: 'spam' is not of type 'number'
numbers/instances/002.yaml:2:3:2:7: 'spam' is not one of [1, 2, 3]
numbers/instances/002.yaml:2:1:4:1: ['spam', 2] is too short
object/instances/002.yml:1:1:2:1: Additional properties are not allowed ('qux' was unexpected)
""".lstrip()
    )


def test_it_filters_on_provided_files():
    result = subprocess.run(
        ["jsonschema-lint", "numbers/instances/002.json"], cwd=SIMPLE_DIR, capture_output=True, text=True
    )
    output = "\n".join([result.stdout, result.stderr])
    assert result.returncode == 1, output
    assert (
        result.stdout
        == """
numbers/instances/002.json:1:2:1:8: 'spam' is not of type 'number'
numbers/instances/002.json:1:2:1:8: 'spam' is not one of [1, 2, 3]
numbers/instances/002.json:1:1:1:12: ['spam', 2] is too short
""".lstrip()
    )


def test_it_uses_specified_schema():
    result = subprocess.run(
        ["jsonschema-lint", "--schema", "numbers/schema.json", *SIMPLE_DIR.glob("**/instances/**/*.json")],
        cwd=SIMPLE_DIR,
        capture_output=True,
        text=True,
    )
    output = "\n".join([result.stdout, result.stderr])
    assert result.returncode == 1, output
    assert (
        result.stdout
        == """
object/instances/001.json:1:1:1:15: {'foo': 'bar'} is not of type 'array'
object/instances/002.json:1:1:1:15: {'qux': 'mux'} is not of type 'array'
numbers/instances/002.json:1:2:1:8: 'spam' is not of type 'number'
numbers/instances/002.json:1:2:1:8: 'spam' is not one of [1, 2, 3]
numbers/instances/002.json:1:1:1:12: ['spam', 2] is too short
""".lstrip()
    )


def test_it_uses_yaml_schema():
    result = subprocess.run(
        ["jsonschema-lint"], cwd=ASSETS_DIR / "extra" / "yaml-schema", capture_output=True, text=True
    )
    output = "\n".join([result.stdout, result.stderr])
    assert result.returncode == 1, output
    assert (
        result.stdout
        == """
instances/002.json:3:16:3:17: 1 is not of type 'string'
""".lstrip()
    )


def test_it_uses_remote_schema(mock_remote_schema_server):
    result = subprocess.run(
        ["jsonschema-lint"], cwd=ASSETS_DIR / "extra" / "remote-schema", capture_output=True, text=True
    )
    output = "\n".join([result.stdout, result.stderr])
    assert result.returncode == 1, output
    assert (
        result.stdout
        == """
instances/002.json:1:12:1:13: 1 is not of type 'string'
""".lstrip()
    )


@pytest.fixture()
def mock_remote_schema_server():
    process = subprocess.Popen(
        ["python", "-m", "http.server"],
        cwd=ASSETS_DIR / "extra" / "remote-schema" / "server",
        text=True,
    )
    try:
        yield
    finally:
        exit_code = process.poll()
        assert not exit_code, "\n".join([process.stdout, process.stderr])
        process.terminate()

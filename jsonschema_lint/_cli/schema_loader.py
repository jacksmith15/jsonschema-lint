import cgi
import json
import mimetypes
from functools import lru_cache
from urllib.request import urlopen

from jsonschema_lint import compat


@lru_cache(maxsize=None)
def load_schema(url: str) -> dict:
    """Fetch and parse a schema from URL.

    Attempts to identify the correct format, falling back to trying both
    JSON and YAML. JSON is preferred, and errors from this will be raised
    if neither work.
    """
    with urlopen(url) as conn:
        content_type = _get_content_type(conn)
        content = conn.read()
    if not compat.YAML_ENABLED:
        return json.loads(content)
    import yaml

    if "json" in content_type:
        return json.loads(content)
    if "yaml" in content_type:
        return yaml.safe_load(content)
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        try:
            return yaml.safe_load(content)
        except yaml.error.YAMLError:
            pass
        raise exc


def _get_content_type(conn) -> str:
    """Pull out mime type from a connection.

    Prefer explicit header if available, otherwise guess from url.
    """
    content_type = mimetypes.guess_type(conn.url)[0] or ""
    if hasattr(conn, "getheaders"):
        content_type = dict(conn.getheaders()).get("Content-Type", content_type)
    return cgi.parse_header(content_type)[0]

import json
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path
from typing import List, Literal, Optional
from urllib.parse import urlparse
from urllib.request import urlopen

from jsonschema_lint import utils
from jsonschema_lint._cli import constants
from jsonschema_lint._cli.schema_loader import load_schema


@dataclass
class RuleStack:
    cwd: Path = field(default_factory=Path.cwd)
    schema_store: bool = False
    schema_override: Optional[Path] = None

    _cache: dict = field(default_factory=dict)

    def rule_for(self, path: Path) -> Optional["Rule"]:
        if path not in self._cache:
            self._cache[path] = self._rule_for(path)
        return self._cache[path]

    def _rule_for(self, path: Path) -> Optional["Rule"]:
        if self.schema_override:
            return Rule(owner=Path.cwd(), glob="**/*", schema_uri=str(self.schema_override), mode=None)
        for rule in self.local_rules:
            if rule.match(path):
                return rule
        for rule in self.remote_rules:
            if rule.match(path):
                return rule
        return None

    @cached_property
    def local_rules(self) -> List["Rule"]:
        return Rule.from_tree(self.cwd)

    @property
    def remote_rules(self) -> List["Rule"]:
        if not self.schema_store:
            return []
        return get_schema_store_rules()


@dataclass
class Rule:
    owner: Path
    glob: str
    schema_uri: str
    mode: Optional[Literal["json", "yaml"]] = None

    @property
    def schema(self):
        return load_schema(self.resolved_schema_uri)

    def match(self, path: Path) -> bool:
        return utils.path_match(path, self.glob)

    @cached_property
    def resolved_schema_uri(self) -> str:
        url = urlparse(self.schema_uri)
        if not url.scheme:
            return (self.owner / self.schema_uri).as_uri()
        return self.schema_uri

    @classmethod
    @lru_cache(maxsize=None)
    def from_tree(cls, root: Path) -> List["Rule"]:
        root = root.absolute()
        config_filepath = root / constants.CONFIG_FILENAME
        result = []
        if config_filepath.exists() and config_filepath.is_file():
            result += cls.from_file(config_filepath)
        if root.parent == root:
            return result
        return result + cls.from_tree(root.parent)

    @classmethod
    def from_file(cls, owner: Path) -> List["Rule"]:
        return list(filter(None, (cls.from_line(owner, line) for line in reversed(owner.read_text().splitlines()))))

    @classmethod
    def from_line(cls, owner: Path, line: str) -> Optional["Rule"]:
        line = line.split("#", 1)[0].strip()  # Remove comments
        if not line:
            return None
        parts = line.split()
        if len(parts) in (2, 3):
            return cls(
                owner=owner.parent, glob=parts[0], schema_uri=parts[1], mode=parts[2] if len(parts) == 3 else None  # type: ignore[arg-type]
            )
        return None


@lru_cache(maxsize=1)
def get_schema_store_rules():
    catalog = schema_store_catalog()
    return [
        Rule(
            owner=Path("/"),
            glob=glob,
            schema_uri=rule["url"],
        )
        for rule in catalog["schemas"]
        for glob in (rule.get("fileMatch") or [])
    ]


@lru_cache(maxsize=1)
def schema_store_catalog() -> dict:
    with urlopen("https://www.schemastore.org/api/json/catalog.json") as conn:
        return json.load(conn)

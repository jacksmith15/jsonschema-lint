import importlib

YAML_ENABLED: bool

try:
    importlib.import_module("yaml")
    YAML_ENABLED = True
except ImportError:
    YAML_ENABLED = False

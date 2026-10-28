"""
Configuration loader and schema validator for SA-Engine.
"""

import yaml
from typing import Any
from pathlib import Path


class ConfigDict(dict):
    """Dictionary supporting dot-notation attribute access."""

    def __getattr__(self, key: str) -> Any:
        try:
            val = self[key]
            if isinstance(val, dict) and not isinstance(val, ConfigDict):
                val = ConfigDict(val)
                self[key] = val
            return val
        except KeyError:
            raise AttributeError(f"No configuration parameter named '{key}'")

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


def get_default_config_path() -> Path:
    """Return the default path to config.yaml."""
    return Path(__file__).resolve().parent / "config.yaml"


def load_config(config_path: str | Path | None = None) -> ConfigDict:
    """Load configuration from a YAML file.

    Args:
        config_path: Optional path to YAML configuration. Defaults to config/config.yaml.

    Returns:
        ConfigDict: Dot-accessible configuration tree.
    """
    path = Path(config_path) if config_path else get_default_config_path()

    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return ConfigDict(data)

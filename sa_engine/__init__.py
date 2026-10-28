from pathlib import Path

# Ensure root config directory is discoverable as sa_engine.config in local development
_root_dir = Path(__file__).resolve().parent.parent
if (_root_dir / "config").is_dir():
    _root_str = str(_root_dir)
    if _root_str not in __path__:
        __path__.append(_root_str)


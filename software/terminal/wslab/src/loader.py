"""Strategy discovery: built-ins plus user strategies in ./strategies."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

from strategies.base import WSlabStrategy
from strategies.macd import MacdCrossover
from strategies.sma_ema import SmaEmaCrossover

BUILTINS = [SmaEmaCrossover, MacdCrossover]


def discover(custom_dir: Path | None = None) -> dict:
    """Return an ordered ``{display_name: strategy_class}`` mapping.

    Built-in strategies come first, followed by any custom strategies found as
    ``*.py`` files in ``custom_dir``.
    """
    found: dict = {cls.display_name(): cls for cls in BUILTINS}

    if custom_dir and custom_dir.is_dir():
        for path in sorted(custom_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            for cls in _load_module_strategies(path):
                found[cls.display_name()] = cls
    return found


def _load_module_strategies(path: Path) -> list:
    mod_name = f"wslab_custom_{path.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        return []
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # don't let one bad file sink the app
        print(
            f"[wslab] Failed to load custom strategy {path.name}: {exc}",
            file=sys.stderr,
        )
        return []

    return [
        obj
        for _, obj in inspect.getmembers(module, inspect.isclass)
        if issubclass(obj, WSlabStrategy)
        and obj is not WSlabStrategy
        and obj.__module__ == mod_name
    ]

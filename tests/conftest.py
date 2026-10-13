# tests/conftest.py
"""Test-harness setup.

Two pre-existing layout problems stop the suite from collecting:

1. ``src`` has no importable package file (``src/_init_.py`` is misspelled), so
   ``from src import ...`` raises ImportError. Rather than change the shipped
   package layout, a stand-in module is registered here that re-exports the
   public names of each ``src`` module.
2. ``src/cli.py`` and siblings use sibling-absolute imports
   (``from parser import ...``), so ``src/`` must be importable on its own.

Both are test-only concerns; production code is untouched.
"""
import importlib
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# (2) src/ modules import each other by bare name
for path in (str(SRC), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

# (1) register a `src` package that re-exports the public names
if "src" not in sys.modules:
    pkg = types.ModuleType("src")
    pkg.__path__ = [str(SRC)]
    pkg.__doc__ = "Test shim for the src/ package."
    for modname in (
        "parser", "cleaner", "qc", "analysis", "plots",
        "reporter", "interpretation", "cli", "melt", "utils",
    ):
        try:
            mod = importlib.import_module(modname)
        except ImportError:
            continue
        for attr in dir(mod):
            if not attr.startswith("_"):
                setattr(pkg, attr, getattr(mod, attr))
    sys.modules["src"] = pkg

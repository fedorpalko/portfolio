"""WSLAB entrypoint. Launches the Textual app."""

import sys
from pathlib import Path

# Make ``src/`` importable so that ``engine``, ``strategies`` and the ``wslab``
# shim package resolve regardless of the working directory.
SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app import WSlabApp  # noqa: E402


def main() -> None:
    WSlabApp().run()


if __name__ == "__main__":
    main()

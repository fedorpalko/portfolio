"""Public import surface for custom strategies.

Custom strategy files (dropped in the top-level ``strategies/`` folder) import
the base class from here:

    from wslab.strategy import WSlabStrategy
"""

from strategies.base import WSlabStrategy

__all__ = ["WSlabStrategy"]

"""WSLAB strategy base class.

All WSLAB strategies inherit from :class:`WSlabStrategy`. Subclasses describe
*when* the strategy wants to be long or short by implementing
:meth:`longSignal` and :meth:`shortSignal`; the base class drives the
``backtesting.py`` ``next()`` loop and handles position management so
subclasses never touch trade plumbing.
"""

from __future__ import annotations

from backtesting import Strategy
from backtesting.lib import crossover  # noqa: F401  re-exported for convenience

# Class attributes that are part of WSLAB's own machinery and must never be
# treated as strategy parameters.
_RESERVED = {"name"}


class WSlabStrategy(Strategy):
    """Base class for WSLAB strategies.

    Define optimizable parameters as simple class attributes (ints/floats are
    treated as optimizable; strings/bools are configurable but fixed). Override
    :meth:`init` to register indicators with ``self.I`` and implement
    :meth:`longSignal` / :meth:`shortSignal`.
    """

    #: Human-friendly name shown in the TUI; falls back to the class name.
    name: str | None = None

    def init(self):  # noqa: D401 - subclasses extend this
        """Register indicators. Override in subclasses (optional)."""

    def longSignal(self) -> bool:
        """Return ``True`` when the strategy wants to be long."""
        return False

    def shortSignal(self) -> bool:
        """Return ``True`` when the strategy wants to be short / flat."""
        return False

    def next(self):
        go_long = bool(self.longSignal())
        go_short = bool(self.shortSignal())

        if go_long and not self.position.is_long:
            if self.position.is_short:
                self.position.close()
            self.buy()
        elif go_short and not self.position.is_short:
            if self.position.is_long:
                self.position.close()
            self.sell()

    # -- introspection -----------------------------------------------------
    @classmethod
    def display_name(cls) -> str:
        return cls.name or cls.__name__

    @classmethod
    def description(cls) -> str:
        return (cls.__doc__ or "No description provided.").strip()

    @classmethod
    def get_params(cls) -> dict:
        """Return user-defined parameters as ``{name: default}``.

        Walks the MRO collecting simple class attributes (int/float/str/bool)
        declared on subclasses of :class:`WSlabStrategy`.
        """
        params: dict = {}
        for klass in reversed(cls.__mro__):
            if klass in (WSlabStrategy, Strategy, object):
                continue
            for key, value in vars(klass).items():
                if key.startswith("_") or key in _RESERVED:
                    continue
                if isinstance(value, (bool, int, float, str)):
                    params[key] = value
        return params

    @classmethod
    def numeric_params(cls) -> dict:
        """Return only the numeric (optimizable) parameters."""
        return {
            k: v
            for k, v in cls.get_params().items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        }

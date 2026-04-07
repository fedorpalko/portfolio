"""
tomato.py — Tomatoes Trend-Following Strategy
IMC Prosperity 4 — Tutorial Round

Strategy rationale:
  Tomatoes are a drifting asset (observed: -49 drift on day -1, +6.5 on day -2).
  Tick-level up/down split is ~50/50, so tick momentum is noise.
  The drift plays out at a macro timescale (~thousands of timestamps).
  
  Approach: Dual EMA crossover (fast=20, slow=50) on mid-price history.
    - Fast EMA crosses above slow → go long (trend up)
    - Fast EMA crosses below slow → go short (trend down)
  
  We also layer in a soft market-make on top to collect spread while flat:
    - When no trend signal, post a 1-tick spread around mid-price
    - When trend is strong, take liquidity aggressively in trend direction
  
  Position limit: 80
  
  NOTE: traderData is used to persist EMA state across ticks (JSON string).
"""

import json
from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict, Optional

PRODUCT = "TOMATOES"
POSITION_LIMIT = 80

# EMA periods (in ticks; each tick = 100 timestamp units)
FAST_PERIOD = 20
SLOW_PERIOD = 50

# Trend signal threshold: |fast - slow| must exceed this to enter
SIGNAL_THRESHOLD = 2.0

# Trend trade size
TREND_SIZE = 15

# Market-make edge (when no trend)
MM_EDGE = 2
MM_SIZE = 5


def ema_update(prev_ema: Optional[float], price: float, period: int) -> float:
    """Exponential moving average update."""
    if prev_ema is None:
        return price
    k = 2.0 / (period + 1)
    return price * k + prev_ema * (1 - k)


def get_mid(od: OrderDepth) -> Optional[float]:
    if not od.buy_orders or not od.sell_orders:
        return None
    best_bid = max(od.buy_orders.keys())
    best_ask = min(od.sell_orders.keys())
    return (best_bid + best_ask) / 2.0


def load_state(trader_data: str) -> dict:
    if not trader_data:
        return {"fast_ema": None, "slow_ema": None, "prev_signal": 0}
    try:
        return json.loads(trader_data)
    except Exception:
        return {"fast_ema": None, "slow_ema": None, "prev_signal": 0}


def tomato_orders(state: TradingState, s: dict) -> List[Order]:
    orders: List[Order] = []

    if PRODUCT not in state.order_depths:
        return orders

    od: OrderDepth = state.order_depths[PRODUCT]
    pos = state.position.get(PRODUCT, 0)
    mid = get_mid(od)

    if mid is None:
        return orders

    # Update EMAs
    s["fast_ema"] = ema_update(s.get("fast_ema"), mid, FAST_PERIOD)
    s["slow_ema"] = ema_update(s.get("slow_ema"), mid, SLOW_PERIOD)

    fast = s["fast_ema"]
    slow = s["slow_ema"]
    diff = fast - slow

    best_bid = max(od.buy_orders.keys())
    best_ask = min(od.sell_orders.keys())

    # ── Trend signal ───────────────────────────────────────────────────────
    if diff > SIGNAL_THRESHOLD:
        # Uptrend → want to be long
        # Take best ask if we have room
        target_pos = POSITION_LIMIT
        if pos < target_pos:
            buy_qty = min(TREND_SIZE, target_pos - pos, -od.sell_orders[best_ask])
            if buy_qty > 0:
                orders.append(Order(PRODUCT, best_ask, buy_qty))

    elif diff < -SIGNAL_THRESHOLD:
        # Downtrend → want to be short
        target_pos = -POSITION_LIMIT
        if pos > target_pos:
            sell_qty = min(TREND_SIZE, pos - target_pos, od.buy_orders[best_bid])
            if sell_qty > 0:
                orders.append(Order(PRODUCT, best_bid, -sell_qty))

    else:
        # No trend → soft market-make around mid
        our_bid = int(mid) - MM_EDGE
        our_ask = int(mid) + MM_EDGE

        bid_room = POSITION_LIMIT - pos
        ask_room = POSITION_LIMIT + pos

        bid_qty = min(MM_SIZE, bid_room)
        ask_qty = min(MM_SIZE, ask_room)

        if bid_qty > 0:
            orders.append(Order(PRODUCT, our_bid, bid_qty))
        if ask_qty > 0:
            orders.append(Order(PRODUCT, our_ask, -ask_qty))

    return orders


class Trader:
    def run(self, state: TradingState) -> tuple:
        s = load_state(state.traderData)

        orders = tomato_orders(state, s)

        result: Dict[str, List[Order]] = {}
        if orders:
            result[PRODUCT] = orders

        new_trader_data = json.dumps(s)
        conversions = 0

        return result, conversions, new_trader_data
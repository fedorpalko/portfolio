"""
emerald.py — Emeralds Market-Making Strategy
IMC Prosperity 4 — Tutorial Round

Strategy rationale:
  Emeralds are a stationary mean-reverting asset pinned at 10,000.
  Observed spread is consistently ~16 (bid ~9992, ask ~10008).
  We exploit this with a tight market-making strategy:
    - Post bids slightly above best bid when we're not max-long
    - Post asks slightly below best ask when we're not max-short
    - Aggressively take any quote that crosses our fair value by > threshold
  Position limit: 80 (per backtester data.py)

Fair value = 10,000 (hard-coded; data confirms it never deviates more than ±4).
We shade our quotes based on current inventory to avoid leaning too hard.
"""

from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict

PRODUCT = "EMERALDS"
POSITION_LIMIT = 80
FAIR_VALUE = 10_000

# How many ticks inside the market we post (competitive but not crossing)
MAKE_EDGE = 1
# Minimum edge we require to hit an existing quote (take liquidity)
TAKE_THRESHOLD = 2
# Inventory skew: reduce quote size by 1 for every SKEW_UNIT units of position
SKEW_UNIT = 10
# Base order size
BASE_SIZE = 10


def get_position(state: TradingState, product: str) -> int:
    return state.position.get(product, 0)


def emerald_orders(state: TradingState) -> List[Order]:
    orders: List[Order] = []

    if PRODUCT not in state.order_depths:
        return orders

    od: OrderDepth = state.order_depths[PRODUCT]
    pos = get_position(state, PRODUCT)

    # ── 1. TAKE liquidity if someone is pricing badly ──────────────────────
    # If best ask is below fair - threshold → buy it
    if od.sell_orders:
        best_ask = min(od.sell_orders.keys())
        best_ask_vol = -od.sell_orders[best_ask]  # sell_orders have negative volumes in Prosperity
        if best_ask < FAIR_VALUE - TAKE_THRESHOLD:
            buy_qty = min(best_ask_vol, POSITION_LIMIT - pos)
            if buy_qty > 0:
                orders.append(Order(PRODUCT, best_ask, buy_qty))
                pos += buy_qty  # update shadow position

    if od.buy_orders:
        best_bid = max(od.buy_orders.keys())
        best_bid_vol = od.buy_orders[best_bid]
        if best_bid > FAIR_VALUE + TAKE_THRESHOLD:
            sell_qty = min(best_bid_vol, POSITION_LIMIT + pos)
            if sell_qty > 0:
                orders.append(Order(PRODUCT, best_bid, -sell_qty))
                pos -= sell_qty

    # ── 2. MAKE quotes around fair value ──────────────────────────────────
    # Inventory skew: if we're long, drop bid size and tighten bid price;
    # if we're short, drop ask size and tighten ask price.
    skew = pos / POSITION_LIMIT  # ranges -1 to +1

    # Quote prices
    our_bid = FAIR_VALUE - MAKE_EDGE
    our_ask = FAIR_VALUE + MAKE_EDGE

    # Quote sizes (inventory-adjusted, ensure we don't breach limits)
    bid_room = POSITION_LIMIT - pos
    ask_room = POSITION_LIMIT + pos

    # Reduce size when skewed to avoid doubling down
    bid_size = max(1, int(BASE_SIZE * (1 - max(skew, 0))))
    ask_size = max(1, int(BASE_SIZE * (1 + min(skew, 0))))

    bid_qty = min(bid_size, bid_room)
    ask_qty = min(ask_size, ask_room)

    if bid_qty > 0:
        orders.append(Order(PRODUCT, our_bid, bid_qty))
    if ask_qty > 0:
        orders.append(Order(PRODUCT, our_ask, -ask_qty))

    return orders


class Trader:
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        result: Dict[str, List[Order]] = {}
        result[PRODUCT] = emerald_orders(state)
        return result
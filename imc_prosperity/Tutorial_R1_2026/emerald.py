from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict

PRODUCT = "EMERALDS"
POSITION_LIMIT = 80
FAIR_VALUE = 10_000

# One tick inside the bots for queue priority
BID_PRICE = 9_993
ASK_PRICE = 10_007

# If position gets too extreme, rebalance by taking bot liquidity
REBALANCE_THRESHOLD = 50  # if |pos| > this, start taking the other side

BASE_SIZE = 30


def emerald_orders(state: TradingState) -> List[Order]:
    orders: List[Order] = []

    if PRODUCT not in state.order_depths:
        return orders

    od: OrderDepth = state.order_depths[PRODUCT]
    pos = state.position.get(PRODUCT, 0)

    # ── 1. TAKE bot quotes to rebalance if position is extreme ────────────
    # If we're very long, hit the bot ask isn't useful — sell into bots' bid
    if pos > REBALANCE_THRESHOLD and od.buy_orders:
        best_bid = max(od.buy_orders.keys())  # bot bid at 9992
        qty = min(od.buy_orders[best_bid], pos - REBALANCE_THRESHOLD // 2)
        if qty > 0:
            orders.append(Order(PRODUCT, best_bid, -qty))
            pos -= qty

    elif pos < -REBALANCE_THRESHOLD and od.sell_orders:
        best_ask = min(od.sell_orders.keys())  # bot ask at 10008
        qty = min(-od.sell_orders[best_ask], -REBALANCE_THRESHOLD // 2 - pos)
        if qty > 0:
            orders.append(Order(PRODUCT, best_ask, qty))
            pos += qty

    # ── 2. MAKE quotes one tick inside the bots ───────────────────────────
    # Inventory skew: compress quotes toward fair value as position grows
    # so we're more eager to unwind and less eager to grow the position
    skew = pos / POSITION_LIMIT  # -1 to +1

    # Shift both sides by skew so the book leans toward unwind
    bid_shift = round(skew * 3)
    ask_shift = round(skew * 3)

    our_bid = BID_PRICE - bid_shift
    our_ask = ASK_PRICE - ask_shift

    bid_room = POSITION_LIMIT - pos
    ask_room = POSITION_LIMIT + pos

    bid_qty = min(BASE_SIZE, bid_room)
    ask_qty = min(BASE_SIZE, ask_room)

    # Safety: never post a bid above or ask below fair value
    if our_bid < FAIR_VALUE and bid_qty > 0:
        orders.append(Order(PRODUCT, our_bid, bid_qty))
    if our_ask > FAIR_VALUE and ask_qty > 0:
        orders.append(Order(PRODUCT, our_ask, -ask_qty))

    return orders


class Trader:
    def run(self, state: TradingState) -> tuple:
        result: Dict[str, List[Order]] = {}
        result[PRODUCT] = emerald_orders(state)
        return result, 0, ""
# query.py
from typing import List, Callable

from ..object import Option
from .filter import ConfigFilter


class OptionFilter:
    def __init__(self, universe: List[Option], spot: float):
        self.universe = universe
        self.spot = spot

    def filter(self, cond: Callable[[Option], bool]) -> 'OptionFilter':
        self.universe = [o for o in self.universe if cond(o)]
        return self

    def apply_filter(self, cfg: ConfigFilter):
        # ==================== OPTION-LEVEL FILTERS ====================
        # These filters apply to individual options before strategy construction
        
        # volume filter
        if cfg.min_volume is not None:
            self.filter(lambda o: (o.volume or 0) >= cfg.min_volume)

        # open interest
        if cfg.min_oi is not None:
            self.filter(lambda o: (o.oi or 0) >= cfg.min_oi)

        if cfg.min_price is not None:
            self.filter(lambda o: (o.price() or 0) >= cfg.min_price)

        # expiry filter
        if cfg.expiry is not None:
            self.filter(lambda o: o.expiry == cfg.expiry)

        # days to expiry range filter
        if cfg.days_to_expiry_range is not None:
            min_days, max_days = cfg.days_to_expiry_range
            self.filter(lambda o: o.days_to_expiry is not None and min_days <= o.days_to_expiry <= max_days)

        # volume ratio range filter (removes fake volume spikes)
        if cfg.volume_ratio_range is not None:
            min_ratio, max_ratio = cfg.volume_ratio_range
            self.filter(lambda o: o.volume_ratio() is not None and min_ratio <= o.volume_ratio() <= max_ratio)

        # max bid/ask spread filter (require tight spreads, avoid illiquid options)
        if cfg.max_bid_ask_spread is not None:
            self.filter(lambda o: o.bid_ask_spread() is not None and o.bid_ask_spread() <= cfg.max_bid_ask_spread)

        return self

    def result(self) -> List[Option]:
        return self.universe


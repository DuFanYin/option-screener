# generator_class.py
from abc import ABC, abstractmethod
from typing import List

from ..object import Option, ConfigFilter
from ..factory.option_filter import OptionFilter
from .strategy_class import SingleLeg, IronCondor, Straddle, Strangle, ForwardVolPair


# ===================== STRATEGY GENERATORS =====================
class StrategyGenerator(ABC):
    """Base class for strategy generators"""
    def __init__(self, options: List[Option], spot: float):
        self.options = options
        self.spot = spot

    @abstractmethod
    def generate(self, cfg: ConfigFilter) -> List:
        """Generate strategies based on config"""
        ...


class SingleCallsGenerator(StrategyGenerator):
    """Generator for single call strategies"""
    def generate(self, cfg: ConfigFilter) -> List:
        query = OptionFilter(self.options, self.spot).apply_filter(cfg)
        opts = query.filter(lambda o: o.is_call() and o.is_otm(self.spot)).result()

        direction_str = cfg.direction.value
        action = "SELL" if direction_str == "SHORT" else "BUY"
        strategies = [SingleLeg(opt, action, direction=direction_str) for opt in opts]
        return strategies


class IronCondorsGenerator(StrategyGenerator):
    """Generator for iron condor strategies"""
    def generate(self, cfg: ConfigFilter) -> List:
        opts = OptionFilter(self.options, self.spot).apply_filter(cfg).result()
        direction_str = cfg.direction.value

        # Group by expiry
        expiry_map: dict[str, List[Option]] = {}
        for opt in opts:
            expiry_map.setdefault(opt.expiry, []).append(opt)

        strategies = []
        for expiry, chain in expiry_map.items():
            calls = sorted([o for o in chain if o.is_call()], key=lambda o: o.strike)
            puts = sorted([o for o in chain if o.is_put()], key=lambda o: o.strike)

            short_calls = [c for c in calls if c.strike > self.spot]
            short_puts = [p for p in puts if p.strike < self.spot]

            # Generate iron condor combinations
            for short_call in short_calls:
                buy_calls = [bc for bc in calls if bc.strike > short_call.strike]
                for buy_call in buy_calls:
                    for short_put in short_puts:
                        buy_puts = [bp for bp in puts if bp.strike < short_put.strike]
                        for buy_put in buy_puts:
                            strategies.append(IronCondor(
                                short_call, buy_call, short_put, buy_put, direction=direction_str
                            ))

        return strategies


class StraddlesGenerator(StrategyGenerator):
    """Generator for straddle strategies"""
    def generate(self, cfg: ConfigFilter) -> List:
        opts = OptionFilter(self.options, self.spot).apply_filter(cfg).result()
        direction_str = cfg.direction.value

        # Group by expiry
        expiry_map: dict[str, List[Option]] = {}
        for opt in opts:
            expiry_map.setdefault(opt.expiry, []).append(opt)

        strategies = []
        for expiry, chain in expiry_map.items():
            calls = sorted([o for o in chain if o.is_call()], key=lambda o: o.strike)
            puts = sorted([o for o in chain if o.is_put()], key=lambda o: o.strike)

            # Find ATM or closest to ATM strikes
            # For straddle, we need call and put at the same strike
            for call in calls:
                # Find put at same strike
                matching_puts = [p for p in puts if p.strike == call.strike]
                for put in matching_puts:
                    strategies.append(Straddle(call, put, direction=direction_str))

        return strategies


class StranglesGenerator(StrategyGenerator):
    """Generator for strangle strategies"""
    def generate(self, cfg: ConfigFilter) -> List:
        opts = OptionFilter(self.options, self.spot).apply_filter(cfg).result()
        direction_str = cfg.direction.value

        # Group by expiry
        expiry_map: dict[str, List[Option]] = {}
        for opt in opts:
            expiry_map.setdefault(opt.expiry, []).append(opt)

        strategies = []
        for expiry, chain in expiry_map.items():
            calls = sorted([o for o in chain if o.is_call() and o.strike > self.spot], key=lambda o: o.strike)
            puts = sorted([o for o in chain if o.is_put() and o.strike < self.spot], key=lambda o: o.strike)

            # Generate strangle combinations: OTM call + OTM put
            # Call strike > spot, Put strike < spot
            for call in calls:
                for put in puts:
                    strategies.append(Strangle(call, put, direction=direction_str))

        return strategies


class ForwardVolsGenerator(StrategyGenerator):
    """Generator computing forward volatility between two expirations for same side/strike."""
    def generate(self, cfg: ConfigFilter) -> List:
        # Start from filtered options
        opts = OptionFilter(self.options, self.spot).apply_filter(cfg).result()

        # Group by expiry
        expiry_map: dict[str, List[Option]] = {}
        for opt in opts:
            expiry_map.setdefault(opt.expiry, []).append(opt)

        # Build mapping by (side, strike) per expiry
        by_key_by_expiry: dict[str, dict[tuple, List[Option]]] = {}
        for expiry, chain in expiry_map.items():
            by_key: dict[tuple, List[Option]] = {}
            for o in chain:
                key = (o.side, o.strike)
                by_key.setdefault(key, []).append(o)
            by_key_by_expiry[expiry] = by_key

        # Sort expiries ascending
        expiries = sorted(expiry_map.keys())

        strategies: List[ForwardVolPair] = []
        # For each pair of expiries (shorter, longer)
        for i in range(len(expiries)):
            for j in range(i + 1, len(expiries)):
                e1, e2 = expiries[i], expiries[j]
                m1, m2 = by_key_by_expiry[e1], by_key_by_expiry[e2]
                # For each key present in both expiries
                for key in set(m1.keys()).intersection(m2.keys()):
                    # Use first occurrence per key
                    o1 = sorted(m1[key], key=lambda x: x.strike)[0]
                    o2 = sorted(m2[key], key=lambda x: x.strike)[0]

                    # Compute T in years using days_to_expiry
                    T1 = max(o1.days_to_expiry, 0) / 365.0
                    T2 = max(o2.days_to_expiry, 0) / 365.0
                    if T2 <= T1:
                        continue

                    iv1 = o1.iv or 0.0
                    iv2 = o2.iv or 0.0
                    num = iv2 * iv2 * T2 - iv1 * iv1 * T1
                    den = T2 - T1
                    if den <= 0 or num <= 0:
                        continue

                    fv = (num / den) ** 0.5

                    strat = ForwardVolPair(o1, o2, fv)

                    # Strategy-level filter for forward_vol
                    if cfg.forward_vol_range is not None:
                        lo, hi = cfg.forward_vol_range
                        if not (lo <= fv <= hi):
                            continue

                    strategies.append(strat)

        return strategies


# generator_class.py
from abc import ABC, abstractmethod
from typing import List

from ..object import Option, ConfigFilter
from ..factory.option_filter import OptionFilter
from .strategy_class import SingleLeg, IronCondor, Straddle, Strangle


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
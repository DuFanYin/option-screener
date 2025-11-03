# factory.py
from typing import Optional, Tuple, List, Callable

from ..object import Option, Direction, StrategyFilter, ConfigFilter
from ..strategy.generator_class import (
    SingleCallsGenerator,
    IronCondorsGenerator,
    StraddlesGenerator,
    StranglesGenerator,
    ForwardVolsGenerator,
)

class StrategyList(list):
    def __init__(self, items, factory):
        super().__init__(items)
        self._factory = factory

    def rank(self, key: str = "rr", reverse: bool = True) -> 'StrategyList':
        if not self:
            return StrategyList([], self._factory)

        # Ranking key functions
        rankers: dict[str, Callable] = {
            "rr": lambda s: s.rr(),
            "gain": lambda s: s.max_gain(),
            "loss": lambda s: s.max_loss(),
            "cost": lambda s: s.cost(),
        }

        if key in rankers:
            key_func = rankers[key]
            # Special handling for loss (ascending)
            if key == "loss":
                sorted_list = sorted(self, key=key_func)
            else:
                sorted_list = sorted(self, key=key_func, reverse=reverse)
        else:
            sorted_list = list(self)

        return StrategyList(sorted_list, self._factory)

    def top(self, n=10):
        return StrategyList(self[:n], self._factory)

    def to_df(self):
        import pandas as pd
        rows = [{
            "strategy": s.pretty(),
            "cost": s.cost(),
            "max_gain": s.max_gain(),
            "max_loss": s.max_loss(),
            "rr": s.rr(),
            "delta": s.net_delta(),
            "theta": s.net_theta(),
            "vega": s.net_vega(),
            "iv": s.avg_iv(),
        } for s in self]
        return pd.DataFrame(rows)


# ===================== FACTORY =====================
class StrategyFactory:
    def __init__(self, options: List[Option], spot: float):
        self.options = options
        self.spot = spot
        # Registry mapping strategy filter fields to generators
        self._generators = {
            'single_calls': SingleCallsGenerator(options, spot),
            'iron_condors': IronCondorsGenerator(options, spot),
            'straddles': StraddlesGenerator(options, spot),
            'strangles': StranglesGenerator(options, spot),
            'forward_vols': ForwardVolsGenerator(options, spot),
        }

    def strategy(self, s_filter: StrategyFilter, c_filter: ConfigFilter) -> StrategyList:
        """Generate strategies with filter and config"""
        return self.generate(s_filter, c_filter)

    def generate(self, s_filter: StrategyFilter, c_filter: ConfigFilter) -> StrategyList:
        """Generate all strategies based on s_filter and apply c_filter filters"""
        all_strategies = []
        
        # Use registry to generate strategies
        for filter_field, generator in self._generators.items():
            if getattr(s_filter, filter_field, False):
                strategies = generator.generate(c_filter)
                filtered = self._filter_strategies(strategies, c_filter)
                all_strategies.extend(filtered)
        
        return StrategyList(all_strategies, self)

    @staticmethod
    def _check_range(value: Optional[float], range_tuple: Optional[Tuple[float, float]]) -> bool:
        """Helper method to check if a value falls within a range."""
        if range_tuple is None:
            return True
        if value is None:
            return False
        min_val, max_val = range_tuple
        return min_val <= value <= max_val

    # ---------- INTERNAL STRATEGY FILTER ----------
    # ==================== STRATEGY-LEVEL FILTERS ====================
    def _filter_strategies(self, strategies: List, c_filter: ConfigFilter) -> List:
        filtered = []

        for strategy in strategies:

            # ---- Debit Filter ----
            if c_filter.debit_range and strategy.debit() > 0:
                if not self._check_range(strategy.debit(), c_filter.debit_range):
                    continue

            # ---- Credit Filter ----
            if c_filter.credit_range and strategy.credit() > 0:
                if not self._check_range(strategy.credit(), c_filter.credit_range):
                    continue

            # ---- Metric Range Checks ----
            metrics = [
                (strategy.max_gain(),    c_filter.potential_gain_range),
                (strategy.max_loss(),    c_filter.potential_loss_range),
                (strategy.rr(),          c_filter.rr_range),
                (strategy.net_delta(),   c_filter.net_delta_range),
                (strategy.net_theta(),   c_filter.net_theta_range),
                (strategy.net_vega(),    c_filter.net_vega_range),
                (strategy.avg_iv(),      c_filter.iv_range),
            ]


            ok = True
            for val, rng in metrics:
                if not self._check_range(val, rng):
                    ok = False
                    break

            if ok:
                filtered.append(strategy)

        return filtered


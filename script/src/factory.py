# factory.py
from .object import SingleLeg, IronCondor, Option
from dataclasses import dataclass
from typing import Optional, Tuple, List

from .config import StrategyConfig


# ranking.py
class StrategyRanking:
    @staticmethod
    def by_rr(strats):
        return sorted(strats, key=lambda strategy: strategy.rr(), reverse=True)

    @staticmethod
    def by_profit(strats):
        return sorted(strats, key=lambda strategy: strategy.max_gain(), reverse=True)

    @staticmethod
    def by_cost(strats):
        return sorted(strats, key=lambda strategy: strategy.cost())

# ============================================================
# ✅ FILTER WRAPPER FOR OPTIONS
# ============================================================
class OptionQuery:
    def __init__(self, universe: List[Option], spot: float):
        self.u = universe
        self.spot = spot

    def filter(self, cond):
        self.u = [o for o in self.u if cond(o)]
        return self

    def apply_config(self, cfg: StrategyConfig):
        # ==================== OPTION-LEVEL FILTERS ====================
        # These filters apply to individual options before strategy construction
        
        # volume filter
        if cfg.min_volume is not None:
            self.filter(lambda o: (o.volume or 0) >= cfg.min_volume)

        # open interest
        if cfg.min_oi is not None:
            self.filter(lambda o: (o.oi or 0) >= cfg.min_oi)

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
        return self.u



# ============================================================
# ✅ STRATEGY FACTORY
# ============================================================

# ============= Helper Wrapper for returned results =============
class StrategyList(list):
    def __init__(self, items, factory):
        super().__init__(items)
        self._factory = factory

    def rank(self, key="rr", reverse=True):
        if not self:
            return StrategyList([], self._factory)

        if key == "rr":
            sorted_list = sorted(self, key=lambda s: s.rr(), reverse=reverse)
        elif key == "gain":
            sorted_list = sorted(self, key=lambda s: s.max_gain(), reverse=reverse)
        elif key == "loss":
            sorted_list = sorted(self, key=lambda s: s.max_loss())
        elif key == "cost":
            sorted_list = sorted(self, key=lambda s: s.cost())
        elif key == "credit" and hasattr(self[0], "credit"):
            sorted_list = sorted(self, key=lambda s: s.credit(), reverse=reverse)
        else:
            sorted_list = list(self)

        return StrategyList(sorted_list, self._factory)

    def top(self, n=10):
        return StrategyList(self[:n], self._factory)

    def to_df(self):
        import pandas as pd
        rows = []
        for s in self:
            rows.append({
                "strategy": s.pretty(),
                "cost": s.cost(),
                "max_gain": s.max_gain(),
                "max_loss": s.max_loss(),
                "rr": s.rr(),
                "delta": s.net_delta(),
                "theta": s.net_theta(),
                "vega": s.net_vega(),
                "iv": s.avg_iv(),
            })
        return pd.DataFrame(rows)


# ===================== FACTORY =====================
class StrategyFactory:
    def __init__(self, options: List[Option], spot: float):
        self.options = options
        self.spot = spot


    # ---------- INTERNAL STRATEGY FILTER ----------
    # ==================== STRATEGY-LEVEL FILTERS ====================
    # These filters apply after strategies are constructed
    def _filter_strategies(self, strategies, cfg: StrategyConfig):
        out = []
        for s in strategies:

            # --- debit / credit ---
            if cfg.debit_range is not None:
                min_debit, max_debit = cfg.debit_range
                cost = s.cost()
                if cost is None or not (min_debit <= cost <= max_debit):
                    continue
            if hasattr(s, "credit"):
                if cfg.credit_range is not None:
                    min_credit, max_credit = cfg.credit_range
                    credit = s.credit()
                    if credit is None or not (min_credit <= credit <= max_credit):
                        continue

            # --- potential gain range ---
            if cfg.potential_gain_range is not None:
                min_gain, max_gain = cfg.potential_gain_range
                gain = s.max_gain()
                if gain is None or not (min_gain <= gain <= max_gain):
                    continue

            # --- potential loss range ---
            if cfg.potential_loss_range is not None:
                min_loss, max_loss = cfg.potential_loss_range
                loss = s.max_loss()
                if loss is None or not (min_loss <= loss <= max_loss):
                    continue

            # --- RR range ---
            if cfg.rr_range is not None:
                min_rr, max_rr = cfg.rr_range
                rr = s.rr()
                if rr is None or not (min_rr <= rr <= max_rr):
                    continue

            # --- net Greeks ranges ---
            if cfg.net_delta_range is not None:
                min_delta, max_delta = cfg.net_delta_range
                delta = s.net_delta()
                if delta is None or not (min_delta <= delta <= max_delta):
                    continue
            if cfg.net_theta_range is not None:
                min_theta, max_theta = cfg.net_theta_range
                theta = s.net_theta()
                if theta is None or not (min_theta <= theta <= max_theta):
                    continue
            if cfg.net_vega_range is not None:
                min_vega, max_vega = cfg.net_vega_range
                vega = s.net_vega()
                if vega is None or not (min_vega <= vega <= max_vega):
                    continue

            # --- avg IV range ---
            if cfg.iv_range is not None:
                min_iv, max_iv = cfg.iv_range
                iv = s.avg_iv()
                if iv is None or not (min_iv <= iv <= max_iv):
                    continue

            out.append(s)

        return out


    # ============================================================
    # ✅ 1: SINGLE CALL BUY
    # ============================================================
    def single_calls(self, cfg: StrategyConfig):
        q = OptionQuery(self.options, self.spot).apply_config(cfg)
        opts = q.filter(lambda o: o.is_call() and o.is_otm(self.spot)).result()

        # Determine direction: use config direction or default to LONG
        from .config import Direction
        direction = cfg.direction if cfg.direction is not None else Direction.LONG
        direction_str = direction.value if isinstance(direction, Direction) else direction
        action = "SELL" if direction_str == "SHORT" else "BUY"
        strategies = [SingleLeg(o, action, direction=direction_str) for o in opts]
        filtered = self._filter_strategies(strategies, cfg)
        return StrategyList(filtered, self)


    # ============================================================
    # ✅ 3: IRON CONDOR (SHORT)
    # ============================================================
    def iron_condors(self, cfg: StrategyConfig):
        opts = OptionQuery(self.options, self.spot).apply_config(cfg).result()

        # Determine direction: use config direction or default to SHORT for iron condors
        from .config import Direction
        direction = cfg.direction if cfg.direction is not None else Direction.SHORT
        direction_str = direction.value if isinstance(direction, Direction) else direction

        # group by expiry
        exp_map = {}
        for o in opts:
            exp_map.setdefault(o.expiry, []).append(o)

        strategies = []
        for exp, chain in exp_map.items():
            calls = sorted([o for o in chain if o.is_call()], key=lambda o: o.strike)
            puts  = sorted([o for o in chain if o.is_put()],  key=lambda o: o.strike)

            short_calls = [c for c in calls if c.strike > self.spot]
            short_puts  = [p for p in puts  if p.strike < self.spot]

            for sc in short_calls:
                for bc in calls:
                    if bc.strike <= sc.strike:
                        continue
                    for sp in short_puts:
                        for bp in puts:
                            if bp.strike >= sp.strike:
                                continue
                            strategies.append(IronCondor(sc, bc, sp, bp, direction=direction_str))

        filtered = self._filter_strategies(strategies, cfg)
        return StrategyList(filtered, self)
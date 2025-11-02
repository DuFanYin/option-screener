# factory.py
from .object import SingleLeg, VerticalSpread, IronCondor, Option

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
# factory.py

from dataclasses import dataclass
from typing import Optional, Tuple, List

from .object import SingleLeg, VerticalSpread, IronCondor, Option
from .config import StrategyConfig

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
        # volume filter
        if cfg.min_volume is not None:
            self.filter(lambda o: (o.volume or 0) >= cfg.min_volume)

        # open interest
        if cfg.min_oi is not None:
            self.filter(lambda o: (o.oi or 0) >= cfg.min_oi)

        # max price
        if cfg.max_price is not None:
            self.filter(lambda o: o.price() is not None and o.price() <= cfg.max_price)

        # expiry filter
        if cfg.expiry is not None:
            self.filter(lambda o: o.expiry == cfg.expiry)

        # strike filter
        if cfg.strikes_range is not None:
            lo, hi = cfg.strikes_range
            self.filter(lambda o: lo <= o.strike <= hi)

        # days to expiry range filter
        if cfg.days_to_expiry_range is not None:
            min_days, max_days = cfg.days_to_expiry_range
            self.filter(lambda o: o.days_to_expiry is not None and min_days <= o.days_to_expiry <= max_days)

        # min IV filter (good for selling premium)
        if cfg.min_iv is not None:
            self.filter(lambda o: o.iv is not None and o.iv >= cfg.min_iv)

        # min delta filter (filter weak/too-deep OTM legs)
        if cfg.min_delta is not None:
            self.filter(lambda o: o.delta is not None and abs(o.delta) >= cfg.min_delta)

        # max gamma filter (for low-gamma trades)
        if cfg.max_gamma is not None:
            self.filter(lambda o: o.gamma is not None and abs(o.gamma) <= cfg.max_gamma)

        # min volume ratio filter (removes fake volume spikes)
        if cfg.min_volume_ratio is not None:
            self.filter(lambda o: o.volume_ratio() is not None and o.volume_ratio() >= cfg.min_volume_ratio)

        # min bid/ask spread filter (require tight spreads, avoid illiquid options)
        # Note: min_bid_ask_spread actually means maximum allowed spread (we want spreads <= this value for tight spreads)
        if cfg.min_bid_ask_spread is not None:
            self.filter(lambda o: o.bid_ask_spread() is not None and o.bid_ask_spread() <= cfg.min_bid_ask_spread)

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
    def _filter_strategies(self, strategies, cfg: StrategyConfig):
        out = []
        for s in strategies:

            # --- debit / credit ---
            if cfg.max_debit is not None and s.cost() > cfg.max_debit:
                continue
            if cfg.min_credit is not None and hasattr(s, "credit") and s.credit() < cfg.min_credit:
                continue

            # --- RR ---
            if cfg.min_rr is not None and s.rr() < cfg.min_rr:
                continue

            # --- risk cap ---
            if cfg.max_loss is not None and s.max_loss() > cfg.max_loss:
                continue

            # --- net Greeks ---
            if cfg.max_net_delta is not None and abs(s.net_delta()) > cfg.max_net_delta:
                continue
            if cfg.max_theta is not None and abs(s.net_theta()) > cfg.max_theta:
                continue
            if cfg.max_vega is not None and abs(s.net_vega()) > cfg.max_vega:
                continue

            # --- avg IV ---
            if cfg.max_iv is not None:
                iv = s.avg_iv()
                if iv is None or iv > cfg.max_iv:
                    continue

            out.append(s)

        return out


    # ============================================================
    # ✅ 1: SINGLE CALL BUY
    # ============================================================
    def single_calls(self, cfg: StrategyConfig):
        q = OptionQuery(self.options, self.spot).apply_config(cfg)
        opts = q.filter(lambda o: o.is_call() and o.is_otm(self.spot)).result()

        strategies = [SingleLeg(o, "BUY") for o in opts]
        filtered = self._filter_strategies(strategies, cfg)
        return StrategyList(filtered, self)


    # ============================================================
    # ✅ 2: VERTICAL CALL DEBIT SPREAD
    # ============================================================
    def vertical_debit_calls(self, cfg: StrategyConfig):
        q = OptionQuery(self.options, self.spot).apply_config(cfg)
        calls = q.filter(lambda o: o.is_call() and o.is_otm(self.spot)).result()
        calls = sorted(calls, key=lambda o: (o.expiry, o.strike))

        strategies = []
        for buy in calls:
            for sell in calls:
                if sell.expiry != buy.expiry:
                    continue
                if sell.strike <= buy.strike:
                    continue

                debit = buy.price() - sell.price()
                if cfg.max_debit is not None and debit > cfg.max_debit:
                    continue

                strategies.append(VerticalSpread(buy, sell))

        filtered = self._filter_strategies(strategies, cfg)
        return StrategyList(filtered, self)


    # ============================================================
    # ✅ 3: IRON CONDOR (SHORT)
    # ============================================================
    def iron_condors(self, cfg: StrategyConfig):
        opts = OptionQuery(self.options, self.spot).apply_config(cfg).result()

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
                            strategies.append(IronCondor(sc, bc, sp, bp))

        filtered = self._filter_strategies(strategies, cfg)
        return StrategyList(filtered, self)
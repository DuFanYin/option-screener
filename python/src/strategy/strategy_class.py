# strategy_class.py
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List

from ..object import Option


# ===================== BASE STRATEGY =====================
@dataclass
class Strategy(ABC):
    direction: str  # "LONG" or "SHORT"

    @abstractmethod
    def legs(self) -> List[Option]: ...

    # Unified cash flow:
    @abstractmethod
    def debit(self) -> float:
        """How much the trader pays up front (positive cash out)."""
        ...

    @abstractmethod
    def credit(self) -> float:
        """How much the trader receives up front (positive cash in)."""
        ...

    def cost(self) -> float:
        """
        Positive = you pay net debit
        Negative = you receive net credit
        """
        return self.debit() - self.credit()

    @abstractmethod
    def max_gain(self) -> float: ...

    @abstractmethod
    def max_loss(self) -> float: ...

    def rr(self):
        loss = self.max_loss()
        return self.max_gain() / loss if loss > 0 else float("inf")

    # ========== Greeks ==========
    def net_delta(self):
        return sum((leg.delta or 0) * 100 * qty for leg, qty in self._signed_legs())

    def net_theta(self):
        return sum((leg.theta or 0) * 100 * qty for leg, qty in self._signed_legs())

    def net_vega(self):
        return sum((leg.vega or 0) * 100 * qty for leg, qty in self._signed_legs())

    def avg_iv(self):
        ivs = [leg.iv for leg, _ in self._signed_legs() if leg.iv is not None]
        return sum(ivs) / len(ivs) if ivs else None

    # Define long/short sign for each leg
    def _signed_legs(self):
        out = []
        for leg in self.legs():
            qty = 1 if self._leg_sign(leg) == "BUY" else -1
            out.append((leg, qty))
        return out

    @abstractmethod
    def _leg_sign(self, leg) -> str:  # "BUY" or "SELL"
        ...

    @abstractmethod
    def pretty(self) -> str:
        ...


# ===================== SINGLE LEG =====================
class SingleLeg(Strategy):
    def __init__(self, opt: Option, action: str, direction: str):
        self.opt = opt
        self.action = action
        self.direction = direction

    def legs(self):
        return [self.opt]

    def _leg_sign(self, leg) -> str:
        return self.action

    def debit(self) -> float:
        return self.opt.price() * 100 if self.action == "BUY" else 0.0

    def credit(self) -> float:
        return self.opt.price() * 100 if self.action == "SELL" else 0.0

    def max_gain(self):
        if self.opt.is_call():
            return float("inf")
        return self.opt.strike * 100 - self.cost()

    def max_loss(self):
        return self.cost()

    def pretty(self):
        return f"Single {self.action} {self.opt.side}@{self.opt.strike} exp {self.opt.expiry}"

    def __repr__(self):
        return (
            f"[Single {self.action}] {self.opt.side} {self.opt.strike} exp={self.opt.expiry} "
            f"cost={self.cost():.2f} rr={self.rr():.2f} "
            f"Δ={self.net_delta():.3f} Θ={self.net_theta():.3f} vega={self.net_vega():.3f}"
        )


# ===================== IRON CONDOR =====================
class IronCondor(Strategy):
    def __init__(self, sc, bc, sp, bp, direction: str):
        self.sc = sc
        self.bc = bc
        self.sp = sp
        self.bp = bp
        self.direction = direction

    def legs(self):
        return [self.sc, self.bc, self.sp, self.bp]

    def _leg_sign(self, leg) -> str:
        return "SELL" if leg in [self.sc, self.sp] else "BUY"

    def debit(self) -> float:
        return (self.bc.price() + self.bp.price()) * 100

    def credit(self) -> float:
        return (self.sc.price() + self.sp.price()) * 100

    def width(self):
        return (self.bc.strike - self.sc.strike) * 100

    def max_loss(self):
        return self.width() - self.credit()

    def max_gain(self):
        return self.credit()

    def pretty(self):
        return f"IC C:{self.sc.strike}/{self.bc.strike} P:{self.sp.strike}/{self.bp.strike} exp {self.sc.expiry}"

    def __repr__(self):
        return (
            f"[IC] C:{self.sc.strike}/{self.bc.strike} P:{self.sp.strike}/{self.bp.strike} exp={self.sc.expiry} "
            f"credit={self.credit():.2f} rr={self.rr():.2f} "
            f"Δ={self.net_delta():.3f} Θ={self.net_theta():.3f} vega={self.net_vega():.3f}"
        )


# ===================== STRADDLE =====================
class Straddle(Strategy):
    def __init__(self, call: Option, put: Option, direction: str):
        self.call = call
        self.put = put
        self.direction = direction

    def legs(self):
        return [self.call, self.put]

    def _leg_sign(self, leg) -> str:
        return "BUY" if self.direction == "LONG" else "SELL"

    def debit(self) -> float:
        total = (self.call.price() + self.put.price()) * 100
        return total if self.direction == "LONG" else 0.0

    def credit(self) -> float:
        total = (self.call.price() + self.put.price()) * 100
        return total if self.direction == "SHORT" else 0.0

    def max_gain(self):
        if self.direction == "LONG":
            return float("inf")
        return self.credit()

    def max_loss(self):
        if self.direction == "LONG":
            return self.cost()
        return float("inf")

    def pretty(self):
        return f"Straddle {self.direction} C:{self.call.strike} P:{self.put.strike} exp {self.call.expiry}"

    def __repr__(self):
        return (
            f"[Straddle {self.direction}] C:{self.call.strike} P:{self.put.strike} exp={self.call.expiry} "
            f"cost={self.cost():.2f} rr={self.rr():.2f} "
            f"Δ={self.net_delta():.3f} Θ={self.net_theta():.3f} vega={self.net_vega():.3f}"
        )


# ===================== STRANGLE =====================
class Strangle(Strategy):
    def __init__(self, call: Option, put: Option, direction: str):
        self.call = call
        self.put = put
        self.direction = direction

    def legs(self):
        return [self.call, self.put]

    def _leg_sign(self, leg) -> str:
        return "BUY" if self.direction == "LONG" else "SELL"

    def debit(self) -> float:
        total = (self.call.price() + self.put.price()) * 100
        return total if self.direction == "LONG" else 0.0

    def credit(self) -> float:
        total = (self.call.price() + self.put.price()) * 100
        return total if self.direction == "SHORT" else 0.0

    def max_gain(self):
        if self.direction == "LONG":
            return float("inf")
        return self.credit()

    def max_loss(self):
        if self.direction == "LONG":
            return self.cost()
        return float("inf")

    def pretty(self):
        return f"Strangle {self.direction} C:{self.call.strike} P:{self.put.strike} exp {self.call.expiry}"

    def __repr__(self):
        return (
            f"[Strangle {self.direction}] C:{self.call.strike} P:{self.put.strike} exp={self.call.expiry} "
            f"cost={self.cost():.2f} rr={self.rr():.2f} "
            f"Δ={self.net_delta():.3f} Θ={self.net_theta():.3f} vega={self.net_vega():.3f}"
        )


class ForwardVolPair(Strategy):
    """Non-trade analytical strategy: forward vol between two maturities for same side/strike."""
    def __init__(self, short_opt: Option, long_opt: Option, forward_vol: float):
        # direction not meaningful here; use LONG as neutral
        self.short_opt = short_opt
        self.long_opt = long_opt
        self._forward_vol = forward_vol
        self.direction = "LONG"

    def legs(self):
        return [self.short_opt, self.long_opt]

    def _leg_sign(self, leg) -> str:
        return "BUY"

    def debit(self) -> float:
        return 0.0

    def credit(self) -> float:
        return 0.0

    def max_gain(self) -> float:
        return 0.0

    def max_loss(self) -> float:
        return 0.0

    def forward_vol(self) -> float:
        return self._forward_vol

    def pretty(self) -> str:
        return (
            f"FwdVol {self.short_opt.side}@{self.short_opt.strike} "
            f"{self.short_opt.expiry}->{self.long_opt.expiry} fv={self._forward_vol:.4f}"
        )

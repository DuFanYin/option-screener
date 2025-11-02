# object.py
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, Tuple

@dataclass
class Option:
    symbol: str
    expiry: str
    strike: float
    side: str         # "CALL" or "PUT"

    mid: float
    iv: float
    volume: float
    oi: float

    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    days_to_expiry: int
    
    bid: Optional[float] = None
    ask: Optional[float] = None

    def is_call(self): return self.side == "CALL"
    def is_put(self):  return self.side == "PUT"
    
    def is_otm(self, spot):
        return (self.is_call() and self.strike > spot) or (self.is_put() and self.strike < spot)

    def price(self): return self.mid or 0.0
    def mid_price(self): return self.price()
    def liquidity(self): return (self.volume or 0) + (self.oi or 0)
    
    def bid_ask_spread(self) -> Optional[float]:
        """Calculate bid/ask spread. Returns None if bid or ask unavailable."""
        if self.bid is not None and self.ask is not None:
            return abs(self.ask - self.bid)
        return None
    
    def volume_ratio(self) -> Optional[float]:
        """Calculate volume to open interest ratio. Returns None if OI is zero."""
        if self.oi and self.oi > 0:
            return (self.volume or 0) / self.oi
        return None

    def __repr__(self):
        return f"{self.side} {self.strike} exp={self.expiry} mid={self.mid:.2f} Δ={self.delta}"

# ========================================================================
# ---------------------  Strategy Wrapper Classes  -----------------------
# ========================================================================

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List
from .object import Option


# ===================== BASE STRATEGY =====================
@dataclass
class Strategy(ABC):
    direction: str  # "LONG" or "SHORT"

    @abstractmethod
    def legs(self) -> List[Option]: ...

    @abstractmethod
    def cost(self) -> float: ...

    @abstractmethod
    def max_gain(self) -> float: ...

    @abstractmethod
    def max_loss(self) -> float: ...

    def rr(self):
        loss = self.max_loss()
        return self.max_gain() / loss if loss > 0 else float("inf")

    # ======= Greek Aggregators =======
    def net_delta(self):
        delta_sum = 0
        for leg, qty in self._signed_legs():
            if leg.delta is not None:
                delta_sum += leg.delta * 100 * qty
        return delta_sum

    def net_gamma(self):
        gamma_sum = 0
        for leg, qty in self._signed_legs():
            if leg.gamma is not None:
                gamma_sum += leg.gamma * 100 * qty
        return gamma_sum

    def net_theta(self):
        theta_sum = 0
        for leg, qty in self._signed_legs():
            if leg.theta is not None:
                theta_sum += leg.theta * 100 * qty
        return theta_sum

    def net_vega(self):
        vega_sum = 0
        for leg, qty in self._signed_legs():
            if leg.vega is not None:
                vega_sum += leg.vega * 100 * qty
        return vega_sum

    def net_rho(self):
        rho_sum = 0
        for leg, qty in self._signed_legs():
            if leg.rho is not None:
                rho_sum += leg.rho * 100 * qty
        return rho_sum

    def avg_iv(self):
        ivs = [leg.iv for leg, _ in self._signed_legs() if leg.iv is not None]
        return sum(ivs) / len(ivs) if ivs else None

    # Convert legs to (Option, +1/-1)
    def _signed_legs(self):
        """
        Returns list of (Option, qty) where:
         +1 = long / buy
         -1 = short / sell
        """
        out = []
        for option in self.legs():
            if hasattr(option, "action"):   # for SingleLeg with explicit BUY/SELL
                qty = 1 if option.action == "BUY" else -1
            else:
                # strategy knows buy/sell direction
                qty = self._leg_sign(option)
            out.append((option, qty))
        return out

    # default sign = +1 (override in subclasses)
    def _leg_sign(self, option):
        return 1

    @abstractmethod
    def pretty(self) -> str: ...


# ===================== SINGLE LEG =====================
class SingleLeg(Strategy):
    def __init__(self, opt: Option, action: str, direction: str):
        self.opt = opt
        self.action = action
        self.direction = direction

    def legs(self):
        return [self.opt]

    def _leg_sign(self, option):
        return 1 if self.action == "BUY" else -1

    def cost(self):
        return self.opt.price() if self.action == "BUY" else -self.opt.price()

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

    def _leg_sign(self, option):
        # short = -1, buy = +1
        if option in [self.sc, self.sp]:
            return -1
        return 1

    def cost(self):
        return -(self.sc.price() - self.bc.price() + self.sp.price() - self.bp.price())

    def credit(self):
        return -self.cost()

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
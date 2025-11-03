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

    def price(self): return self.mid if self.mid and self.mid > 0.0 else 0.0
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

from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum


class Direction(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

@dataclass
class StrategyFilter:
    """Filter which strategy types to generate"""
    single_calls: bool = False
    iron_condors: bool = False
    straddles: bool = False
    strangles: bool = False


@dataclass
class ConfigFilter:
    # ==================== OPTION-LEVEL FILTERS ====================
    # These filters apply to individual options before strategy construction
    min_volume: Optional[int] = None
    min_oi: Optional[int] = None
    min_price: Optional[float] = None

    expiry: Optional[str] = None
    days_to_expiry_range: Optional[Tuple[int, int]] = None  # (min_days, max_days) inclusive
    
    volume_ratio_range: Optional[Tuple[float, float]] = None  # Volume relative to open interest (removes fake volume spikes)
    max_bid_ask_spread: Optional[float] = None  # Require bid/ask spread to be tight (avoid illiquid options)

    # ==================== STRATEGY-LEVEL FILTERS ====================
    # These filters apply after strategies are constructed
    direction: Optional[Direction] = None  # Strategy direction: LONG or SHORT
    
    debit_range: Optional[Tuple[float, float]] = None
    credit_range: Optional[Tuple[float, float]] = None

    potential_gain_range: Optional[Tuple[float, float]] = None
    potential_loss_range: Optional[Tuple[float, float]] = None

    rr_range: Optional[Tuple[float, float]] = None
    net_delta_range: Optional[Tuple[float, float]] = None
    net_theta_range: Optional[Tuple[float, float]] = None
    net_vega_range: Optional[Tuple[float, float]] = None
    iv_range: Optional[Tuple[float, float]] = None
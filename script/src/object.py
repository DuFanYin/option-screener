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
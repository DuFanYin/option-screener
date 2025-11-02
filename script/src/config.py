from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class StrategyConfig:
    # ----- Option-level filters -----
    min_volume: Optional[int] = None
    min_oi: Optional[int] = None
    max_price: Optional[float] = None
    strikes_range: Optional[Tuple[float, float]] = None
    expiry: Optional[str] = None
    days_to_expiry_range: Optional[Tuple[int, int]] = None  # (min_days, max_days) inclusive

    # ----- Strategy-level -----
    max_debit: Optional[float] = None
    min_credit: Optional[float] = None
    max_loss: Optional[float] = None
    min_rr: Optional[float] = None

    # ----- Greek & IV limits -----
    max_net_delta: Optional[float] = None
    max_theta: Optional[float] = None
    max_vega: Optional[float] = None
    max_iv: Optional[float] = None
    min_iv: Optional[float] = None  # Require minimum IV (good for selling premium)
    min_delta: Optional[float] = None  # Filter weak/too-deep OTM legs
    max_gamma: Optional[float] = None  # For low-gamma trades
    
    # ----- Liquidity filters -----
    min_volume_ratio: Optional[float] = None  # Volume relative to open interest (removes fake volume spikes)
    min_bid_ask_spread: Optional[float] = None  # Require bid/ask spread to be tight (avoid illiquid options)

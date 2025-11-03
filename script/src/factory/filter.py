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

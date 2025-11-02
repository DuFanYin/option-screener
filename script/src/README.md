# Option Screener - Source Documentation

This directory contains the core option screening and strategy generation logic.

## StrategyConfig Parameters

The `StrategyConfig` class allows you to filter strategies at both the option level and strategy level. All parameters are optional (default to `None`).

### Option-Level Filters

These filters apply when selecting individual options before constructing strategies:

- **`min_volume`** (`Optional[int]`): Minimum volume required for an option
- **`min_oi`** (`Optional[int]`): Minimum open interest required for an option
- **`expiry`** (`Optional[str]`): Filter options by specific expiry date (e.g., "2025-01-17")
- **`days_to_expiry_range`** (`Optional[Tuple[int, int]]`): Days to expiry range as a tuple `(min_days, max_days)` inclusive. Use `(2, 10)` for 2-10 days, or `(2, 2)` for exactly 2 days
- **`volume_ratio_range`** (`Optional[Tuple[float, float]]`): Volume relative to open interest range as a tuple `(min_ratio, max_ratio)` inclusive (removes fake volume spikes)
- **`max_bid_ask_spread`** (`Optional[float]`): Maximum allowed bid/ask spread to require tight spreads and avoid illiquid/impossible-to-fill options

### Strategy-Level Filters

These filters apply after strategies are constructed:

- **`direction`** (`Optional[Literal["LONG", "SHORT"]]`): Strategy direction - "LONG" (buy/long positions) or "SHORT" (sell/short positions). Defaults to "LONG" for single calls if not specified
- **`min_debit`** (`Optional[float]`): Minimum debit/cost allowed for a strategy
- **`max_debit`** (`Optional[float]`): Maximum debit/cost allowed for a strategy
- **`min_credit`** (`Optional[float]`): Minimum credit required (for credit strategies like Iron Condors)
- **`max_credit`** (`Optional[float]`): Maximum credit allowed (for credit strategies like Iron Condors)
- **`potential_gain_range`** (`Optional[Tuple[float, float]]`): Maximum potential gain range as a tuple `(min_gain, max_gain)` inclusive
- **`potential_loss_range`** (`Optional[Tuple[float, float]]`): Maximum potential loss range as a tuple `(min_loss, max_loss)` inclusive
- **`rr_range`** (`Optional[Tuple[float, float]]`): Risk-reward ratio range as a tuple `(min_rr, max_rr)` inclusive (max_gain / max_loss)
- **`net_delta_range`** (`Optional[Tuple[float, float]]`): Net delta range as a tuple `(min_delta, max_delta)` inclusive
- **`net_theta_range`** (`Optional[Tuple[float, float]]`): Net theta range as a tuple `(min_theta, max_theta)` inclusive
- **`net_vega_range`** (`Optional[Tuple[float, float]]`): Net vega range as a tuple `(min_vega, max_vega)` inclusive
- **`iv_range`** (`Optional[Tuple[float, float]]`): Average implied volatility range as a tuple `(min_iv, max_iv)` inclusive across all legs

### Example Usage

```python
from script.src.factory import StrategyFactory
from script.src.config import StrategyConfig
from script.src.loader import load_option_snapshot

options, spot = load_option_snapshot("data/pltr.json")
factory = StrategyFactory(options, spot)

cfg = StrategyConfig(
    # Option-level filters
    min_volume=10,
    min_oi=50,
    expiry="2025-01-17",
    days_to_expiry_range=(2, 10),  # 2 to 10 days inclusive
    volume_ratio_range=(0.1, 1.0),  # Volume to OI ratio range
    max_bid_ask_spread=0.10,  # Maximum allowed spread (tight spreads)
    
    # Strategy-level filters
    direction="LONG",  # or "SHORT" for short positions
    min_debit=1.0,
    max_debit=3.0,
    min_credit=1.0,
    max_credit=5.0,
    potential_gain_range=(50, 500),
    potential_loss_range=(0, 100),
    rr_range=(1.5, 10.0),
    net_delta_range=(-50, 50),
    net_theta_range=(-100, 100),
    net_vega_range=(-200, 200),
    iv_range=(0.1, 0.5),
)

strategies = factory.vertical_debit_calls(cfg)
```

## Rank Method Parameters

The `rank()` method on `StrategyList` allows you to sort strategies by different criteria.

### Supported Keys

- **`"rr"`**: Sort by risk-reward ratio (default)
- **`"gain"`**: Sort by maximum potential gain
- **`"loss"`**: Sort by maximum potential loss (ascending)
- **`"cost"`**: Sort by strategy cost/debit
- **`"credit"`**: Sort by credit received (only for credit strategies like Iron Condors)

### Parameters

- **`key`** (`str`): The sorting criterion (default: `"rr"`)
- **`reverse`** (`bool`): Whether to sort in descending order (default: `True`)

### Example Usage

```python
# Rank by risk-reward ratio (default)
ranked = strategies.rank()

# Rank by cost (lowest first)
ranked = strategies.rank("cost", reverse=False)

# Rank by maximum gain
ranked = strategies.rank("gain")

# Get top 5 strategies ranked by cost
top_5 = strategies.rank("cost").top(5)

# Convert to DataFrame
df = strategies.rank("rr").top(10).to_df()
```

## Available Strategy Types

1. **Single Calls** (`single_calls`): Long OTM call options
2. **Vertical Debit Calls** (`vertical_debit_calls`): Debit call spreads (buy lower, sell higher)
3. **Iron Condors** (`iron_condors`): Short iron condor strategies (credit spreads)

Each method returns a `StrategyList` that supports:
- `.rank(key, reverse)` - Sort strategies
- `.top(n)` - Get top N strategies
- `.to_df()` - Convert to pandas DataFrame

## StrategyConfig Field Compatibility Table

The following table shows which `StrategyConfig` fields apply to which strategies:

| Config Field | Single Calls | Vertical Debit Calls | Iron Condors |
|------------|--------------|---------------------|--------------|
| **Option-Level Filters** |
| `min_volume` | ✅ | ✅ | ✅ |
| `min_oi` | ✅ | ✅ | ✅ |
| `expiry` | ✅ | ✅ | ✅ |
| `days_to_expiry_range` | ✅ | ✅ | ✅ |
| `volume_ratio_range` | ✅ | ✅ | ✅ |
| `max_bid_ask_spread` | ✅ | ✅ | ✅ |
| **Strategy-Level Filters** |
| `direction` | ✅ | ✅ | ✅ |
| `min_debit` | ✅ | ✅ | ✅ |
| `max_debit` | ✅ | ✅ | ✅ |
| `min_credit` | | | ✅ |
| `max_credit` | | | ✅ |
| `potential_gain_range` | ✅ | ✅ | ✅ |
| `potential_loss_range` | ✅ | ✅ | ✅ |
| `rr_range` | ✅ | ✅ | ✅ |
| `net_delta_range` | ✅ | ✅ | ✅ |
| `net_theta_range` | ✅ | ✅ | ✅ |
| `net_vega_range` | ✅ | ✅ | ✅ |
| `iv_range` | ✅ | ✅ | ✅ |
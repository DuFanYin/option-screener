# Option Screener - Source Documentation

This directory contains the core option screening and strategy generation logic.

## StrategyConfig Parameters

The `StrategyConfig` class allows you to filter strategies at both the option level and strategy level. All parameters are optional (default to `None`).

### Option-Level Filters

These filters apply when selecting individual options before constructing strategies:

- **`min_volume`** (`Optional[int]`): Minimum volume required for an option
- **`min_oi`** (`Optional[int]`): Minimum open interest required for an option
- **`max_price`** (`Optional[float]`): Maximum option price (mid price)
- **`strikes_range`** (`Optional[Tuple[float, float]]`): Strike price range as a tuple `(low, high)`
- **`expiry`** (`Optional[str]`): Filter options by specific expiry date (e.g., "2025-01-17")
- **`days_to_expiry_range`** (`Optional[Tuple[int, int]]`): Days to expiry range as a tuple `(min_days, max_days)` inclusive. Use `(2, 10)` for 2-10 days, or `(2, 2)` for exactly 2 days

### Strategy-Level Filters

These filters apply after strategies are constructed:

- **`max_debit`** (`Optional[float]`): Maximum debit/cost allowed for a strategy
- **`min_credit`** (`Optional[float]`): Minimum credit required (for credit strategies like Iron Condors)
- **`max_loss`** (`Optional[float]`): Maximum potential loss allowed
- **`min_rr`** (`Optional[float]`): Minimum risk-reward ratio (max_gain / max_loss)

### Greek & IV Limits

Risk management filters based on net Greeks and implied volatility:

- **`max_net_delta`** (`Optional[float]`): Maximum absolute net delta for the strategy
- **`max_theta`** (`Optional[float]`): Maximum absolute net theta for the strategy
- **`max_vega`** (`Optional[float]`): Maximum absolute net vega for the strategy
- **`max_iv`** (`Optional[float]`): Maximum average implied volatility across all legs
- **`min_iv`** (`Optional[float]`): Require minimum IV (good for selling premium)
- **`min_delta`** (`Optional[float]`): Filter weak/too-deep OTM legs (minimum absolute delta)
- **`max_gamma`** (`Optional[float]`): Maximum gamma for low-gamma trades (maximum absolute gamma)

### Liquidity Filters

Filters to ensure option liquidity and quality:

- **`min_volume_ratio`** (`Optional[float]`): Volume relative to open interest (removes fake volume spikes)
- **`min_bid_ask_spread`** (`Optional[float]`): Maximum allowed bid/ask spread to require tight spreads and avoid illiquid/impossible-to-fill options

### Example Usage

```python
from script.src.factory import StrategyFactory, StrategyConfig
from script.src.loader import load_option_snapshot

options, spot = load_option_snapshot("data/pltr.json")
factory = StrategyFactory(options, spot)

cfg = StrategyConfig(
    min_volume=10,
    min_oi=50,
    max_price=5,
    strikes_range=(20, 30),
    expiry="2025-01-17",
    days_to_expiry_range=(2, 10),  # 2 to 10 days inclusive
    min_iv=0.3,  # Require minimum IV for selling premium
    min_delta=0.05,  # Filter weak OTM legs
    max_gamma=0.1,  # Low-gamma trades
    min_volume_ratio=0.1,  # Volume to OI ratio
    min_bid_ask_spread=0.10,  # Maximum allowed spread (tight spreads)
    max_debit=3,
    min_credit=1,
    max_loss=5,
    min_rr=1.5,
    max_net_delta=100,
    max_theta=50,
    max_vega=200,
    max_iv=0.5,
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
| `max_price` | ✅ | ✅ | ✅ |
| `strikes_range` | ✅ | ✅ | ✅ |
| `expiry` | ✅ | ✅ | ✅ |
| `days_to_expiry_range` | ✅ | ✅ | ✅ |
| `min_iv` | ✅ | ✅ | ✅ |
| `min_delta` | ✅ | ✅ | ✅ |
| `max_gamma` | ✅ | ✅ | ✅ |
| **Strategy-Level Filters** |
| `max_debit` | ✅ | ✅ | ✅ |
| `min_credit` | | | ✅ |
| `max_loss` | ✅ | ✅ | ✅ |
| `min_rr` | ✅ | ✅ | ✅ |
| **Greek & IV Limits** |
| `max_net_delta` | ✅ | ✅ | ✅ |
| `max_theta` | ✅ | ✅ | ✅ |
| `max_vega` | ✅ | ✅ | ✅ |
| `max_iv` | ✅ | ✅ | ✅ |
| **Liquidity Filters** |
| `min_volume_ratio` | ✅ | ✅ | ✅ |
| `min_bid_ask_spread` | ✅ | ✅ | ✅ |





{
  "symbols": [
    "PLTR"
  ],
  "timestamp": 1762049680.174532,
  "underlying": {
    "last": 200.47,
    "bid": 201.5,
    "ask": 201.62,
    "volume": 52697644,
    "updated_at": 1761940800462
  },
  "chains": {
    "PLTR": {
      "2025-11-07": [
        {
          "symbol": "PLTR251107P00095000",
          "description": "PLTR Nov 7 2025 $95.00 Put",
          "exch": "Z",
          "type": "option",
          "last": 0.02,
          "change": -0.02,
          "volume": 5384,
          "open": 0.04,
          "high": 0.06,
          "low": 0.01,
          "close": 0.02,
          "bid": 0.01,
          "ask": 0.03,
          "underlying": "PLTR",
          "strike": 95.0,
          "greeks": {
            "delta": -6.01864144947e-05,
            "gamma": 7.40630883938048e-10,
            "theta": -1.6306298433649376e-08,
            "vega": 2.000688743685533e-05,
            "rho": 0.018323446898149878,
            "phi": -0.03885635243292845,
            "bid_iv": 1.774586,
            "mid_iv": 1.864725,
            "ask_iv": 1.954864,
            "smv_vol": 1.119,
            "updated_at": "2025-10-31 20:00:02"
          },
          "change_percentage": -50.0,
          "average_volume": 0,
          "last_volume": 8,
          "trade_date": 1761938340985,
          "prevclose": 0.04,
          "week_52_high": 0.0,
          "week_52_low": 0.0,
          "bidsize": 108,
          "bidexch": "N",
          "bid_date": 1761939057000,
          "asksize": 10,
          "askexch": "I",
          "ask_date": 1761940498000,
          "open_interest": 3452,
          "contract_size": 100,
          "expiration_date": "2025-11-07",
          "expiration_type": "weeklys",
          "option_type": "put",
          "root_symbol": "PLTR"
        },
        {
          "symbol": "PLTR251107C00095000",
          "description": "PLTR Nov 7 2025 $95.00 Call",
          "exch": "Z",
          "type": "option",
          "last": 106.13,
          "change": 4.29,
          "volume": 37,
          "open": 106.53,
          "high": 108.44,
          "low": 103.9,
          "close": 106.13,
          "bid": 104.95,
          "ask": 106.55,
          "underlying": "PLTR",
          "strike": 95.0,
          "greeks": {
            "delta": 0.9999398135855053,
            "gamma": 7.40630883938048e-10,
            "theta": -1.6306298433649376e-08,
            "vega": 2.000688743685533e-05,
            "rho": 0.018323446898149878,
            "phi": -0.03885635243292845,
            "bid_iv": 0.0,
            "mid_iv": 2.467764,


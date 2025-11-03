# Option Screener - Source Documentation

This directory contains the core option screening and strategy generation logic.

## Project Overview

The option screener works in a five-stage filtering and generation process:

1. **Strategy Selection**: Choose which strategy types to generate using `StrategyFilter` (single calls, iron condors, straddles, strangles). This determines which generators will be used.

2. **Option-Level Filtering**: For each selected strategy type, individual options are filtered using option-level filters (volume, open interest, price, expiry, days to expiry, volume ratio, bid/ask spread). This narrows down the universe of options before strategy construction.

3. **Brute Force Combination Generation**: After filtering individual options, the system generates every possible combination of options that could form the selected strategy types (e.g., for Iron Condors, all combinations of short calls, long calls, short puts, and long puts).

4. **Strategy-Level Filtering**: Strategy-level filters are applied to the generated combinations (debit/credit ranges, potential gain/loss, risk-reward ratio, Greeks, IV). Only strategies that pass all filters proceed to ranking.

5. **Ranking**: The final filtered strategies are ranked by criteria such as risk-reward ratio, cost, potential gain, or credit received, allowing you to select the top N strategies for analysis.

This workflow ensures efficient processing by selecting strategy types first, then filtering at the option level (reducing the search space) before generating combinations, applying sophisticated strategy-level criteria, and finally ranking results to identify the best opportunities.

## ConfigFilter Parameters

The `ConfigFilter` class allows you to filter strategies at both the option level and strategy level. All parameters are optional (default to `None`).

### Option-Level Filters

These filters apply when selecting individual options before constructing strategies:

- **`min_volume`** (`Optional[int]`): Minimum volume required for an option
- **`min_oi`** (`Optional[int]`): Minimum open interest required for an option
- **`min_price`** (`Optional[float]`): Minimum option price required
- **`expiry`** (`Optional[str]`): Filter options by specific expiry date (e.g., "2025-01-17")
- **`days_to_expiry_range`** (`Optional[Tuple[int, int]]`): Days to expiry range as a tuple `(min_days, max_days)` inclusive. Use `(2, 10)` for 2-10 days, or `(2, 2)` for exactly 2 days
- **`volume_ratio_range`** (`Optional[Tuple[float, float]]`): Volume relative to open interest range as a tuple `(min_ratio, max_ratio)` inclusive (removes fake volume spikes)
- **`max_bid_ask_spread`** (`Optional[float]`): Maximum allowed bid/ask spread to require tight spreads and avoid illiquid/impossible-to-fill options

### Strategy-Level Filters

These filters apply after strategies are constructed:

- **`direction`** (`Optional[Direction]`): Strategy direction - `Direction.LONG` (buy/long positions) or `Direction.SHORT` (sell/short positions)
- **`debit_range`** (`Optional[Tuple[float, float]]`): Debit/cost range as a tuple `(min_debit, max_debit)` inclusive
- **`credit_range`** (`Optional[Tuple[float, float]]`): Credit received range as a tuple `(min_credit, max_credit)` inclusive (for credit strategies like Iron Condors)
- **`potential_gain_range`** (`Optional[Tuple[float, float]]`): Maximum potential gain range as a tuple `(min_gain, max_gain)` inclusive
- **`potential_loss_range`** (`Optional[Tuple[float, float]]`): Maximum potential loss range as a tuple `(min_loss, max_loss)` inclusive
- **`rr_range`** (`Optional[Tuple[float, float]]`): Risk-reward ratio range as a tuple `(min_rr, max_rr)` inclusive (max_gain / max_loss)
- **`net_delta_range`** (`Optional[Tuple[float, float]]`): Net delta range as a tuple `(min_delta, max_delta)` inclusive
- **`net_theta_range`** (`Optional[Tuple[float, float]]`): Net theta range as a tuple `(min_theta, max_theta)` inclusive
- **`net_vega_range`** (`Optional[Tuple[float, float]]`): Net vega range as a tuple `(min_vega, max_vega)` inclusive
- **`iv_range`** (`Optional[Tuple[float, float]]`): Average implied volatility range as a tuple `(min_iv, max_iv)` inclusive across all legs

## StrategyFilter

The `StrategyFilter` class allows you to select which strategy types to generate:

- **`single_calls`** (`bool`): Generate single call/put strategies
- **`iron_condors`** (`bool`): Generate iron condor strategies
- **`straddles`** (`bool`): Generate straddle strategies
- **`strangles`** (`bool`): Generate strangle strategies

## Usage Examples

The factory method takes both filter and config parameters:

```python
# Generate strategies with filter and config
strategies = factory.strategy(s_filter, c_filter)

# Rank and get top N
top_strategies = factory.strategy(s_filter, c_filter).rank("rr").top(10)

# Convert to DataFrame
df = factory.strategy(s_filter, c_filter).rank("cost").top(20).to_df()
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

1. **Single Calls** (`single_calls`): Long/short OTM call or put options
2. **Iron Condors** (`iron_condors`): Iron condor strategies (credit spreads)
3. **Straddles** (`straddles`): Straddle strategies (same strike call + put)
4. **Strangles** (`strangles`): Strangle strategies (OTM call + OTM put)

Each method returns a `StrategyList` that supports:
- `.rank(key, reverse)` - Sort strategies
- `.top(n)` - Get top N strategies
- `.to_df()` - Convert to pandas DataFrame

## ConfigFilter Field Compatibility Table

The following table shows which `ConfigFilter` fields apply to which strategies:

| Config Field | Single Calls | Iron Condors | Straddles | Strangles |
|------------|--------------|--------------|-----------|-----------|
| **Option-Level Filters** |
| `min_volume` | ✅ | ✅ | ✅ | ✅ |
| `min_oi` | ✅ | ✅ | ✅ | ✅ |
| `min_price` | ✅ | ✅ | ✅ | ✅ |
| `expiry` | ✅ | ✅ | ✅ | ✅ |
| `days_to_expiry_range` | ✅ | ✅ | ✅ | ✅ |
| `volume_ratio_range` | ✅ | ✅ | ✅ | ✅ |
| `max_bid_ask_spread` | ✅ | ✅ | ✅ | ✅ |
| **Strategy-Level Filters** |
| `direction` | ✅ | ✅ | ✅ | ✅ |
| `debit_range` | ✅ | ✅ | ✅ | ✅ |
| `credit_range` | ✅ | ✅ | ✅ | ✅ |
| `potential_gain_range` | ✅ | ✅ | ✅ | ✅ |
| `potential_loss_range` | ✅ | ✅ | ✅ | ✅ |
| `rr_range` | ✅ | ✅ | ✅ | ✅ |
| `net_delta_range` | ✅ | ✅ | ✅ | ✅ |
| `net_theta_range` | ✅ | ✅ | ✅ | ✅ |
| `net_vega_range` | ✅ | ✅ | ✅ | ✅ |
| `iv_range` | ✅ | ✅ | ✅ | ✅ |

import json
import sys
from pathlib import Path
from python.src.loader import load_option_snapshot
from python.src.factory.factory import StrategyFactory
from python.src.object import ConfigFilter, Direction, StrategyFilter


def string_to_direction(s: str) -> Direction:
    """Convert string to Direction enum"""
    if s.upper() == "LONG":
        return Direction.LONG
    return Direction.SHORT


def load_strategy_filter_from_json(path: str) -> StrategyFilter:
    """Load StrategyFilter from JSON config file"""
    with open(path, 'r') as f:
        config_json = json.load(f)
    
    # Get strategy_filter section
    sf = config_json["strategy_filter"]
    
    return StrategyFilter(
        single_calls=sf["single_calls"],
        iron_condors=sf["iron_condors"],
        straddles=sf["straddles"],
        strangles=sf["strangles"],
    )


def load_config_filter_from_json(path: str) -> ConfigFilter:
    """Load ConfigFilter from JSON config file"""
    with open(path, 'r') as f:
        config_json = json.load(f)
    
    # Get config_filter section
    config = config_json["config_filter"]
    
    # Helper to convert null to None
    def to_tuple_or_none(val):
        return tuple(val) if val is not None else None
    
    return ConfigFilter(
        # Option-level filters
        min_volume=config["min_volume"],
        min_oi=config["min_oi"],
        min_price=config["min_price"],
        expiry=config["expiry"],
        days_to_expiry_range=to_tuple_or_none(config["days_to_expiry_range"]),
        volume_ratio_range=to_tuple_or_none(config["volume_ratio_range"]),
        max_bid_ask_spread=config["max_bid_ask_spread"],
        
        # Strategy-level filters
        direction=string_to_direction(config["direction"]) if config["direction"] else None,
        debit_range=to_tuple_or_none(config["debit_range"]),
        credit_range=to_tuple_or_none(config["credit_range"]),
        potential_gain_range=to_tuple_or_none(config["potential_gain_range"]),
        potential_loss_range=to_tuple_or_none(config["potential_loss_range"]),
        rr_range=to_tuple_or_none(config["rr_range"]),
        net_delta_range=to_tuple_or_none(config["net_delta_range"]),
        net_theta_range=to_tuple_or_none(config["net_theta_range"]),
        net_vega_range=to_tuple_or_none(config["net_vega_range"]),
        iv_range=to_tuple_or_none(config["iv_range"]),
    )


def main():
    # Get config file path (default: config.json)
    config_path = "config.json"
    
    # Check if config file exists
    if not Path(config_path).exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    # Hardcode data file path
    data_path = "data/pltr.json"
    
    # Check if data file exists
    if not Path(data_path).exists():
        print(f"Error: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(1)
    
    # Load config JSON for ranking settings
    with open(config_path, 'r') as f:
        config_json = json.load(f)
    
    # Load filters from config
    s_filter = load_strategy_filter_from_json(config_path)
    c_filter = load_config_filter_from_json(config_path)
    
    # Load options and spot
    options, spot = load_option_snapshot(data_path)
    factory = StrategyFactory(options, spot)
    
    # Get ranking parameters from config
    ranking = config_json["ranking"]
    rank_key = ranking["key"]
    top_n = ranking["top_n"]
    
    # Generate, rank, and get top strategies
    results = factory.strategy(s_filter, c_filter).rank(rank_key).top(top_n)
    
    print(f"Found {len(results)} strategies")
    print(f"Ranked by: {rank_key}")
    print("----------------------------------------")
    print(results.to_df())


if __name__ == "__main__":
    main()

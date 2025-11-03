import json
from pathlib import Path
from typing import Tuple, List
from datetime import datetime, date
from .object import Option  # <-- your Option class

def load_option_snapshot(path: str) -> Tuple[float, List[Option]]:
    """
    Load JSON snapshot (from Tradier) and return:
        spot_price: float
        options: List[Option]
    """

    # Read JSON
    data = json.loads(Path(path).read_text())

    symbol = data["symbols"][0]
    chains = data["chains"][symbol]        # { "2025-11-07": [ ... ], ... }
    underlying = data.get("underlying", {})

    # ===== Get spot price =====
    # Prefer bid/ask mid if available, else last
    bid = underlying.get("bid")
    ask = underlying.get("ask")
    last = underlying.get("last")

    if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
        spot = (bid + ask) / 2
    elif isinstance(last, (int, float)):
        spot = last
    else:
        spot = None

    # ===== Helper extractors =====
    def mid_price(opt):
        bid, ask, last = opt.get("bid"), opt.get("ask"), opt.get("last")
        if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
            return (bid + ask) / 2
        if isinstance(last, (int, float)):
            return float(last)
        return None

    def extract_iv(greeks):
        if not greeks:
            return None
        for key in ("mid_iv", "bid_iv", "ask_iv", "smv_vol", "implied_volatility", "volatility"):
            value = greeks.get(key)
            if isinstance(value, (int, float)) and value > 0:
                return value
        return None

    # ===== Convert all chain rows into Option objects =====
    options: List[Option] = []
    today = date.today()
    # Use datetime for consistency with C++ (which uses system_clock with time)
    now_datetime = datetime.now()
    now_timestamp = now_datetime.timestamp()

    for expiry_key, rows in chains.items():
        for opt_data in rows:
            side = "CALL" if opt_data["option_type"].lower() == "call" else "PUT"
            greeks = opt_data.get("greeks", {})
            
            # Always use expiration_date from option data
            expiry_str = opt_data["expiration_date"]
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            # Calculate days using floor like C++ for consistency
            expiry_datetime = datetime.combine(expiry_date, datetime.min.time())
            expiry_timestamp = expiry_datetime.timestamp()
            diff_seconds = expiry_timestamp - now_timestamp
            days_to_expiry = int(diff_seconds // 86400)

            # Extract bid and ask
            bid_val = opt_data.get("bid")
            ask_val = opt_data.get("ask")
            bid = float(bid_val) if isinstance(bid_val, (int, float)) else None
            ask = float(ask_val) if isinstance(ask_val, (int, float)) else None

            option = Option(
                symbol=symbol,
                expiry=expiry_str,
                strike=float(opt_data["strike"]),
                side=side,

                mid=mid_price(opt_data) or 0.0,
                iv=extract_iv(greeks) or 0.0,
                volume=opt_data.get("volume") or 0,
                oi=opt_data.get("open_interest") or 0,
                
                bid=bid,
                ask=ask,

                delta=greeks.get("delta") or 0.0,
                gamma=greeks.get("gamma") or 0.0,
                theta=greeks.get("theta") or 0.0,
                vega=greeks.get("vega") or 0.0,
                rho=greeks.get("rho") or 0.0,
                days_to_expiry=days_to_expiry,
            )

            options.append(option)

    return options, spot
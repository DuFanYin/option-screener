from script.src.loader import load_option_snapshot
from script.src.factory import StrategyFactory
from script.src.config import StrategyConfig, Direction


path = "data/pltr.json"
options, spot = load_option_snapshot(path)
factory = StrategyFactory(options, spot)



MIN_VOLUME = None
MIN_OI = 5
EXPIRY = None
DAYS_TO_EXPIRY_RANGE = (30,150)
VOLUME_RATIO_RANGE = None
MAX_BID_ASK_SPREAD = 0.30

DIRECTION = Direction.LONG
DEBIT_RANGE = (5,10)
CREDIT_RANGE = None 
POTENTIAL_GAIN_RANGE = None
POTENTIAL_LOSS_RANGE = None

RR_RANGE = None
NET_DELTA_RANGE = None
NET_THETA_RANGE = None
NET_VEGA_RANGE = None
IV_RANGE = None


cfg = StrategyConfig(
    # Option-level filters
    min_volume=MIN_VOLUME,
    min_oi=MIN_OI,
    expiry=EXPIRY,
    days_to_expiry_range=DAYS_TO_EXPIRY_RANGE,
    volume_ratio_range=VOLUME_RATIO_RANGE,
    max_bid_ask_spread=MAX_BID_ASK_SPREAD,
    
    # Strategy-level filters
    direction=DIRECTION,
    debit_range=DEBIT_RANGE,
    credit_range=CREDIT_RANGE,
    potential_gain_range=POTENTIAL_GAIN_RANGE,
    potential_loss_range=POTENTIAL_LOSS_RANGE,

    rr_range=RR_RANGE,
    net_delta_range=NET_DELTA_RANGE,
    net_theta_range=NET_THETA_RANGE,
    net_vega_range=NET_VEGA_RANGE,
    iv_range=IV_RANGE,
)


results = factory.single_calls(cfg).rank("cost")
print(len(results))
print(results.to_df())
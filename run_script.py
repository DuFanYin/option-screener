from script.src.loader import load_option_snapshot
from script.src.factory.factory import StrategyFactory
from script.src.factory.filter import ConfigFilter, Direction, StrategyFilter


path = "data/pltr.json"
options, spot = load_option_snapshot(path)
factory = StrategyFactory(options, spot)


filter = StrategyFilter(
    single_calls=True,
    iron_condors=False,
    straddles=True,
    strangles=False,
)


cfg = ConfigFilter(
    # Option-level filters
    min_volume=None,
    min_oi=5,
    min_price=0.05,

    expiry=None,
    days_to_expiry_range=(0, 30),
    volume_ratio_range=None,
    max_bid_ask_spread=None,
    
    # Strategy-level filters
    direction=Direction.SHORT,
    debit_range=None,
    credit_range=(0, 2500),
    potential_gain_range=None,
    potential_loss_range=None,

    rr_range=None,
    net_delta_range=None,
    net_theta_range=None,
    net_vega_range=None,
    iv_range=None,
)


results_2 = factory.strategy(filter).config(cfg).rank("cost").top(10)


print(len(results_2))
print(results_2.to_df())
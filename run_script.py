from script.src.loader import load_option_snapshot
from script.src.factory import StrategyFactory
from script.src.config import StrategyConfig


path = "data/pltr.json"
options, spot = load_option_snapshot(path)
factory = StrategyFactory(options, spot)


cfg = StrategyConfig(
    min_volume=10,
    min_oi=None,
    max_price=5,
    strikes_range=None,
    expiry=None,

    max_debit=None,
    min_credit=None,
    max_loss=None,
    min_rr=1.5,

    max_net_delta=None,
    max_theta=None,
    max_vega=None,
    max_iv=None,

)


verticals = factory.vertical_debit_calls(cfg).rank("cost").top(5)
print(verticals.to_df())
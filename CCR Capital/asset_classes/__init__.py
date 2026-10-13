from .commodity import calculate as calculate_commodity
from .common import AssetClassCalculation, AssetClassConfiguration
from .credit import calculate as calculate_credit
from .equity import calculate as calculate_equity
from .foreign_exchange import calculate as calculate_foreign_exchange
from .interest_rate import calculate as calculate_interest_rate


CALCULATORS = {
    "interest_rate": calculate_interest_rate,
    "foreign_exchange": calculate_foreign_exchange,
    "credit": calculate_credit,
    "equity": calculate_equity,
    "commodity": calculate_commodity,
}


def calculate_asset_class_add_on(
    config: AssetClassConfiguration,
) -> AssetClassCalculation:
    """Calculate the trade-level add-on for one supported asset class."""
    try:
        calculator = CALCULATORS[config.asset_class]
    except KeyError as error:
        supported = ", ".join(CALCULATORS)
        raise ValueError(
            f"Unsupported asset class {config.asset_class!r}; "
            f"supported classes are: {supported}."
        ) from error
    return calculator(config)


__all__ = ["calculate_asset_class_add_on"]

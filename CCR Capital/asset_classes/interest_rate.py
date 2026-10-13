from math import isfinite

from .common import (
    AssetClassCalculation,
    AssetClassConfiguration,
    build_calculation,
    calculate_supervisory_delta,
    calculate_supervisory_duration,
    valuation_date,
)


SUPERVISORY_FACTOR = 0.005
OPTION_SUPERVISORY_VOLATILITY = 0.50


def calculate(config: AssetClassConfiguration) -> AssetClassCalculation:
    if (
        not isfinite(config.notional_to_domestic_rate)
        or config.notional_to_domestic_rate <= 0
    ):
        raise ValueError(
            "Notional-to-domestic rate must be positive and finite."
        )
    duration = calculate_supervisory_duration(
        config.start_date, config.end_date, valuation_date(config)
    )
    delta, option_details = calculate_supervisory_delta(
        config,
        OPTION_SUPERVISORY_VOLATILITY,
        supports_negative_prices=True,
    )
    details = (
        ("Interest rate currency", config.currency.upper()),
        ("Notional-to-domestic rate", config.notional_to_domestic_rate),
    ) + option_details
    adjusted_notional = (
        config.notional * config.notional_to_domestic_rate * duration
    )
    return build_calculation(
        config,
        adjusted_notional,
        SUPERVISORY_FACTOR,
        delta,
        details,
        supervisory_duration=duration,
    )

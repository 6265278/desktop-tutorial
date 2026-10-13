from math import isfinite

from .common import (
    AssetClassCalculation,
    AssetClassConfiguration,
    build_calculation,
    calculate_supervisory_delta,
)


SUPERVISORY_FACTORS = {"single_name": 0.32, "index": 0.20}
OPTION_SUPERVISORY_VOLATILITIES = {
    "single_name": 1.20,
    "index": 0.75,
}


def calculate(config: AssetClassConfiguration) -> AssetClassCalculation:
    if config.equity_reference_type not in SUPERVISORY_FACTORS:
        raise ValueError(
            "equity_reference_type must be 'single_name' or 'index'."
        )
    if not isfinite(config.underlying_price) or config.underlying_price < 0:
        raise ValueError("Underlying price must be finite and non-negative.")
    if not isfinite(config.underlying_units) or config.underlying_units < 0:
        raise ValueError("Underlying units must be finite and non-negative.")
    if (
        not isfinite(config.underlying_to_domestic_rate)
        or config.underlying_to_domestic_rate <= 0
    ):
        raise ValueError(
            "Underlying-to-domestic rate must be positive and finite."
        )

    delta, option_details = calculate_supervisory_delta(
        config,
        OPTION_SUPERVISORY_VOLATILITIES[config.equity_reference_type],
    )
    details = (
        ("Equity reference type", config.equity_reference_type),
        ("Underlying price", config.underlying_price),
        ("Underlying units", config.underlying_units),
        ("Underlying-to-domestic rate", config.underlying_to_domestic_rate),
    ) + option_details
    return build_calculation(
        config,
        (
            config.underlying_price
            * config.underlying_units
            * config.underlying_to_domestic_rate
        ),
        SUPERVISORY_FACTORS[config.equity_reference_type],
        delta,
        details,
    )

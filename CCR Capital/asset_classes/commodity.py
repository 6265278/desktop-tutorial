from math import isfinite

from .common import (
    AssetClassCalculation,
    AssetClassConfiguration,
    build_calculation,
    calculate_supervisory_delta,
)


HEDGING_SETS = {"energy", "metals", "agricultural", "other"}
SUPERVISORY_FACTORS = {"electricity": 0.40, "other": 0.18}
OPTION_SUPERVISORY_VOLATILITIES = {
    "electricity": 1.50,
    "other": 0.70,
}


def calculate(config: AssetClassConfiguration) -> AssetClassCalculation:
    if config.commodity_hedging_set not in HEDGING_SETS:
        raise ValueError(
            "commodity_hedging_set must be energy, metals, agricultural, "
            "or other."
        )
    if config.commodity_type not in SUPERVISORY_FACTORS:
        raise ValueError("commodity_type must be 'electricity' or 'other'.")
    if (
        config.commodity_type == "electricity"
        and config.commodity_hedging_set != "energy"
    ):
        raise ValueError("Electricity must use the energy hedging set.")
    if not isfinite(config.underlying_price):
        raise ValueError("Underlying price must be finite.")
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
        OPTION_SUPERVISORY_VOLATILITIES[config.commodity_type],
        supports_negative_prices=True,
    )
    details = (
        ("Commodity hedging set", config.commodity_hedging_set),
        ("Commodity type", config.commodity_type),
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
        SUPERVISORY_FACTORS[config.commodity_type],
        delta,
        details,
    )

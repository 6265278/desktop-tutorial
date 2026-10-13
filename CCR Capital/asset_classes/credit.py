from math import isfinite

from .common import (
    AssetClassCalculation,
    AssetClassConfiguration,
    build_calculation,
    calculate_supervisory_delta,
    calculate_supervisory_duration,
    valuation_date,
)


SINGLE_NAME_FACTORS = {
    "aaa": 0.0038,
    "aa": 0.0038,
    "a": 0.0042,
    "bbb": 0.0054,
    "bb": 0.0106,
    "b": 0.0160,
    "ccc": 0.0600,
    "unrated": 0.0106,
}
INDEX_FACTORS = {"ig": 0.0038, "sg": 0.0106}
SINGLE_NAME_OPTION_VOLATILITY = 1.00
INDEX_OPTION_VOLATILITY = 0.80


def calculate(config: AssetClassConfiguration) -> AssetClassCalculation:
    if (
        not isfinite(config.notional_to_domestic_rate)
        or config.notional_to_domestic_rate <= 0
    ):
        raise ValueError(
            "Notional-to-domestic rate must be positive and finite."
        )
    if config.credit_reference_type == "single_name":
        if config.credit_rating_bucket not in SINGLE_NAME_FACTORS:
            raise ValueError(
                "Invalid credit rating bucket; choose aaa, aa, a, bbb, "
                "bb, b, ccc, or unrated."
            )
        factor = SINGLE_NAME_FACTORS[config.credit_rating_bucket]
        volatility = SINGLE_NAME_OPTION_VOLATILITY
        category = f"single name, {config.credit_rating_bucket.upper()}"
    elif config.credit_reference_type == "index":
        if config.credit_index_grade not in INDEX_FACTORS:
            raise ValueError("Credit index grade must be 'ig' or 'sg'.")
        factor = INDEX_FACTORS[config.credit_index_grade]
        volatility = INDEX_OPTION_VOLATILITY
        category = f"index, {config.credit_index_grade.upper()}"
    else:
        raise ValueError(
            "credit_reference_type must be 'single_name' or 'index'."
        )

    duration = calculate_supervisory_duration(
        config.start_date, config.end_date, valuation_date(config)
    )
    delta, option_details = calculate_supervisory_delta(
        config, volatility
    )
    details = (
        ("Credit reference type", category),
        ("Notional-to-domestic rate", config.notional_to_domestic_rate),
    ) + option_details
    return build_calculation(
        config,
        config.notional * config.notional_to_domestic_rate * duration,
        factor,
        delta,
        details,
        supervisory_duration=duration,
    )

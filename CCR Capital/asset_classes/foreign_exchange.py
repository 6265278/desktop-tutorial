from math import isfinite

from .common import (
    AssetClassCalculation,
    AssetClassConfiguration,
    build_calculation,
    calculate_supervisory_delta,
)


SUPERVISORY_FACTOR = 0.04
OPTION_SUPERVISORY_VOLATILITY = 0.15


def calculate(config: AssetClassConfiguration) -> AssetClassCalculation:
    domestic_currency = config.domestic_currency.strip().upper()
    base_currency = config.fx_base_currency.strip().upper()
    quote_currency = config.fx_quote_currency.strip().upper()
    if not domestic_currency or not base_currency or not quote_currency:
        raise ValueError("FX and domestic currencies must not be empty.")
    if base_currency == quote_currency:
        raise ValueError("FX base and quote currencies must be different.")
    for label, amount in (
        ("FX base notional", config.fx_base_notional),
        ("FX quote notional", config.fx_quote_notional),
    ):
        if not isfinite(amount) or amount < 0:
            raise ValueError(f"{label} must be finite and non-negative.")
    if base_currency != domestic_currency and (
        not isfinite(config.fx_base_to_domestic_rate)
        or config.fx_base_to_domestic_rate <= 0
    ):
        raise ValueError(
            "FX base-to-domestic rate must be positive and finite."
        )
    if quote_currency != domestic_currency and (
        not isfinite(config.fx_quote_to_domestic_rate)
        or config.fx_quote_to_domestic_rate <= 0
    ):
        raise ValueError(
            "FX quote-to-domestic rate must be positive and finite."
        )

    base_rate = (
        1.0
        if base_currency == domestic_currency
        else config.fx_base_to_domestic_rate
    )
    quote_rate = (
        1.0
        if quote_currency == domestic_currency
        else config.fx_quote_to_domestic_rate
    )
    base_value = config.fx_base_notional * base_rate
    quote_value = config.fx_quote_notional * quote_rate
    if base_currency == domestic_currency:
        adjusted_notional = quote_value
    elif quote_currency == domestic_currency:
        adjusted_notional = base_value
    else:
        adjusted_notional = max(base_value, quote_value)

    delta, option_details = calculate_supervisory_delta(
        config, OPTION_SUPERVISORY_VOLATILITY
    )
    details = (
        ("Domestic currency", domestic_currency),
        ("FX base currency", base_currency),
        ("FX quote currency", quote_currency),
        ("FX base notional", config.fx_base_notional),
        ("FX quote notional", config.fx_quote_notional),
        ("FX base-to-domestic rate", base_rate),
        ("FX quote-to-domestic rate", quote_rate),
    ) + option_details
    return build_calculation(
        config,
        adjusted_notional,
        SUPERVISORY_FACTOR,
        delta,
        details,
    )

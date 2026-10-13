from dataclasses import dataclass
from datetime import date
from math import exp, isfinite, log, sqrt
from statistics import NormalDist
from typing import Protocol


MINIMUM_MATURITY_YEARS = 10 / 250
TRANSACTION_ADJUSTMENT_FACTORS = {
    "standard": 1.0,
    "basis": 0.5,
    "volatility": 5.0,
}


class AssetClassConfiguration(Protocol):
    asset_class: str
    instrument_type: str
    transaction_type: str
    start_date: date
    end_date: date
    valuation_date: date | None
    notional: float
    supervisory_delta: float
    currency: str
    domestic_currency: str
    notional_to_domestic_rate: float
    option_type: str
    option_position: str
    option_expiry_date: date | None
    option_underlying_price: float
    option_strike_price: float
    option_lambda: float
    fx_base_currency: str
    fx_quote_currency: str
    fx_base_notional: float
    fx_quote_notional: float
    fx_base_to_domestic_rate: float
    fx_quote_to_domestic_rate: float
    credit_reference_type: str
    credit_rating_bucket: str
    credit_index_grade: str
    equity_reference_type: str
    underlying_price: float
    underlying_units: float
    underlying_to_domestic_rate: float
    commodity_hedging_set: str
    commodity_type: str


@dataclass(frozen=True)
class AssetClassCalculation:
    supervisory_duration: float | None
    maturity_factor: float
    adjusted_notional: float
    effective_notional: float
    supervisory_delta: float
    supervisory_factor: float
    add_on: float
    details: tuple[tuple[str, str | float | date], ...]


def valuation_date(config: AssetClassConfiguration) -> date:
    return config.valuation_date or config.start_date


def calculate_maturity_factor(
    end_date: date, valuation_date_: date
) -> float:
    remaining_years = max((end_date - valuation_date_).days / 365, 0.0)
    floored_maturity = max(remaining_years, MINIMUM_MATURITY_YEARS)
    return sqrt(min(floored_maturity, 1.0))


def calculate_supervisory_duration(
    start_date: date, end_date: date, valuation_date_: date
) -> float:
    if valuation_date_ > start_date:
        return 0.0

    start_years = max((start_date - valuation_date_).days / 365, 0.0)
    end_years = max((end_date - valuation_date_).days / 365, 0.0)
    duration = (
        exp(-0.05 * start_years) - exp(-0.05 * end_years)
    ) / 0.05
    return max(duration, MINIMUM_MATURITY_YEARS)


def calculate_supervisory_delta(
    config: AssetClassConfiguration,
    supervisory_volatility: float,
    supports_negative_prices: bool = False,
) -> tuple[float, tuple[tuple[str, str | float | date], ...]]:
    if config.instrument_type == "linear":
        if config.supervisory_delta not in {-1.0, 1.0}:
            raise ValueError(
                "Linear trades must use supervisory_delta of 1.0 or -1.0 "
                "to indicate direction."
            )
        return config.supervisory_delta, ()
    if config.instrument_type != "option":
        raise ValueError(
            "instrument_type must be 'linear' or 'option' "
            "(European vanilla option)."
        )
    if config.option_type not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'.")
    if config.option_position not in {"bought", "sold"}:
        raise ValueError("option_position must be 'bought' or 'sold'.")
    if config.option_expiry_date is None:
        raise ValueError("option_expiry_date is required for options.")

    value_date = valuation_date(config)
    if config.option_expiry_date > config.end_date:
        raise ValueError("Option expiry cannot be after the trade end date.")
    time_to_expiry = (config.option_expiry_date - value_date).days / 365
    if time_to_expiry <= 0:
        raise ValueError("Option expiry must be after the valuation date.")
    if not isfinite(config.option_underlying_price) or not isfinite(
        config.option_strike_price
    ):
        raise ValueError("Option price and strike must be finite.")
    if not isfinite(config.option_lambda) or config.option_lambda < 0:
        raise ValueError("option_lambda must be finite and non-negative.")
    if supervisory_volatility <= 0 or not isfinite(supervisory_volatility):
        raise ValueError("Supervisory volatility must be positive and finite.")

    price = config.option_underlying_price
    strike = config.option_strike_price
    lambda_shift = 0.0
    if price <= 0 or strike <= 0:
        if not supports_negative_prices or config.option_lambda <= 0:
            raise ValueError(
                "Non-positive option price or strike requires a positive "
                "option_lambda for this asset class."
            )
        price += config.option_lambda
        strike += config.option_lambda
        if price <= 0 or strike <= 0:
            raise ValueError(
                "option_lambda must make option price and strike positive."
            )
        lambda_shift = config.option_lambda

    sigma = supervisory_volatility
    denominator = sigma * sqrt(time_to_expiry)
    normal = NormalDist()
    if config.option_type == "call":
        delta = normal.cdf(
            (
                log(price / strike)
                + 0.5 * sigma**2 * time_to_expiry
            )
            / denominator
        )
    else:
        delta = -normal.cdf(
            (
                -log(price / strike)
                + 0.5 * sigma**2 * time_to_expiry
            )
            / denominator
        )
    if config.option_position == "sold":
        delta = -delta

    details = (
        ("Option type", config.option_type),
        ("Option position", config.option_position),
        ("Option expiry date", config.option_expiry_date),
        ("Option underlying price", config.option_underlying_price),
        ("Option strike price", config.option_strike_price),
        ("Supervisory volatility", supervisory_volatility),
        ("Option time to expiry (years)", time_to_expiry),
    )
    if lambda_shift:
        details += (
            ("Option lambda shift", lambda_shift),
            ("Shifted option underlying price", price),
            ("Shifted option strike price", strike),
        )
    return delta, details


def build_calculation(
    config: AssetClassConfiguration,
    adjusted_notional: float,
    supervisory_factor: float,
    supervisory_delta: float,
    details: tuple[tuple[str, str | float | date], ...],
    supervisory_duration: float | None = None,
) -> AssetClassCalculation:
    try:
        transaction_adjustment_factor = TRANSACTION_ADJUSTMENT_FACTORS[
            config.transaction_type
        ]
    except KeyError as error:
        supported_types = ", ".join(TRANSACTION_ADJUSTMENT_FACTORS)
        raise ValueError(
            f"Unsupported transaction_type {config.transaction_type!r}; "
            f"choose one of: {supported_types}."
        ) from error

    value_date = valuation_date(config)
    maturity_factor = calculate_maturity_factor(config.end_date, value_date)
    effective_notional = (
        adjusted_notional * maturity_factor * supervisory_delta
    )
    details += (
        ("Transaction type", config.transaction_type),
        ("Transaction adjustment factor", transaction_adjustment_factor),
        ("Base supervisory factor", supervisory_factor),
    )
    adjusted_supervisory_factor = (
        supervisory_factor * transaction_adjustment_factor
    )
    return AssetClassCalculation(
        supervisory_duration=supervisory_duration,
        maturity_factor=maturity_factor,
        adjusted_notional=adjusted_notional,
        effective_notional=effective_notional,
        supervisory_delta=supervisory_delta,
        supervisory_factor=adjusted_supervisory_factor,
        add_on=abs(effective_notional) * adjusted_supervisory_factor,
        details=details,
    )

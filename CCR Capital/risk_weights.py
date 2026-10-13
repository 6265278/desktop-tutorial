from __future__ import annotations

from math import isfinite
from typing import Protocol


class CounterpartyConfiguration(Protocol):
    counterparty_type: str
    counterparty_rating_bucket: str
    sovereign_is_canadian: bool
    sovereign_assessment_method: str
    sovereign_eca_score: str
    pse_status: str
    foreign_pse_risk_weight: float
    mdb_qualifies_for_zero_weight: bool
    financial_institution_treated_as_bank: bool
    bank_treatment: str
    bank_short_term: bool
    bank_scra_grade: str
    bank_meets_enhanced_scra_criteria: bool
    bank_simplified_short_term: bool
    corporate_type: str
    corporate_rating_bucket: str
    corporate_unrated_treatment: str
    specialized_lending_type: str


RATING_BUCKETS = {
    "1": "AAA to AA-",
    "2": "A+ to A-",
    "3": "BBB+ to BBB-",
    "4": "BB+ to B-",
    "5": "Below B-",
    "6": "Unrated",
}
SOVEREIGN_RISK_WEIGHTS = {
    "1": 0.00,
    "2": 0.20,
    "3": 0.50,
    "4": 1.00,
    "5": 1.50,
    "6": 1.00,
}
SOVEREIGN_ECA_RISK_WEIGHTS = {
    "0-1": 0.00,
    "2": 0.20,
    "3": 0.50,
    "4-6": 1.00,
    "7": 1.50,
}
PSE_RISK_WEIGHTS = {
    "1": 0.20,
    "2": 0.50,
    "3": 1.00,
    "4": 1.00,
    "5": 1.50,
    "6": 1.00,
}
MDB_RISK_WEIGHTS = {
    "1": 0.20,
    "2": 0.30,
    "3": 0.50,
    "4": 1.00,
    "5": 1.50,
    "6": 0.50,
}
BANK_ECRA_BASE_WEIGHTS = {
    "1": 0.20,
    "2": 0.30,
    "3": 0.50,
    "4": 1.00,
    "5": 1.50,
}
BANK_ECRA_SHORT_TERM_WEIGHTS = {
    "1": 0.20,
    "2": 0.20,
    "3": 0.20,
    "4": 0.50,
    "5": 1.50,
}
BANK_SCRA_WEIGHTS = {
    ("a", False): 0.40,
    ("b", False): 0.75,
    ("c", False): 1.50,
    ("a", True): 0.20,
    ("b", True): 0.50,
    ("c", True): 1.50,
}
CORPORATE_RATED_WEIGHTS = {
    "1": 0.20,
    "2": 0.50,
    "3": 0.75,
    "4": 1.00,
    "5": 1.50,
}
CORPORATE_RATING_BUCKETS = {
    "1": "AAA to AA-",
    "2": "A+ to A-",
    "3": "BBB+ to BBB-",
    "4": "BB+ to BB-",
    "5": "Below BB-",
}
CORPORATE_UNRATED_WEIGHTS = {
    "blanket_100": 1.00,
    "investment_grade": 0.65,
    "non_investment_grade": 1.35,
}
SPECIALIZED_LENDING_WEIGHTS = {
    "rated_1": 0.20,
    "rated_2": 0.50,
    "rated_3": 0.75,
    "rated_4": 1.00,
    "rated_5": 1.50,
    "object_or_commodities": 1.00,
    "project_pre_operational": 1.30,
    "project_operational": 1.00,
    "project_operational_high_quality": 0.80,
}


def resolve_counterparty_risk_weight(
    config: CounterpartyConfiguration,
) -> tuple[str, float]:
    """Resolve the standardized credit risk weight for a counterparty."""
    counterparty_type = config.counterparty_type

    if counterparty_type == "sovereign":
        if config.sovereign_is_canadian:
            return "Canadian sovereign / central bank", 0.0
        if config.sovereign_assessment_method == "eca":
            if config.sovereign_eca_score not in SOVEREIGN_ECA_RISK_WEIGHTS:
                raise ValueError("Invalid sovereign ECA risk score.")
            return (
                "Sovereign (eligible ECA score)",
                SOVEREIGN_ECA_RISK_WEIGHTS[config.sovereign_eca_score],
            )
        if config.sovereign_assessment_method != "rating":
            raise ValueError("Invalid sovereign assessment method.")
        rating = config.counterparty_rating_bucket
        if rating not in SOVEREIGN_RISK_WEIGHTS:
            raise ValueError("Invalid sovereign rating bucket.")
        return (
            f"Sovereign ({RATING_BUCKETS[rating]})",
            SOVEREIGN_RISK_WEIGHTS[rating],
        )

    if counterparty_type == "pse":
        if config.pse_status == "canadian_provincial":
            return "Canadian provincial/territorial PSE", 0.0
        if config.pse_status == "foreign":
            if (
                not isfinite(config.foreign_pse_risk_weight)
                or config.foreign_pse_risk_weight < 0
            ):
                raise ValueError(
                    "Foreign PSE risk weight must be non-negative."
                )
            return (
                "Foreign PSE (local treatment)",
                config.foreign_pse_risk_weight,
            )
        if config.pse_status != "other_canadian":
            raise ValueError("Invalid PSE status.")
        rating = config.counterparty_rating_bucket
        if rating not in PSE_RISK_WEIGHTS:
            raise ValueError("Invalid sovereign rating bucket for PSE.")
        return (
            f"Canadian PSE ({RATING_BUCKETS[rating]})",
            PSE_RISK_WEIGHTS[rating],
        )

    if counterparty_type == "mdb":
        if config.mdb_qualifies_for_zero_weight:
            return "Qualifying MDB", 0.0
        rating = config.counterparty_rating_bucket
        if rating not in MDB_RISK_WEIGHTS:
            raise ValueError("Invalid MDB rating bucket.")
        return (
            f"Other MDB ({RATING_BUCKETS[rating]})",
            MDB_RISK_WEIGHTS[rating],
        )

    if counterparty_type in {"bank", "financial"}:
        if (
            counterparty_type == "financial"
            and not config.financial_institution_treated_as_bank
        ):
            return _resolve_corporate_risk_weight(config)

        rating = config.counterparty_rating_bucket
        if config.bank_treatment == "ecra":
            if rating not in BANK_ECRA_BASE_WEIGHTS:
                raise ValueError("Invalid rated-bank rating bucket.")
            weights = (
                BANK_ECRA_SHORT_TERM_WEIGHTS
                if config.bank_short_term
                else BANK_ECRA_BASE_WEIGHTS
            )
            return f"Bank, ECRA ({RATING_BUCKETS[rating]})", weights[rating]
        if config.bank_treatment == "scra":
            if config.bank_scra_grade not in {"a", "b", "c"}:
                raise ValueError("SCRA grade must be 'a', 'b', or 'c'.")
            if (
                config.bank_scra_grade == "a"
                and config.bank_meets_enhanced_scra_criteria
            ):
                return "Bank, SCRA Grade A with enhanced criteria", 0.30
            return (
                f"Bank, SCRA Grade {config.bank_scra_grade.upper()}",
                BANK_SCRA_WEIGHTS[
                    (config.bank_scra_grade, config.bank_short_term)
                ],
            )
        if config.bank_treatment == "unrated_100":
            return "Bank, SCRA 100% option", 1.00
        if config.bank_treatment == "smsb_simplified":
            return (
                "Bank, eligible SMSB simplified treatment",
                0.20 if config.bank_simplified_short_term else 0.40,
            )
        if config.bank_treatment == "canadian_dsib":
            return "Qualifying Canadian D-SIB / D-SIFI", 0.15
        raise ValueError("Invalid bank treatment.")

    if counterparty_type == "corporate":
        return _resolve_corporate_risk_weight(config)

    if counterparty_type == "individual":
        return "Individual, non-regulatory retail", 1.00

    raise ValueError(
        "counterparty_type must be sovereign, pse, mdb, bank, "
        "financial, corporate, or individual."
    )


def _resolve_corporate_risk_weight(
    config: CounterpartyConfiguration,
) -> tuple[str, float]:
    if config.corporate_type == "rated_general":
        rating = config.corporate_rating_bucket
        if rating not in CORPORATE_RATED_WEIGHTS:
            raise ValueError("Invalid corporate rating bucket.")
        return (
            f"Corporate, rated ({CORPORATE_RATING_BUCKETS[rating]})",
            CORPORATE_RATED_WEIGHTS[rating],
        )
    if config.corporate_type == "unrated_general":
        if config.corporate_unrated_treatment not in CORPORATE_UNRATED_WEIGHTS:
            raise ValueError("Invalid unrated corporate treatment.")
        return (
            "Corporate, unrated",
            CORPORATE_UNRATED_WEIGHTS[config.corporate_unrated_treatment],
        )
    if config.corporate_type == "unrated_sme":
        return "Corporate SME, unrated", 0.75
    if config.corporate_type == "us_gse":
        return "US Government Sponsored Enterprise", 0.20
    if config.corporate_type == "specialized":
        lending_type = config.specialized_lending_type
        if lending_type not in SPECIALIZED_LENDING_WEIGHTS:
            raise ValueError("Invalid specialized lending type.")
        if lending_type.startswith("rated_"):
            rating = lending_type.removeprefix("rated_")
            return (
                "Specialized lending, issue-rated "
                f"({CORPORATE_RATING_BUCKETS[rating]})",
                SPECIALIZED_LENDING_WEIGHTS[lending_type],
            )
        return (
            "Corporate, specialized lending",
            SPECIALIZED_LENDING_WEIGHTS[lending_type],
        )

    raise ValueError("Invalid corporate counterparty classification.")

"""Pure, explainable Sura Score rules shared by the PWA and Bank Portal."""

from dataclasses import dataclass
from statistics import fmean, pstdev

MAX_SCORE = 1000
PILLAR_WEIGHTS: dict[str, float] = {
    "commitment_behaviour": 0.35,
    "repayment_behaviour": 0.25,
    "transaction_stability": 0.20,
    "institutional_verification": 0.12,
    "social_reliability": 0.08,
}
ENTRY_TIER_BASELINE = round(PILLAR_WEIGHTS["institutional_verification"] * MAX_SCORE)
COSIGNERS_FOR_FULL_SCORE = 2
SCORE_VERSION = "trd-5.2-v1"


@dataclass(frozen=True)
class ScoreSignals:
    locks_joined: int = 0
    locks_completed: int = 0
    contributions_due: int = 0
    contributions_on_time: int = 0
    float_repayments: int = 0
    float_repayments_on_time: int = 0
    activity_intervals_days: tuple[float, ...] = ()
    institution_verified: bool = False
    cosigners: int = 0


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return min(1.0, max(0.0, numerator / denominator))


def _regularity(intervals: tuple[float, ...]) -> float:
    if len(intervals) < 2:
        return 0.0
    mean = fmean(intervals)
    if mean <= 0:
        return 0.0
    return max(0.0, 1.0 - (pstdev(intervals) / mean))


def commitment_behaviour(signals: ScoreSignals) -> float:
    return (_rate(signals.locks_completed, signals.locks_joined) + _rate(
        signals.contributions_on_time, signals.contributions_due
    )) / 2


def repayment_behaviour(signals: ScoreSignals) -> float:
    return _rate(signals.float_repayments_on_time, signals.float_repayments)


def transaction_stability(signals: ScoreSignals) -> float:
    return _regularity(signals.activity_intervals_days)


def institutional_verification(signals: ScoreSignals) -> float:
    return 1.0 if signals.institution_verified else 0.0


def social_reliability(signals: ScoreSignals) -> float:
    return _rate(signals.cosigners, COSIGNERS_FOR_FULL_SCORE)


PILLAR_RULES = {
    "commitment_behaviour": commitment_behaviour,
    "repayment_behaviour": repayment_behaviour,
    "transaction_stability": transaction_stability,
    "institutional_verification": institutional_verification,
    "social_reliability": social_reliability,
}


def pillar_sub_scores(signals: ScoreSignals) -> dict[str, float]:
    return {name: rule(signals) for name, rule in PILLAR_RULES.items()}


def pillar_points(signals: ScoreSignals) -> dict[str, int]:
    return {
        name: round(sub_score * PILLAR_WEIGHTS[name] * MAX_SCORE)
        for name, sub_score in pillar_sub_scores(signals).items()
    }


def score_breakdown(signals: ScoreSignals) -> dict[str, int]:
    return pillar_points(signals)


def calculate_score(signals: ScoreSignals) -> int:
    return sum(pillar_points(signals).values())


def tier_for_score(score: int) -> str:
    if score < ENTRY_TIER_BASELINE:
        return "unverified"
    if score < 350:
        return "entry"
    if score < 700:
        return "building"
    return "established"


def build_score_report(signals: ScoreSignals) -> dict:
    points = pillar_points(signals)
    score = sum(points.values())
    return {
        "score": score,
        "breakdown": points,
        "sub_scores": pillar_sub_scores(signals),
        "weights": dict(PILLAR_WEIGHTS),
        "tier": tier_for_score(score),
        "entry_tier": score <= ENTRY_TIER_BASELINE,
        "score_version": SCORE_VERSION,
    }


def exceeds_entry_tier(score: int) -> bool:
    return score > ENTRY_TIER_BASELINE

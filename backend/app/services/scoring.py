"""Sura Score rule engine.

Implements Sura-TRD section 5.2: a transparent weighted sum across five pillars,
deliberately not a trained model. Every point on the score traces back to a named
pillar and a named signal, which is what makes it auditable for a bank.

Everything in this module is pure. No database, no clock, no API. The score is
recomputed from signals on demand rather than mutated in place, so any score can
be reproduced from the events that produced it.
"""

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

# A brand-new verified user has only the institutional verification pillar, which
# is 0.12 of the maximum. This is the anchor the section 5.1 ordering and cap rule
# compares against, so it is derived, not hand-picked.
ENTRY_TIER_BASELINE = round(PILLAR_WEIGHTS["institutional_verification"] * MAX_SCORE)

# Two verified co-signers is treated as full social reliability. Beyond that the
# pillar stops growing, so network size can never outweigh behaviour.
COSIGNERS_FOR_FULL_SCORE = 2


@dataclass(frozen=True)
class ScoreSignals:
    """The raw observable behaviour a score is derived from."""

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
    """1.0 when activity is perfectly periodic, lower the more erratic it is.

    Uses the coefficient of variation, so it measures spread relative to the
    average gap rather than absolute spread.
    """
    if len(intervals) < 2:
        return 0.0
    mean = fmean(intervals)
    if mean <= 0:
        return 0.0
    return max(0.0, 1.0 - (pstdev(intervals) / mean))


def commitment_behaviour(signals: ScoreSignals) -> float:
    """Did they finish what they started, and did they pay on time."""
    completion = _rate(signals.locks_completed, signals.locks_joined)
    punctuality = _rate(signals.contributions_on_time, signals.contributions_due)
    return (completion + punctuality) / 2


def repayment_behaviour(signals: ScoreSignals) -> float:
    """How they handled live, real-money Sura Float obligations."""
    return _rate(signals.float_repayments_on_time, signals.float_repayments)


def transaction_stability(signals: ScoreSignals) -> float:
    """Regularity of account activity, not its size."""
    return _regularity(signals.activity_intervals_days)


def institutional_verification(signals: ScoreSignals) -> float:
    """Identity confirmation. Binary by design, and the entire entry tier."""
    return 1.0 if signals.institution_verified else 0.0


def social_reliability(signals: ScoreSignals) -> float:
    """Peer co-signers from the same verified circle. Light touch, not punitive."""
    return _rate(signals.cosigners, COSIGNERS_FOR_FULL_SCORE)


PILLAR_RULES = {
    "commitment_behaviour": commitment_behaviour,
    "repayment_behaviour": repayment_behaviour,
    "transaction_stability": transaction_stability,
    "institutional_verification": institutional_verification,
    "social_reliability": social_reliability,
}


def pillar_sub_scores(signals: ScoreSignals) -> dict[str, float]:
    """Each pillar as a 0.0 to 1.0 sub-score, before weighting."""
    return {name: rule(signals) for name, rule in PILLAR_RULES.items()}


def pillar_points(signals: ScoreSignals) -> dict[str, int]:
    """Each pillar's actual contribution to the score, in points.

    Rounded per pillar so the breakdown shown to a user always sums exactly to the
    score they were given.
    """
    sub_scores = pillar_sub_scores(signals)
    return {
        name: round(sub_score * PILLAR_WEIGHTS[name] * MAX_SCORE)
        for name, sub_score in sub_scores.items()
    }


def score_breakdown(signals: ScoreSignals) -> dict[str, int]:
    return pillar_points(signals)


def calculate_score(signals: ScoreSignals) -> int:
    return sum(pillar_points(signals).values())


def build_score_report(signals: ScoreSignals) -> dict:
    """Shape stored in score_history and returned by GET /v1/score/{user_id}."""
    sub_scores = pillar_sub_scores(signals)
    points = pillar_points(signals)
    return {
        "score": sum(points.values()),
        "breakdown": points,
        "sub_scores": sub_scores,
        "weights": dict(PILLAR_WEIGHTS),
        "entry_tier": calculate_score(signals) <= ENTRY_TIER_BASELINE,
    }


def exceeds_entry_tier(score: int) -> bool:
    """Section 5.1 eligibility check for an early payout slot."""
    return score > ENTRY_TIER_BASELINE

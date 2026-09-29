"""Golden tests for the authoritative five-pillar Sura Score engine."""

from app.services.scoring import (
    ENTRY_TIER_BASELINE,
    MAX_SCORE,
    PILLAR_WEIGHTS,
    ScoreSignals,
    build_score_report,
    calculate_score,
    exceeds_entry_tier,
    pillar_points,
    score_breakdown,
    social_reliability,
    transaction_stability,
)


VERIFIED_NEWCOMER = ScoreSignals(institution_verified=True)
COMPLETED_ONE_ROTATION = ScoreSignals(
    locks_joined=1,
    locks_completed=1,
    contributions_due=4,
    contributions_on_time=4,
    activity_intervals_days=(7.0, 7.0, 7.0),
    institution_verified=True,
    cosigners=2,
)


def test_verified_newcomer_is_exactly_the_entry_tier_baseline():
    assert calculate_score(VERIFIED_NEWCOMER) == ENTRY_TIER_BASELINE == 120
    assert pillar_points(VERIFIED_NEWCOMER) == {
        "commitment_behaviour": 0,
        "repayment_behaviour": 0,
        "transaction_stability": 0,
        "institutional_verification": 120,
        "social_reliability": 0,
    }


def test_full_rotation_is_a_reproducible_750_score():
    assert calculate_score(COMPLETED_ONE_ROTATION) == 750
    report = build_score_report(COMPLETED_ONE_ROTATION)
    assert report["tier"] == "established"
    assert report["sub_scores"]["commitment_behaviour"] == 1.0


def test_missed_contribution_reduces_commitment_points():
    missed = ScoreSignals(
        locks_joined=1,
        locks_completed=1,
        contributions_due=4,
        contributions_on_time=3,
        activity_intervals_days=(7.0, 7.0, 7.0),
        institution_verified=True,
        cosigners=2,
    )
    assert pillar_points(missed)["commitment_behaviour"] == 306
    assert calculate_score(missed) == 706


def test_weights_sum_to_one_and_points_sum_to_score():
    assert sum(PILLAR_WEIGHTS.values()) == 1.0
    assert score_breakdown(COMPLETED_ONE_ROTATION) == pillar_points(COMPLETED_ONE_ROTATION)
    assert sum(score_breakdown(COMPLETED_ONE_ROTATION).values()) == calculate_score(COMPLETED_ONE_ROTATION)


def test_score_is_bounded_and_monotonic_for_on_time_contributions():
    impossible = ScoreSignals(locks_completed=99, contributions_on_time=99, cosigners=500, institution_verified=True)
    assert 0 <= calculate_score(impossible) <= MAX_SCORE
    weaker = ScoreSignals(locks_joined=1, locks_completed=1, contributions_due=4, contributions_on_time=2, institution_verified=True)
    stronger = ScoreSignals(locks_joined=1, locks_completed=1, contributions_due=4, contributions_on_time=4, institution_verified=True)
    assert calculate_score(weaker) < calculate_score(stronger)


def test_stability_and_social_signals_obey_their_limits():
    assert transaction_stability(ScoreSignals(activity_intervals_days=(7.0, 7.0, 7.0))) == 1.0
    assert transaction_stability(ScoreSignals(activity_intervals_days=(7.0,))) == 0.0
    assert social_reliability(ScoreSignals(cosigners=50)) == 1.0
    assert exceeds_entry_tier(calculate_score(COMPLETED_ONE_ROTATION)) is True

"""Golden set for the Sura Score rule engine.

Every expected number here is hand-derived from Sura-TRD 5.2 so a change to a
weight or a rule shows up as a failing test instead of a silently different
score. Re-run this file after any change to app/services/scoring.py.
"""

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


def test_new_verified_user_sits_exactly_on_the_entry_tier_baseline():
    assert calculate_score(VERIFIED_NEWCOMER) == ENTRY_TIER_BASELINE == 120


def test_entry_tier_baseline_is_only_the_verification_pillar():
    points = pillar_points(VERIFIED_NEWCOMER)
    assert points == {
        "commitment_behaviour": 0,
        "repayment_behaviour": 0,
        "transaction_stability": 0,
        "institutional_verification": 120,
        "social_reliability": 0,
    }


def test_unverified_user_with_no_history_scores_zero():
    assert calculate_score(ScoreSignals()) == 0


def test_completing_a_full_rotation_scores_750():
    # 350 commitment + 0 repayment (no Float history yet)
    # + 200 transaction stability + 120 verification + 80 social
    assert calculate_score(COMPLETED_ONE_ROTATION) == 750


def test_one_missed_contribution_lowers_the_score_to_706():
    missed = ScoreSignals(
        locks_joined=1,
        locks_completed=1,
        contributions_due=4,
        contributions_on_time=3,
        activity_intervals_days=(7.0, 7.0, 7.0),
        institution_verified=True,
        cosigners=2,
    )
    # punctuality 3/4, so commitment sub-score is (1.0 + 0.75) / 2 = 0.875
    assert pillar_points(missed)["commitment_behaviour"] == 306
    assert calculate_score(missed) == 706


def test_every_pillar_at_maximum_sums_to_the_maximum_score():
    everything = ScoreSignals(
        locks_joined=1,
        locks_completed=1,
        contributions_due=4,
        contributions_on_time=4,
        float_repayments=3,
        float_repayments_on_time=3,
        activity_intervals_days=(7.0, 7.0, 7.0),
        institution_verified=True,
        cosigners=2,
    )
    assert calculate_score(everything) == MAX_SCORE == 1000


def test_breakdown_always_sums_exactly_to_the_score():
    cases = [
        ScoreSignals(),
        VERIFIED_NEWCOMER,
        COMPLETED_ONE_ROTATION,
        ScoreSignals(locks_joined=3, locks_completed=1, cosigners=1),
        ScoreSignals(activity_intervals_days=(2.0, 30.0, 3.0, 29.0)),
    ]
    for signals in cases:
        assert sum(score_breakdown(signals).values()) == calculate_score(signals)


def test_weights_match_the_trd():
    assert PILLAR_WEIGHTS == {
        "commitment_behaviour": 0.35,
        "repayment_behaviour": 0.25,
        "transaction_stability": 0.20,
        "institutional_verification": 0.12,
        "social_reliability": 0.08,
    }
    assert sum(PILLAR_WEIGHTS.values()) == 1.0


def test_score_never_leaves_the_bounds_even_with_impossible_input():
    impossible = ScoreSignals(
        locks_joined=0,
        locks_completed=99,
        contributions_due=0,
        contributions_on_time=99,
        float_repayments=1,
        float_repayments_on_time=99,
        cosigners=500,
        institution_verified=True,
    )
    assert 0 <= calculate_score(impossible) <= MAX_SCORE


def test_more_on_time_contributions_never_lowers_the_score():
    weaker = ScoreSignals(
        locks_joined=1,
        locks_completed=1,
        contributions_due=4,
        contributions_on_time=2,
        institution_verified=True,
    )
    stronger = ScoreSignals(
        locks_joined=1,
        locks_completed=1,
        contributions_due=4,
        contributions_on_time=4,
        institution_verified=True,
    )
    assert calculate_score(weaker) < calculate_score(stronger)


def test_regular_activity_scores_full_stability_and_erratic_activity_does_not():
    assert transaction_stability(ScoreSignals(activity_intervals_days=(7.0, 7.0, 7.0))) == 1.0
    erratic = transaction_stability(ScoreSignals(activity_intervals_days=(2.0, 30.0, 3.0, 29.0)))
    assert 0.0 < erratic < 0.2


def test_transaction_stability_is_zero_without_enough_history():
    assert transaction_stability(ScoreSignals()) == 0.0
    assert transaction_stability(ScoreSignals(activity_intervals_days=(7.0,))) == 0.0


def test_social_reliability_caps_at_two_cosigners():
    assert social_reliability(ScoreSignals(cosigners=2)) == 1.0
    assert social_reliability(ScoreSignals(cosigners=50)) == 1.0


def test_entry_tier_gate_for_the_anchor_and_cap_rule():
    assert exceeds_entry_tier(calculate_score(VERIFIED_NEWCOMER)) is False
    assert exceeds_entry_tier(calculate_score(COMPLETED_ONE_ROTATION)) is True


def test_calculation_is_pure_and_repeatable():
    first = calculate_score(COMPLETED_ONE_ROTATION)
    assert first == calculate_score(COMPLETED_ONE_ROTATION) == 750


def test_score_report_carries_the_audit_trail():
    report = build_score_report(COMPLETED_ONE_ROTATION)
    assert report["score"] == 750
    assert report["entry_tier"] is False
    assert report["sub_scores"]["commitment_behaviour"] == 1.0
    assert report["weights"] == PILLAR_WEIGHTS

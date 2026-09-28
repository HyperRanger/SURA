from app.services.scoring import build_score_snapshot, calculate_score, score_breakdown


def test_calculate_score_caps_at_hundred():
    score = calculate_score(95, [10, 20])
    assert score == 100


def test_score_breakdown():
    breakdown = score_breakdown()
    assert breakdown == {
        "commitment_behaviour": 0.35,
        "repayment_behaviour": 0.25,
        "transaction_stability": 0.20,
        "institutional_verification": 0.12,
        "social_reliability": 0.08,
    }


def test_score_snapshot_reflects_completed_and_missed_cycles():
    snapshot = build_score_snapshot(12, [12, 10], missed_cycles=1, completed_cycles=2)
    assert snapshot["score"] == 49
    assert snapshot["breakdown"] == {
        "commitment_behaviour": 0.35,
        "repayment_behaviour": 0.25,
        "transaction_stability": 0.20,
        "institutional_verification": 0.12,
        "social_reliability": 0.08,
    }

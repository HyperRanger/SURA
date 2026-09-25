from app.services.scoring import calculate_score, score_breakdown


def test_calculate_score():
    score = calculate_score(50, [10, 5])
    assert score == 65


def test_score_breakdown():
    breakdown = score_breakdown()
    assert breakdown["commitment_behaviour"] == 0.35
    assert breakdown["transaction_stability"] == 0.20

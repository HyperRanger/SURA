def calculate_score(base_score: int, contribution_history: list[int] | None = None) -> int:
    history = contribution_history or []
    bonus = sum(history)
    return max(0, min(100, base_score + bonus))


def score_breakdown() -> dict:
    return {
        "commitment_behaviour": 0.35,
        "repayment_behaviour": 0.25,
        "transaction_stability": 0.20,
        "institutional_verification": 0.12,
        "social_reliability": 0.08,
    }

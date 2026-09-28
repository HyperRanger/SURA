import json
from typing import Any


def calculate_score(
    base_score: int,
    contribution_history: list[int] | None = None,
    missed_cycles: int = 0,
    completed_cycles: int = 0,
) -> int:
    history = contribution_history or []
    bonus = sum(history)
    score = base_score + bonus + (completed_cycles * 15) - (missed_cycles * 15)
    return max(0, min(100, score))


def score_breakdown() -> dict[str, float]:
    return {
        "commitment_behaviour": 0.35,
        "repayment_behaviour": 0.25,
        "transaction_stability": 0.20,
        "institutional_verification": 0.12,
        "social_reliability": 0.08,
    }


def build_score_snapshot(
    base_score: int = 12,
    contribution_history: list[int] | None = None,
    missed_cycles: int = 0,
    completed_cycles: int = 0,
) -> dict[str, Any]:
    history = contribution_history or []
    snapshot = {
        "base_score": base_score,
        "contribution_history": list(history),
        "missed_cycles": missed_cycles,
        "completed_cycles": completed_cycles,
        "score": calculate_score(base_score, history, missed_cycles, completed_cycles),
        "breakdown": score_breakdown(),
    }
    return snapshot


def serialize_score_snapshot(snapshot: dict[str, Any]) -> str:
    return json.dumps({
        "base_score": snapshot["base_score"],
        "contribution_history": snapshot["contribution_history"],
        "missed_cycles": snapshot["missed_cycles"],
        "completed_cycles": snapshot["completed_cycles"],
        "score": snapshot["score"],
        "breakdown": snapshot["breakdown"],
    })

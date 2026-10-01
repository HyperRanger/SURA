import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContributionEvaluation:
    contribution_status: str
    cycle_status: str
    commitment_status: str
    beneficiary_status: str
    member_total_before: int
    member_total_after: int
    cycle_total_before: int
    cycle_total_after: int
    expected_member_amount: int
    required_cycle_total: int
    member_count: int
    distinct_contributors: int
    cycle_complete: bool
    cycle_missed: bool

    def to_rule_trace(self) -> dict[str, Any]:
        return {
            "contribution_status": self.contribution_status,
            "cycle_status": self.cycle_status,
            "commitment_status": self.commitment_status,
            "beneficiary_status": self.beneficiary_status,
            "member_total_before": self.member_total_before,
            "member_total_after": self.member_total_after,
            "cycle_total_before": self.cycle_total_before,
            "cycle_total_after": self.cycle_total_after,
            "expected_member_amount": self.expected_member_amount,
            "required_cycle_total": self.required_cycle_total,
            "member_count": self.member_count,
            "distinct_contributors": self.distinct_contributors,
            "cycle_complete": self.cycle_complete,
            "cycle_missed": self.cycle_missed,
        }


def evaluate_contribution(
    *,
    contribution_amount: int,
    expected_member_amount: int,
    member_total_before: int,
    cycle_total_before: int,
    member_count: int,
    distinct_contributors: int,
) -> ContributionEvaluation:
    member_total_after = member_total_before + contribution_amount
    cycle_total_after = cycle_total_before + contribution_amount
    required_cycle_total = expected_member_amount * member_count

    contribution_status = "full" if member_total_after >= expected_member_amount else "partial"
    cycle_complete = member_total_after >= expected_member_amount and cycle_total_after >= required_cycle_total
    # A missed cycle is a deadline decision, not a contribution-total decision.
    # All members may have made partial contributions before the due date.
    cycle_missed = False

    if cycle_complete:
        cycle_status = "completed"
        commitment_status = "completed"
        beneficiary_status = "paid"
    else:
        cycle_status = "active"
        commitment_status = "active"
        beneficiary_status = "scheduled"

    return ContributionEvaluation(
        contribution_status=contribution_status,
        cycle_status=cycle_status,
        commitment_status=commitment_status,
        beneficiary_status=beneficiary_status,
        member_total_before=member_total_before,
        member_total_after=member_total_after,
        cycle_total_before=cycle_total_before,
        cycle_total_after=cycle_total_after,
        expected_member_amount=expected_member_amount,
        required_cycle_total=required_cycle_total,
        member_count=member_count,
        distinct_contributors=distinct_contributors,
        cycle_complete=cycle_complete,
        cycle_missed=cycle_missed,
    )


def dump_rule_trace(evaluation: ContributionEvaluation) -> str:
    return json.dumps(evaluation.to_rule_trace())

"""
Decision engine — combines trust, plausibility, and contradiction.

Returns: AUTO_CONFIRMED | REQUIRES_REVIEW | REJECTED

Decision logic is DETERMINISTIC and TESTABLE.
LLM does NOT make the final decision.
"""
from app.services.trust_service import TrustResult
from app.services.plausibility_service import PlausibilityResult
from app.services.contradiction_service import ContradictionResult

# Thresholds
HIGH_TRUST = 0.65
LOW_TRUST = 0.35


class DecisionResult:
    def __init__(self, decision: str, reasoning_context: dict):
        self.decision = decision  # AUTO_CONFIRMED | REQUIRES_REVIEW | REJECTED
        self.reasoning_context = reasoning_context


def make_decision(
    trust: TrustResult,
    plausibility: PlausibilityResult,
    contradiction: ContradictionResult,
    speaker_status: str,
) -> DecisionResult:
    """
    Deterministic decision engine.

    AUTO_CONFIRMED conditions (ALL must hold):
    - Speaker is IDENTIFIED or trust score is HIGH
    - Plausibility check passes
    - Contradiction is NO_CONFLICT

    REJECTED conditions (ANY):
    - STRONG_CONFLICT contradiction
    - Speaker UNKNOWN AND trust < LOW_TRUST AND plausibility fails

    Otherwise: REQUIRES_REVIEW
    """
    context = {
        "trust_score": trust.score,
        "trust_components": trust.components,
        "plausibility_passed": plausibility.passed,
        "plausibility_reason": plausibility.reason,
        "contradiction_level": contradiction.level,
        "contradiction_reason": contradiction.reason,
        "speaker_status": speaker_status,
    }

    # REJECTED: Strong contradiction
    if contradiction.level == "STRONG_CONFLICT":
        # Only auto-reject if speaker is also unknown or untrusted
        if speaker_status == "UNKNOWN" or trust.score < LOW_TRUST:
            return DecisionResult("REJECTED", context)
        # If speaker is known and trusted, still flag for review on strong conflict
        return DecisionResult("REQUIRES_REVIEW", context)

    # AUTO_CONFIRMED: All conditions met
    speaker_ok = speaker_status == "IDENTIFIED" or trust.score >= HIGH_TRUST
    no_issues = plausibility.passed and contradiction.level == "NO_CONFLICT"

    if speaker_ok and no_issues:
        return DecisionResult("AUTO_CONFIRMED", context)

    # REJECTED: Unknown speaker, failing plausibility, and possible conflict
    if (
        speaker_status == "UNKNOWN"
        and trust.score < LOW_TRUST
        and not plausibility.passed
    ):
        return DecisionResult("REJECTED", context)

    # Everything else: REQUIRES_REVIEW
    return DecisionResult("REQUIRES_REVIEW", context)

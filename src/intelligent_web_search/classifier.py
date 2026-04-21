from __future__ import annotations

from dataclasses import dataclass

from .models import HeuristicDecision


@dataclass
class BorderlineClassifierResult:
    override: str | None
    confidence: float
    reason: str


class BorderlineClassifier:
    """Optional hook for a future small model.

    Current implementation is a no-op placeholder. The orchestrator can call this
    only for borderline cases if enabled later.
    """

    def decide(self, decision: HeuristicDecision) -> BorderlineClassifierResult:
        return BorderlineClassifierResult(
            override=None,
            confidence=0.0,
            reason="classifier_not_enabled",
        )

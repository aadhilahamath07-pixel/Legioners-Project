"""
Explainable multi-factor pothole prioritization for Legioners Road Intelligence.

Prototype only: default weights and thresholds must be evaluated with domain experts
or historical maintenance data before being used for real maintenance decisions.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping

DEFAULT_WEIGHTS = {
    "severity": 0.35,
    "traffic": 0.25,
    "road_importance": 0.20,
    "location_risk": 0.10,
    "accessibility": 0.10,
}
FACTOR_LABELS = {
    "severity": "Damage severity",
    "traffic": "Traffic exposure",
    "road_importance": "Road importance",
    "location_risk": "Location risk",
    "accessibility": "Road usability/access",
}


@dataclass
class PriorityResult:
    score: float
    priority: str
    explanation: str
    factor_scores: dict[str, float]
    weighted_contributions: dict[str, float]
    missing_factors: list[str]
    weights_used: dict[str, float]
    emergency_override: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_score(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number from 0 to 100.")
    value = float(value)
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100.")
    return value


def calculate_priority(
    factors: Mapping[str, Any],
    *,
    weights: Mapping[str, float] | None = None,
    emergency_override: bool = False,
) -> dict[str, Any]:
    """Score available factors; report missing data instead of silently treating it as zero."""
    chosen_weights = dict(weights or DEFAULT_WEIGHTS)
    if set(chosen_weights) != set(DEFAULT_WEIGHTS):
        raise ValueError("Weights must contain exactly: " + ", ".join(DEFAULT_WEIGHTS))
    for name, weight in chosen_weights.items():
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0:
            raise ValueError(f"Weight for {name} must be a non-negative number.")
    total_weight = sum(chosen_weights.values())
    if total_weight <= 0:
        raise ValueError("At least one weight must be greater than zero.")
    normalized = {k: float(v) / total_weight for k, v in chosen_weights.items()}

    valid: dict[str, float] = {}
    missing: list[str] = []
    for name in DEFAULT_WEIGHTS:
        value = factors.get(name)
        if value is None:
            missing.append(name)
        else:
            valid[name] = _validate_score(name, value)
    available_weight = sum(normalized[name] for name in valid)
    if available_weight <= 0:
        raise ValueError("At least one valid factor score is required.")

    effective = {name: normalized[name] / available_weight for name in valid}
    contributions = {name: round(valid[name] * effective[name], 2) for name in valid}
    score = round(sum(contributions.values()), 2)

    if emergency_override:
        priority, reason = "Critical", "An authorized emergency rule overrides the calculated ranking."
    elif score >= 80:
        priority, reason = "High", "The combined risk score is high."
    elif score >= 55:
        priority, reason = "Medium", "The combined risk score is moderate."
    else:
        priority, reason = "Low", "The combined risk score is lower than the higher-ranked cases."

    top = sorted(valid, key=lambda name: contributions[name], reverse=True)[:2]
    drivers = " Main contributing factors: " + ", ".join(
        f"{FACTOR_LABELS[name]} ({valid[name]:.0f}/100)" for name in top
    ) + "." if top else ""
    missing_note = ""
    if missing:
        missing_note = " Missing data: " + ", ".join(FACTOR_LABELS[n] for n in missing)
        missing_note += "; score uses available factors with re-normalized weights."

    return PriorityResult(
        score=score,
        priority=priority,
        explanation=reason + drivers + missing_note,
        factor_scores=valid,
        weighted_contributions=contributions,
        missing_factors=missing,
        weights_used={k: round(v, 4) for k, v in effective.items()},
        emergency_override=emergency_override,
    ).to_dict()


def rank_inspections(
    inspections: list[Mapping[str, Any]],
    *,
    factor_key: str = "priority_factors",
) -> list[dict[str, Any]]:
    """Rank inspection dictionaries with a `priority_factors` mapping, highest first."""
    ranked = []
    for inspection in inspections:
        factors = inspection.get(factor_key)
        if not isinstance(factors, Mapping):
            raise ValueError(f"Each inspection must contain a '{factor_key}' mapping.")
        result = calculate_priority(
            factors,
            emergency_override=bool(inspection.get("emergency_override", False)),
        )
        ranked.append({**dict(inspection), "priority_result": result})
    ranked.sort(
        key=lambda item: (item["priority_result"]["emergency_override"], item["priority_result"]["score"]),
        reverse=True,
    )
    for rank, item in enumerate(ranked, start=1):
        item["priority_rank"] = rank
    return ranked


if __name__ == "__main__":
    # Illustrative smoke test only; these are not real road inspection data.
    example = {"severity": 90, "traffic": 80, "road_importance": 85, "location_risk": 70, "accessibility": 75}
    print(calculate_priority(example))

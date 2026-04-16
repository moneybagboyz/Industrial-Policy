"""Metric decomposition utilities for explainability."""

from __future__ import annotations


def decompose_metric(metric_name: str, contributions: dict[str, float]) -> dict[str, object]:
    """Return normalized decomposition payload for UI traces."""
    total = sum(contributions.values())
    return {
        "metric": metric_name,
        "total_delta": total,
        "drivers": [{"name": k, "contribution": v} for k, v in contributions.items()],
    }


def has_hidden_modifiers(trace_payload: dict[str, object]) -> bool:
    """Simple guard: total delta must equal sum of visible drivers."""
    drivers = trace_payload.get("drivers", [])
    total = trace_payload.get("total_delta", 0.0)
    visible = sum(float(item["contribution"]) for item in drivers)
    return round(float(total) - visible, 10) != 0.0

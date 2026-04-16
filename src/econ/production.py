"""Production helpers for constrained sector output."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionInputs:
    capacity_output: float
    required_input_per_unit: float
    available_input: float


def constrained_output(inputs: ProductionInputs) -> float:
    """Return realized output under a single binding input constraint."""
    if inputs.required_input_per_unit <= 0:
        raise ValueError("required_input_per_unit must be positive")
    input_limited_output = inputs.available_input / inputs.required_input_per_unit
    return max(0.0, min(inputs.capacity_output, input_limited_output))

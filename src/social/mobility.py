"""Social mobility transition helpers."""

from __future__ import annotations

import math


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def upward_mobility_probability(
    beta0: float,
    edu_access: float,
    health: float,
    formal_jobs: float,
    closure: float,
    discrimination: float,
    beta1: float,
    beta2: float,
    beta3: float,
    beta4: float,
    beta5: float,
) -> float:
    score = (
        beta0
        + beta1 * edu_access
        + beta2 * health
        + beta3 * formal_jobs
        - beta4 * closure
        - beta5 * discrimination
    )
    return sigmoid(score)


def decile_transition(population: float, up_prob: float, down_prob: float) -> tuple[float, float, float]:
    """Return stay, upward, downward flow counts."""
    up = max(0.0, population * up_prob)
    down = max(0.0, population * down_prob)
    stay = max(0.0, population - up - down)
    return stay, up, down

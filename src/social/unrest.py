"""Collective action and unrest probability helpers."""

from __future__ import annotations

import math


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def mobilization_index(grievance: float, network: float, elite_split: float, fear: float, m1: float, m2: float, m3: float, m4: float) -> float:
    return m1 * grievance + m2 * network + m3 * elite_split - m4 * fear


def protest_probability(mobilization: float, threshold: float) -> float:
    return sigmoid(mobilization - threshold)


def unrest_risk(
    theta0: float,
    needs_gap: float,
    inflation: float,
    unemployment: float,
    inequality: float,
    legitimacy: float,
    capacity: float,
    repression: float,
    theta1: float,
    theta2: float,
    theta3: float,
    theta4: float,
    theta5: float,
    theta6: float,
    theta7: float,
) -> float:
    value = (
        theta0
        + theta1 * needs_gap
        + theta2 * inflation
        + theta3 * unemployment
        + theta4 * inequality
        - theta5 * legitimacy
        - theta6 * capacity
        + theta7 * repression
    )
    return min(100.0, max(0.0, value))

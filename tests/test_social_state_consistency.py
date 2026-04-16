from __future__ import annotations

from src.social.cohorts import next_population, population_residual
from src.social.mobility import decile_transition, upward_mobility_probability
from src.social.trust_legitimacy import next_legitimacy, next_trust
from src.social.unrest import mobilization_index, protest_probability, unrest_risk


def test_population_conservation_residual() -> None:
    before = 1000.0
    births = 12.0
    deaths = 8.0
    migration = -2.0

    after = next_population(before, births, deaths, migration)
    residual = population_residual(before, after, births, deaths, migration)

    assert after == 1002.0
    assert residual == 0.0


def test_mobility_probability_bounds() -> None:
    prob = upward_mobility_probability(
        beta0=0.0,
        edu_access=0.6,
        health=0.7,
        formal_jobs=0.5,
        closure=0.2,
        discrimination=0.1,
        beta1=0.8,
        beta2=0.6,
        beta3=0.7,
        beta4=0.5,
        beta5=0.4,
    )
    assert 0.0 < prob < 1.0


def test_decile_transition_mass_balance() -> None:
    stay, up, down = decile_transition(population=100.0, up_prob=0.1, down_prob=0.05)
    assert round(stay + up + down, 6) == 100.0


def test_trust_and_legitimacy_clamped() -> None:
    leg = next_legitimacy(
        current=95.0,
        service_performance=10.0,
        real_income=5.0,
        corruption=0.0,
        repression_excess=0.0,
        fairness=5.0,
        l1=0.2,
        l2=0.2,
        l3=0.1,
        l4=0.1,
        l5=0.2,
    )
    trust = next_trust(
        current=5.0,
        legitimacy=leg,
        info_quality=2.0,
        polarization=80.0,
        inequality_shock=10.0,
        z1=0.01,
        z2=0.2,
        z3=0.05,
        z4=0.05,
    )

    assert 0.0 <= leg <= 100.0
    assert 0.0 <= trust <= 100.0


def test_unrest_and_protest_probability() -> None:
    mobil = mobilization_index(
        grievance=60.0,
        network=40.0,
        elite_split=30.0,
        fear=20.0,
        m1=0.4,
        m2=0.3,
        m3=0.2,
        m4=0.3,
    )
    prob = protest_probability(mobilization=mobil, threshold=10.0)
    unrest = unrest_risk(
        theta0=20.0,
        needs_gap=0.2,
        inflation=0.05,
        unemployment=0.1,
        inequality=55.0,
        legitimacy=40.0,
        capacity=45.0,
        repression=20.0,
        theta1=20.0,
        theta2=40.0,
        theta3=30.0,
        theta4=0.2,
        theta5=0.3,
        theta6=0.2,
        theta7=0.1,
    )

    assert 0.0 < prob < 1.0
    assert 0.0 <= unrest <= 100.0

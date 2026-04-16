"""Tests for the policy system, ideological traditions, and consequence engine."""

from __future__ import annotations

import pytest

from src.core.policy_system import (
    DEFAULT_ACTIVE_POLICIES,
    add_to_graveyard,
    bandwidth_cost,
    bandwidth_recharge,
    decay_graveyard,
    initial_ministry_budgets,
    make_policy,
    realized_value,
    update_active_policies,
    update_credibility,
    update_ministry_budgets,
    update_policy_vitality,
)
from src.core.ideology_traditions import (
    TRADITIONS,
    bandwidth_discount_for_action,
    dominant_tradition,
    initial_tradition_influence,
    update_tradition_influence,
)
from src.core.consequence_engine import (
    apply_consequence_deltas,
    apply_matured_consequences,
    queue_consequences,
)


# ---------------------------------------------------------------------------
# policy_system: bandwidth
# ---------------------------------------------------------------------------

class TestBandwidth:
    def test_recharge_range(self):
        low  = bandwidth_recharge(0.0, 0.0)
        high = bandwidth_recharge(100.0, 1.0)
        assert 20 <= low <= 60
        assert 20 <= high <= 60

    def test_cost_scaled_by_iq(self):
        cheap = bandwidth_cost("adjust_tax_rate", institutional_quality=1.0)
        expensive = bandwidth_cost("adjust_tax_rate", institutional_quality=0.0)
        assert cheap < expensive

    def test_cost_minimum_one(self):
        assert bandwidth_cost("adjust_tax_rate", institutional_quality=1.0) >= 1

    def test_unknown_action_defaults(self):
        assert bandwidth_cost("totally_unknown_action", 0.5) >= 1


# ---------------------------------------------------------------------------
# policy_system: realized_value
# ---------------------------------------------------------------------------

class TestRealizedValue:
    def test_perfect_state_near_formal(self):
        rv = realized_value(1.0, bureaucratic_reach=1.0, legitimacy_norm=1.0,
                            elite_capture=0.0, vitality=100.0)
        assert rv > 0.8

    def test_zero_vitality_collapses_output(self):
        rv = realized_value(1.0, bureaucratic_reach=1.0, legitimacy_norm=1.0,
                            elite_capture=0.0, vitality=0.0)
        # capacity_factor = 0.5 + 0.3 + 0.0 = 0.8 → still gets something
        # but significantly lower than full vitality
        rv_full = realized_value(1.0, 1.0, 1.0, 0.0, 100.0)
        assert rv < rv_full

    def test_high_capture_reduces_output(self):
        low_capture  = realized_value(0.8, 0.7, 0.7, 0.1, 60.0)
        high_capture = realized_value(0.8, 0.7, 0.7, 0.9, 60.0)
        assert high_capture < low_capture


# ---------------------------------------------------------------------------
# policy_system: vitality
# ---------------------------------------------------------------------------

class TestVitality:
    def test_funded_vitality_increases(self):
        v0 = 50.0
        v1 = update_policy_vitality(v0, upkeep_funded=True,
                                    institutional_quality=0.7, legitimacy=0.6)
        assert v1 > v0

    def test_unfunded_vitality_decays(self):
        v0 = 50.0
        v1 = update_policy_vitality(v0, upkeep_funded=False,
                                    institutional_quality=0.7, legitimacy=0.6)
        assert v1 < v0

    def test_vitality_bounded(self):
        v_high = update_policy_vitality(99.0, True, 1.0, 1.0)
        v_low  = update_policy_vitality(0.5, False, 0.0, 0.0)
        assert 0.0 <= v_low <= 100.0
        assert 0.0 <= v_high <= 100.0


# ---------------------------------------------------------------------------
# policy_system: update_active_policies
# ---------------------------------------------------------------------------

class TestUpdateActivePolicies:
    def _budgets(self) -> dict[str, float]:
        return initial_ministry_budgets(0.20, 1_000_000.0)

    def test_stable_policies_survive(self):
        policies = [make_policy("test_pol", "fiscal", 0.5, upkeep_cost=0.001)]
        # Seed vitality high so they won't collapse immediately
        policies[0]["vitality"] = 80.0
        updated, collapsed = update_active_policies(
            policies, self._budgets(), 0.7, 0.6, 0.6, 0.2
        )
        assert len(collapsed) == 0
        assert len(updated) == 1

    def test_zero_vitality_collapses(self):
        pol = make_policy("dying_pol", "fiscal", 0.5, upkeep_cost=0.001)
        pol["vitality"] = 0.01  # effectively zero after one decay tick
        # Force underfunded
        _, collapsed = update_active_policies(
            [pol], {"finance": 0.0}, 0.0, 0.1, 0.1, 0.9
        )
        assert len(collapsed) == 1

    def test_age_ticks_increments(self):
        pol = make_policy("aging_pol", "fiscal", 0.5, upkeep_cost=0.0)
        pol["vitality"] = 80.0
        updated, _ = update_active_policies([pol], self._budgets(), 0.7, 0.6, 0.6, 0.2)
        assert updated[0]["age_ticks"] == 1


# ---------------------------------------------------------------------------
# policy_system: graveyard
# ---------------------------------------------------------------------------

class TestGraveyard:
    def test_add_and_decay(self):
        grave: list = []
        pol = make_policy("old_pol", "fiscal", 0.5)
        pol["age_ticks"] = 20
        grave = add_to_graveyard(grave, pol, "test_collapse", tick=5)
        assert len(grave) == 1
        assert grave[0]["grievance"] > 0.0

        grave, total = decay_graveyard(grave)
        # Grievance should have decreased by GRIEVANCE_DECAY_PER_TICK
        assert total < grave[0]["grievance"] + 1.5 + 0.01

    def test_expired_entries_removed(self):
        grave: list = []
        pol = make_policy("short_pol", "fiscal", 0.5)
        pol["age_ticks"] = 1
        grave = add_to_graveyard(grave, pol, "repeal", tick=0)
        grave[0]["scar_ticks_remaining"] = 1  # will expire next decay
        grave[0]["grievance"] = 0.0           # already zero grievance
        grave, total = decay_graveyard(grave)
        assert len(grave) == 0  # expired because scar_ticks → 0


# ---------------------------------------------------------------------------
# policy_system: credibility
# ---------------------------------------------------------------------------

class TestCredibility:
    def test_collapse_reduces_credibility(self):
        c0 = 1.0
        c1 = update_credibility(c0, n_collapsed=2, n_failed_laws=1)
        assert c1 < c0

    def test_credibility_floor(self):
        c = update_credibility(0.21, n_collapsed=100, n_failed_laws=100)
        assert c >= 0.20

    def test_credibility_ceiling(self):
        c = update_credibility(0.99, n_collapsed=0, n_failed_laws=0)
        assert c <= 1.0


# ---------------------------------------------------------------------------
# ideology_traditions
# ---------------------------------------------------------------------------

class TestIdeologyTraditions:
    def test_initial_influence_positive(self):
        inf = initial_tradition_influence(0.6, 0.3)
        assert len(inf) == 6
        assert all(v >= 5.0 for v in inf.values())
        assert all(v <= 100.0 for v in inf.values())

    def test_all_six_traditions_present(self):
        inf = initial_tradition_influence(0.5, 0.5)
        assert set(inf.keys()) == set(TRADITIONS.keys())

    def test_update_stays_in_range(self):
        inf = initial_tradition_influence(0.6, 0.3)
        prior = {"inequality": 50.0, "legitimacy": 50.0, "gdp_growth": 0.02, "crisis_active": False}
        inf2 = update_tradition_influence(inf, prior, "")
        assert all(5.0 <= v <= 100.0 for v in inf2.values())

    def test_dominant_returns_key(self):
        inf = {"a": 0.6, "b": 0.3, "c": 0.1}
        assert dominant_tradition(inf) == "a"

    def test_bandwidth_discount_applies_for_matching_family(self):
        # "industrial" is in developmental_nationalism's policy_families
        discount_multiplier = bandwidth_discount_for_action("industrial", "developmental_nationalism")
        assert discount_multiplier < 1.0

    def test_bandwidth_no_discount_for_nonmatching_family(self):
        # "fiscal" is NOT in developmental_nationalism's policy_families
        multiplier = bandwidth_discount_for_action("fiscal", "developmental_nationalism")
        assert multiplier == 1.0


# ---------------------------------------------------------------------------
# consequence_engine
# ---------------------------------------------------------------------------

class TestConsequenceEngine:
    def test_queue_consequence(self):
        pending = queue_consequences([], "test_policy", {"inequality": 2.0}, 12, 0, 0.5)
        assert len(pending) == 1
        entry = pending[0]
        assert entry["policy_name"] == "test_policy"
        assert entry["manifest_tick"] > 0

    def test_high_iq_shortens_delay(self):
        p_lo = queue_consequences([], "pol", {"x": 1.0}, 20, 0, 0.0)
        p_hi = queue_consequences([], "pol", {"x": 1.0}, 20, 0, 1.0)
        assert p_hi[0]["manifest_tick"] <= p_lo[0]["manifest_tick"]

    def test_mature_consequence_applied(self):
        pending = queue_consequences([], "pol", {"trust": 5.0}, 1, 0, 0.0)
        remaining, deltas, revealed = apply_matured_consequences(pending, current_tick=5)
        assert len(remaining) == 0
        assert "trust" in deltas
        assert len(revealed) == 1
        assert revealed[0]["policy_name"] == "pol"

    def test_unmatured_consequence_stays_pending(self):
        pending = queue_consequences([], "pol", {"trust": 5.0}, 20, 0, 0.0)
        remaining, deltas, revealed = apply_matured_consequences(pending, current_tick=1)
        assert len(remaining) == 1
        assert deltas == {}

    def test_apply_deltas_additive(self):
        state = {"trust": 40.0, "inequality": 50.0}
        deltas = {"trust": 5.0, "inequality": -2.0}
        patch = apply_consequence_deltas(state, deltas)
        assert patch["trust"] == pytest.approx(45.0)
        assert patch["inequality"] == pytest.approx(48.0)

    def test_empty_effects_not_queued(self):
        pending = queue_consequences([], "pol", {}, 10, 0, 0.5)
        assert len(pending) == 0

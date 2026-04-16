"""Factory for the default simulation engine with registered stages."""

from __future__ import annotations

from .stages import (
    apply_building_policies,
    apply_policies,
    compute_real_economy,
    run_consistency_checks,
    update_construction_queue,
    update_class_dynamics,
    update_consequence_queue,
    update_events_and_crises,
    update_expectations,
    update_ideology_traditions,
    update_laws_and_interest_groups,
    update_logistics_and_market,
    update_military_security,
    update_policy_state,
    update_prices_labor,
    update_public_external,
    update_social_political,
    update_technology,
    update_victory_failure,
    update_world_diplomacy,
)
from .scenario_loader import initial_state_from_scenario, load_scenario_file
from .tick_engine import TickEngine


def build_default_engine(seed: int) -> TickEngine:
    engine = TickEngine(base_seed=seed)
    engine.register_stage("apply_policies", apply_policies)
    engine.register_stage("update_world_diplomacy", update_world_diplomacy)
    engine.register_stage("update_construction_queue", update_construction_queue)
    engine.register_stage("update_expectations", update_expectations)
    engine.register_stage("compute_real_economy", compute_real_economy)
    engine.register_stage("update_logistics_and_market", update_logistics_and_market)
    engine.register_stage("update_prices_labor", update_prices_labor)
    engine.register_stage("update_public_external", update_public_external)
    engine.register_stage("update_laws_and_interest_groups", update_laws_and_interest_groups)
    engine.register_stage("update_technology", update_technology)
    engine.register_stage("update_military_security", update_military_security)
    engine.register_stage("update_class_dynamics", update_class_dynamics)
    engine.register_stage("update_social_political", update_social_political)
    engine.register_stage("update_events_and_crises", update_events_and_crises)
    engine.register_stage("update_victory_failure", update_victory_failure)
    engine.register_stage("apply_building_policies", apply_building_policies)
    engine.register_stage("update_policy_state", update_policy_state)
    engine.register_stage("update_ideology_traditions", update_ideology_traditions)
    engine.register_stage("update_consequence_queue", update_consequence_queue)
    engine.register_stage("run_consistency_checks", run_consistency_checks)
    return engine


def build_engine_from_scenario(seed: int, scenario_path: str) -> TickEngine:
    """Build engine and initialize state from a YAML scenario file."""
    engine = build_default_engine(seed=seed)
    scenario_data = load_scenario_file(scenario_path)
    initial_state = initial_state_from_scenario(scenario_data)
    engine.initialize(initial_state)
    return engine

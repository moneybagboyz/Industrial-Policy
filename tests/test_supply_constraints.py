from __future__ import annotations

from src.econ.inventory import next_inventory, unmet_demand
from src.econ.production import ProductionInputs, constrained_output
from src.econ.supply_allocation import proportional_allocation


def test_constrained_output_is_input_bounded() -> None:
    inputs = ProductionInputs(
        capacity_output=120.0,
        required_input_per_unit=2.0,
        available_input=180.0,
    )
    # Input supports only 90 units.
    assert constrained_output(inputs) == 90.0


def test_constrained_output_is_capacity_bounded() -> None:
    inputs = ProductionInputs(
        capacity_output=80.0,
        required_input_per_unit=2.0,
        available_input=500.0,
    )
    assert constrained_output(inputs) == 80.0


def test_inventory_and_unmet_demand() -> None:
    end_inv = next_inventory(current_inventory=10.0, production=15.0, demand=40.0)
    shortage = unmet_demand(current_inventory=10.0, production=15.0, demand=40.0)

    assert end_inv == 0.0
    assert shortage == 15.0


def test_proportional_allocation_scales_when_constrained() -> None:
    allocation = proportional_allocation(
        total_supply=60.0,
        requested={"industry_a": 60.0, "industry_b": 40.0},
    )

    assert round(allocation["industry_a"], 6) == 36.0
    assert round(allocation["industry_b"], 6) == 24.0
    assert round(sum(allocation.values()), 6) == 60.0

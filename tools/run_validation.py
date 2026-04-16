"""Validation gate runner for phase advancement."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.econ.national_accounts import (
    ExpenditureComponents,
    IncomeComponents,
    accounting_residual_ratio,
    gdp_expenditure,
    gdp_income,
)
from src.econ.sector_balances import SectorBalances, net_sector_balance
from src.social.cohorts import population_residual


def run_pytest() -> tuple[bool, str]:
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    ok = process.returncode == 0
    output = (process.stdout or "") + (process.stderr or "")
    return ok, output.strip()


def run_stress_pytest() -> tuple[bool, str]:
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/stress"],
        capture_output=True,
        text=True,
        check=False,
    )
    ok = process.returncode == 0
    output = (process.stdout or "") + (process.stderr or "")
    return ok, output.strip()


def run_validation() -> dict:
    exp = ExpenditureComponents(500.0, 120.0, 140.0, 90.0, 70.0)
    inc = IncomeComponents(420.0, 280.0, 60.0, 25.0, 5.0)
    ratio = accounting_residual_ratio(gdp_expenditure(exp), gdp_income(inc))

    sectors = SectorBalances(
        households=20.0,
        firms=-5.0,
        government=-10.0,
        financial_sector=2.0,
        rest_of_world=-7.0,
    )
    sector_res = net_sector_balance(sectors)

    pop_res = population_residual(
        total_before=1000.0,
        total_after=1002.0,
        births=12.0,
        deaths=8.0,
        migration_net=-2.0,
    )

    pytest_ok, pytest_output = run_pytest()
    stress_ok, stress_output = run_stress_pytest()

    gates = {
        "gdp_identity": {
            "value": ratio,
            "threshold": 0.001,
            "pass": ratio <= 0.001,
        },
        "sector_residual": {
            "value": abs(sector_res),
            "threshold": 0.000001,
            "pass": abs(sector_res) <= 0.000001,
        },
        "social_population_residual": {
            "value": abs(pop_res),
            "threshold": 0.000001,
            "pass": abs(pop_res) <= 0.000001,
        },
        "pytest": {
            "pass": pytest_ok,
            "output": pytest_output,
        },
        "stress_scenarios": {
            "pass": stress_ok,
            "output": stress_output,
        },
    }

    verdict = all(g["pass"] for g in gates.values())
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "gates": gates,
        "verdict": "pass" if verdict else "fail",
    }


if __name__ == "__main__":
    result = run_validation()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["verdict"] == "pass" else 1)

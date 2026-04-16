"""ASCII map rendering helpers for regional topology."""

from __future__ import annotations

from typing import Any


def render_region_ascii_map(state: dict[str, Any], width: int = 56, height: int = 18) -> str:
    region_state = state.get("region_state")
    if not isinstance(region_state, dict):
        return "No regional map available."

    regions = region_state.get("regions")
    if not isinstance(regions, dict) or not regions:
        return "No regional map available."

    grid = [["." for _ in range(width)] for _ in range(height)]
    legend_rows: list[str] = []

    sorted_regions = sorted(regions.items())
    for idx, (name, row) in enumerate(sorted_regions, start=1):
        if not isinstance(row, dict):
            continue
        x = int(float(row.get("coord_x", 50.0)) / 100.0 * (width - 1))
        y = int(float(row.get("coord_y", 50.0)) / 100.0 * (height - 1))
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))

        token = f"{idx % 10}"
        grid[y][x] = token
        neighbors = row.get("neighbors", [])
        n_count = len(neighbors) if isinstance(neighbors, list) else 0
        legend_rows.append(f"{token}:{name} ({int(float(row.get('coord_x', 0.0)))},{int(float(row.get('coord_y', 0.0)))}) n={n_count}")

    map_lines = ["".join(r) for r in grid]
    legend = "  ".join(legend_rows[:8])
    if len(legend_rows) > 8:
        legend += "  ..."
    return "\n".join(map_lines + ["", "Legend: " + legend])

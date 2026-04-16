from __future__ import annotations

from src.ui.table_dashboard import render_table


def test_render_table_contains_headers_and_rows() -> None:
    table = render_table("Example", [("price", "100.0"), ("wage", "1000.0")])
    assert "Example" in table
    assert "Metric" in table
    assert "price" in table
    assert "wage" in table
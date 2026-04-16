"""ASCII table rendering helpers for terminal dashboard views."""

from __future__ import annotations


def render_table(title: str, rows: list[tuple[str, object]]) -> str:
    key_width = max([len("Metric")] + [len(str(key)) for key, _ in rows])
    value_width = max([len("Value")] + [len(str(value)) for _, value in rows])
    border = f"+-{'-' * key_width}-+-{'-' * value_width}-+"
    lines = [title, border, f"| {'Metric'.ljust(key_width)} | {'Value'.ljust(value_width)} |", border]
    for key, value in rows:
        lines.append(f"| {str(key).ljust(key_width)} | {str(value).ljust(value_width)} |")
    lines.append(border)
    return "\n".join(lines)


def render_matrix_table(title: str, headers: list[str], rows: list[list[object]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(str(value)))

    border = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    header_line = "| " + " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers)) + " |"

    lines = [title, border, header_line, border]
    for row in rows:
        lines.append("| " + " | ".join(str(value).ljust(widths[idx]) for idx, value in enumerate(row)) + " |")
    lines.append(border)
    return "\n".join(lines)
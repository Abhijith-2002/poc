"""
agent/tools_local.py
Local auxiliary tools for parameter binding, SQL safety guarding,
Markdown table formatting with PII redaction, and chart visualization.
"""

import os
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
import re
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tabulate import tabulate

from agent.guardrails import (
    check_bytes_limit,
    mask_tabular_data,
    validate_query_guardrails,
)


def bind_parameters(sql_template: str, parameters: Optional[Dict[str, Any]] = None, project: str = "loyalty_project", dataset: str = "loyalty_poc") -> str:
    """
    Substitutes project/dataset anchors and @param placeholders with safely escaped literals.
    """
    sql = sql_template.replace("${PROJECT}.${DATASET}", f"{project}.{dataset}")
    sql = sql.replace("${PROJECT}", project)
    sql = sql.replace("${DATASET}", dataset)

    if not parameters:
        return sql

    for param_name, param_val in parameters.items():
        placeholder = f"@{param_name}"
        if param_val is None:
            literal = "NULL"
        elif isinstance(param_val, str):
            escaped = param_val.replace("'", "''")
            literal = f"'{escaped}'"
        elif isinstance(param_val, (int, float)):
            literal = str(param_val)
        elif isinstance(param_val, bool):
            literal = "TRUE" if param_val else "FALSE"
        elif isinstance(param_val, list):
            items_str = ", ".join(f"'{str(x).replace('\'', '\'\'')}'" if isinstance(x, str) else str(x) for x in param_val)
            literal = f"({items_str})"
        else:
            literal = f"'{str(param_val)}'"

        # Replace using word boundary
        pattern = re.compile(rf"{re.escape(placeholder)}\b")
        sql = pattern.sub(literal, sql)

    return sql


def sql_guard(sql: str) -> Dict[str, Any]:
    """Local tool to validate SQL syntax and read-only safety before execution."""
    return validate_query_guardrails(sql)


def render_table(data: List[Dict[str, Any]], columns: Optional[List[str]] = None, show_pii: bool = False, limit: int = 25) -> str:
    """
    Formats tabular dictionary records into a Markdown table with PII masking.
    """
    if not data:
        return "*(Empty result set)*"

    # Redact PII
    masked = mask_tabular_data(data, show_pii=show_pii)
    
    # Restrict columns if provided
    display_rows = []
    headers = columns if columns else list(masked[0].keys())

    for r in masked[:limit]:
        row_dict = {col: r.get(col, "") for col in headers}
        display_rows.append(row_dict)

    df = pd.DataFrame(display_rows)
    table_md = tabulate(df, headers="keys", tablefmt="github", showindex=False)
    
    if len(data) > limit:
        table_md += f"\n\n*(Displaying top {limit} of {len(data):,} total rows)*"
        
    return table_md


def render_chart(
    data: List[Dict[str, Any]],
    chart_type: str,
    title: str,
    output_path: str,
    x_col: Optional[str] = None,
    y_col: Optional[str] = None,
    **kwargs,
) -> str:
    """
    Renders analytical charts (pie, grouped_bar) to PNG files in outputs/.
    
    Args:
        data: List of record dictionaries.
        chart_type: 'pie' or 'grouped_bar'.
        title: Title of chart.
        output_path: Destination file path (e.g. 'outputs/uc2a_visit_spend_pie.png').
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.close("all")

    if chart_type == "pie":
        # UC2a: Pie Chart for Average Visit Spend by Tier
        labels = [r.get(x_col or "tier_name", "") for r in data]
        values = [float(r.get(y_col or "avg_visit_spend", 0.0)) for r in data]

        fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(aspect="equal"))
        colors = ["#CD7F32", "#C0C0C0", "#FFD700", "#E5E4E2"]  # Bronze, Silver, Gold, Platinum

        # Match color length
        if len(values) <= len(colors):
            slice_colors = colors[:len(values)]
        else:
            slice_colors = plt.cm.Set3(np.linspace(0, 1, len(values)))

        def func(pct, allvals):
            absolute = pct / 100. * sum(allvals)
            return f"${absolute:.2f}\n({pct:.1f}%)"

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct=lambda pct: func(pct, values),
            startangle=140,
            colors=slice_colors,
            textprops=dict(color="black", weight="bold"),
            wedgeprops=dict(width=0.8, edgecolor="white", linewidth=2),
        )

        ax.set_title(title, fontsize=14, weight="bold", pad=20)
        plt.tight_layout()
        plt.savefig(output_path, dpi=200)
        plt.close(fig)
        return f"Pie chart successfully saved to {output_path}"

    elif chart_type == "grouped_bar":
        # UC5: Grouped bar chart comparing Last Year vs This Year with green/red variance highlighting
        labels = [r.get("tier_name", "") for r in data]
        last_year_vals = [float(r.get("last_year_spend", 0.0)) for r in data]
        this_year_vals = [float(r.get("this_year_spend", 0.0)) for r in data]
        pct_changes = [float(r.get("pct_change", 0.0)) for r in data]

        x = np.arange(len(labels))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))

        # Last year bars (neutral slate gray)
        rects1 = ax.bar(x - width/2, last_year_vals, width, label="Last Year (Same Period)", color="#708090", edgecolor="white")

        # This year bars colored green when up, red when down
        this_year_colors = ["#2E7D32" if val >= ly else "#D32F2F" for val, ly in zip(this_year_vals, last_year_vals)]
        rects2 = ax.bar(x + width/2, this_year_vals, width, label="This Year (Calendar YTD)", color=this_year_colors, edgecolor="white")

        ax.set_ylabel("Total Spend ($ AUD)", fontsize=12, weight="bold")
        ax.set_title(title, fontsize=14, weight="bold", pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=11, weight="bold")
        ax.legend(loc="upper right", frameon=True)
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        # Format y-axis currency with millions
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"${y*1e-6:.1f}M"))

        # Add percentage labels above This Year bars
        for i, (rect, pct) in enumerate(zip(rects2, pct_changes)):
            height = rect.get_height()
            color = "#2E7D32" if pct >= 0 else "#D32F2F"
            sign = "+" if pct >= 0 else ""
            ax.annotate(
                f"{sign}{pct:.1f}%",
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                weight="bold",
                color=color,
            )

        plt.tight_layout()
        plt.savefig(output_path, dpi=200)
        plt.close(fig)
        return f"Variance-highlighted grouped bar chart saved to {output_path}"

    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")

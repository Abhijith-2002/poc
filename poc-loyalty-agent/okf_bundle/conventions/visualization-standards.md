---
type: Convention
title: Visualization Standards
description: Graphical and chart rendering specifications for retail analytics outputs.
tags:
  - conventions
  - visualization
  - charts
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
---

# Visualization Standards

## Chart Types & Specifications
1. **Pie Chart (UC2a: Visit Spend by Tier)**:
   - Output path: `outputs/uc2a_visit_spend_pie.png`.
   - Displays percentage and dollar amount share of average visit spend across loyalty tiers.
   - Clean color palette with distinct slices for Bronze, Silver, Gold, Platinum.
2. **Grouped Bar Chart with Variance Highlighting (UC5: YoY Tier Spend)**:
   - Output path: `outputs/uc5_yoy_tier_spend.png`.
   - Side-by-side grouped bars for Last Year vs This Year (YTD) per tier.
   - **Color Rule**:
     - Green bar/fill when This Year spend is greater than Last Year (`diff > 0`).
     - Red bar/fill when This Year spend is lower than Last Year (`diff < 0`).
   - Include percentage delta annotations above each tier group (e.g. `+15.2%`, `-8.4%`).


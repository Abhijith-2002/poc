---
type: Routing Matrix
title: Question Routing Matrix
description: Maps natural language queries, user intents, and synonyms to canonical OKF use cases.
tags:
  - routing
  - intents
  - disambiguation
status: stable
generated:
  by: okf-authoring/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/use-cases/index.md"
---

# Question Routing Matrix

This matrix maps natural language user inquiries, trigger keywords, and conversational intents to canonical OKF use cases in `/use-cases/`.

## Master Routing Table

| Use Case ID | Concept File Path | Primary Trigger Phrases / Synonyms | Required Parameters | Chained Parent | Output Format |
|---|---|---|---|---|---|
| **UC1** | [/use-cases/uc01-top-members-doncaster-email.md](/use-cases/uc01-top-members-doncaster-email.md) | "Top 100 members by spend at Doncaster", "Doncaster email contactable", "Highest spenders Doncaster past year", "Doncaster VIP campaign members" | `store_name='Doncaster'` | None | Table (100 rows) |
| **UC1a** | [/use-cases/uc01a-rank-by-purchases.md](/use-cases/uc01a-rank-by-purchases.md) | "Of those 100, rank by number of purchases", "Rank them by purchase count", "Order Doncaster top spenders by transaction count" | Inherited from UC1 | `UC1` | Table (100 rows) |
| **UC2** | [/use-cases/uc02-avg-visit-spend-by-tier.md](/use-cases/uc02-avg-visit-spend-by-tier.md) | "Average visit spend per member broken down by tier", "Spend per visit by tier past 3 months", "Tier basket size last 90 days" | `window_months=3` | None | Table (4 rows) |
| **UC2a** | [/use-cases/uc02a-pie-graph-visit-spend.md](/use-cases/uc02a-pie-graph-visit-spend.md) | "Provide a pie graph of UC2", "Pie chart of visit spend by tier", "Show that as a pie graph", "Plot visit spend" | Inherited from UC2 | `UC2` | Pie Chart (`.png`) |
| **UC3** | [/use-cases/uc03-age-band-store-vs-online.md](/use-cases/uc03-age-band-store-vs-online.md) | "Which age band is more likely to shop in store vs online", "Store vs online shopping by age group", "Digital vs physical store preference by demographics past 6 months" | `window_months=6` | None | Table (6 rows) |
| **UC3a** | [/use-cases/uc03a-top-age-band-store-visits.md](/use-cases/uc03a-top-age-band-store-visits.md) | "For the top age band on average how many store visits per member", "Average store visits for that top age group", "Store visit frequency for top demographic" | Inherited from UC3 (`target_age_band`) | `UC3` | Metrics Summary |
| **UC4** | [/use-cases/uc04-new-joiners-high-frequency-spend.md](/use-cases/uc04-new-joiners-high-frequency-spend.md) | "Top 100 members who joined in last 6 months with high visit frequency", "New joiners frequent shoppers ranked by spend", "Best new customers past 6 months" | `min_visits=5` | None | Table (100 rows) |
| **UC4a** | [/use-cases/uc04a-online-vs-store-spend-split.md](/use-cases/uc04a-online-vs-store-spend-split.md) | "Of those 100 show the break-up of online vs in-store spend", "Online vs store split for those top new joiners", "Channel breakdown for those 100" | Inherited from UC4 | `UC4` | Table (100 rows) |
| **UC5** | [/use-cases/uc05-spend-by-tier-yoy-comparison.md](/use-cases/uc05-spend-by-tier-yoy-comparison.md) | "Chart spend by member tier this year vs last year", "Highlight green when up red when down", "YoY spend comparison by loyalty tier", "YTD tier spend variance" | `ytd_mode='calendar_ytd'` | None | Grouped Bar (`.png`) |
| **UC6** | [/use-cases/uc06-demographic-breakdown-spent-vs-not-spent.md](/use-cases/uc06-demographic-breakdown-spent-vs-not-spent.md) | "Demographic breakdown of members who have NOT spent in the last 6 months vs those who have", "Dormant vs active members by age, gender, state", "Lapsed customer demographics" | `window_months=6` | None | Table |
| **UC7** | [/use-cases/uc07-staff-high-frequency-transactions.md](/use-cases/uc07-staff-high-frequency-transactions.md) | "Rank top 100 members with staff_indicator = Y by high transaction frequency", "Team members multiple transactions per day", "Staff purchase frequency last month" | `window_days=30` | None | Table (100 rows) |
| **UC8** | [/use-cases/uc08-gold-inactive-points.md](/use-cases/uc08-gold-inactive-points.md) | "Number of members in Gold tier with points >= {xx} who haven't transacted in past 2 months", "Inactive Gold members with points threshold", "Dormant Gold high points count" | `points_threshold` (REQUIRED) | None | Single Count |

## Disambiguation Rules
1. **Chained Follow-Up Queries**:
   - If user asks "Of those 100..." immediately following UC1, route directly to `UC1a`.
   - If user asks "Provide a pie chart..." immediately following UC2, route directly to `UC2a`.
   - If user asks "For the top age band..." immediately following UC3, route directly to `UC3a`.
   - If user asks "Of those 100 show the break-up..." immediately following UC4, route directly to `UC4a`.
2. **Missing Parameters (UC8)**:
   - If the user asks for inactive Gold members with points (UC8) without specifying a numerical points threshold (e.g. "How many Gold members with high points haven't transacted in 2 months?"), the agent MUST halt and prompt the user:
     *"Please specify the minimum points balance threshold (e.g., 2000, 3000, 5000) to evaluate."*
3. **Out-of-Scope Queries**:
   - If a user asks a question not covered by any curated use case (e.g., "What is our best-selling shoe model?"), the agent must state that no curated use case exists, and fall back to ad-hoc SQL only after consulting table and metric schemas, explicitly flagging the query as non-curated.

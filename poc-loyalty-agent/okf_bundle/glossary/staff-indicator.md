---
type: Business Term
title: Staff Indicator
description: Flag identifying whether a loyalty member is an internal retail employee/team member.
tags:
  - loyalty
  - hr
  - staff
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_member.md"
---

# Staff Indicator

## Definition
`dim_member.staff_indicator` flags internal staff members:
- `'Y'`: Confirmed team member / staff.
- `'N'`: Regular retail customer.

## Business Context & Rules
- Staff members receive corporate staff discounts and earn loyalty points on eligible purchases.
- Staff often exhibit unique purchase behaviors, such as multiple small purchases on the same shift/day (e.g. coffee, lunch snacks, register test purchases).
- Relevant for [UC7: Top Staff by Transaction Frequency](/use-cases/uc07-staff-high-frequency-transactions.md).


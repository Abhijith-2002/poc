---
type: Business Term
title: Loyalty Tier
description: Customer membership tier indicating engagement level, spend threshold, and benefits.
tags:
  - loyalty
  - tiers
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_member_tier.md"
  - "/datasets/loyalty_poc/tables/dim_member.md"
---

# Loyalty Tier

## Definition
The loyalty programme consists of 4 ascending tiers defined in `dim_member_tier`:
1. **Bronze (`tier_id = 1`)**: Entry-level tier ($0 annual spend threshold). Base points multiplier (1.0x).
2. **Silver (`tier_id = 2`)**: Regular active members ($1,000 threshold). 1.25x points multiplier, free standard shipping.
3. **Gold (`tier_id = 3`)**: High-value members ($3,000 threshold). 1.5x points multiplier, VIP invitations, priority service.
4. **Platinum (`tier_id = 4`)**: Top-tier elite spenders ($7,500 threshold). 2.0x points multiplier, dedicated concierge.

## Related Analytical Use Cases
- [UC2: Average Visit Spend by Tier](/use-cases/uc02-avg-visit-spend-by-tier.md)
- [UC5: Spend by Member Tier This Year vs Last Year](/use-cases/uc05-spend-by-tier-yoy-comparison.md)
- [UC8: Inactive Gold Members with High Points](/use-cases/uc08-gold-inactive-points.md)


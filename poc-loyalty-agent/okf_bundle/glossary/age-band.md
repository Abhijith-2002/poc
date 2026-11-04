---
type: Business Term
title: Age Band
description: Standard demographic customer age segmentation brackets.
tags:
  - demographics
  - segmentation
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_member.md"
---

# Age Band

## Definition
Demographic age segmentation in `dim_member.age_band`.

## Permitted Values
- `'18-24'`: Young adult / Gen Z cohort. Predominantly online shoppers.
- `'25-34'`: Early career / Millennial cohort. High online propensity.
- `'35-44'`: Established family / Gen X cohort. Balanced omnichannel shoppers.
- `'45-54'`: Mature family cohort. Moderate store preference.
- `'55-64'`: Mature / Boomer cohort. Predominantly in-store shoppers.
- `'65+'`: Senior cohort. Highest store visit propensity.

## Analytical Notes
For UC3, channel preference (in-store vs online) must be evaluated across these 6 distinct bands over the last 6 months.


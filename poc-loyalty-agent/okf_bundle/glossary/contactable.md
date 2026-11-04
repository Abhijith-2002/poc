---
type: Business Term
title: Contactable Member
description: A loyalty member who is legally eligible to receive marketing email communications.
tags:
  - loyalty
  - privacy
  - marketing
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
sources:
  - "/datasets/loyalty_poc/tables/dim_member.md"
---

# Contactable Member

## Definition
A loyalty member is classified as **contactable by email** if they possess a valid, non-empty email address and have explicitly opted in to receive electronic direct mail (eDM).

## Logic in Schema
In `dim_member`:
- Column `contactable_by_email` is a precomputed `BOOLEAN`:
  ```sql
  email IS NOT NULL AND TRIM(email) != '' AND email_opt_in = TRUE
  ```
- Filtering rule: For marketing campaign targeting (e.g., UC1), always apply:
  ```sql
  WHERE contactable_by_email = TRUE
  ```

## Privacy & Protection
Customer email addresses and full names are classified as PII. In analytical summaries, emails must be masked unless `SHOW_PII=true` is enabled. See [PII Masking Conventions](/conventions/pii-masking.md).


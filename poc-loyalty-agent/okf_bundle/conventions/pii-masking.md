---
type: Convention
title: PII Masking Standards
description: Redaction and obfuscation rules for customer personally identifiable information.
tags:
  - conventions
  - security
  - privacy
status: stable
generated:
  by: okf-generator/1.0.0
  at: "2026-11-03T00:00:00Z"
verified: true
---

# PII Masking Standards

## Policy
Customer email addresses and full names are sensitive data elements and must not be exposed in plaintext in conversational UI responses or default logs.

## Obfuscation Rules
- **Email Masking**: Mask email usernames and domain stems:
  - Example: `emma.smith124@gmail.com` -> `e***h@g***l.com`.
- **Name Masking**: Display first initial and last initial:
  - Example: `Emma Smith` -> `E*** S***`.
- **Unmasked Override (`SHOW_PII=true`)**:
  - Plaintext PII is revealed ONLY when the environment variable `SHOW_PII=true` is explicitly set by authorized administrators.
  - For operational campaign exports (such as UC1 Doncaster email campaign), the agent saves an unmasked CSV to `outputs/` when permitted, and prints only a masked preview in chat.


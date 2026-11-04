# Open Knowledge Format (OKF) v0.2 Implementation Notes

These notes summarize the rules, constraints, and conventions from the official Open Knowledge Format (OKF) v0.2 specification (`GoogleCloudPlatform/open-knowledge-format` / `knowledge-catalog`) followed in the `poc-loyalty-agent` project.

---

## 1. Bundle Structure & Concept Identity
- **Bundle Definition**: An OKF bundle is a directory tree of UTF-8 encoded Markdown (`.md`) files.
- **Concept Identity**: Each non-reserved file represents exactly one **concept**.
  - A concept's canonical ID is its relative file path from the bundle root minus the `.md` extension.
  - Example: `datasets/loyalty_poc/tables/dim_member.md` has concept ID `datasets/loyalty_poc/tables/dim_member`.
- **Reserved Files**:
  - `index.md`: Used for directory navigation and progressive discovery. Only the bundle-root `index.md` may contain YAML frontmatter, where it declares `okf_version: "0.2"`. All subfolder `index.md` files must NOT contain frontmatter.
  - `log.md`: Chronological log of bundle updates. Log entries use plain ISO date headings (`# YYYY-MM-DD` or `## YYYY-MM-DD`) with bulleted change descriptions.

---

## 2. YAML Frontmatter Requirements
- Every concept file MUST begin with parseable YAML frontmatter bounded by `---`.
- **Mandatory Field**:
  - `type`: Non-empty string. In OKF, `type` is an **open vocabulary**. Consumers must tolerate unknown keys and unknown types gracefully.
- **Well-Known Core Frontmatter Keys (v0.2)**:
  - `type`: String (e.g., `BigQuery Table`, `BigQuery View`, `Business Term`, `Metric`, `Use Case`, `Attested Computation`).
  - `resource`: URI or locator of the physical asset (e.g., `bigquery://project/dataset/table`).
  - `title`: Short human-readable title.
  - `description`: One- or two-sentence summary of the concept's purpose.
  - `tags`: List of strings for topical indexing and search.
  - `status`: Lifecycle state (`draft`, `stable`, `deprecated`).
  - `generated`: Mapping with `{by: string, at: ISO8601 UTC timestamp}`.
  - `verified`: Boolean or verification record indicating review status.
  - `stale_after`: ISO8601 UTC timestamp after which the concept must be re-validated.
  - `sources`: List of upstream source references or dataset lineage paths.
  - `usage_window`: Temporal validity bounds if applicable.

---

## 3. Cross-Linking & Navigation
- Concepts reference other concepts using standard Markdown links:
  `[Target Concept Title](/path/to/concept.md)` or relative links `[Target Concept Title](../path/to/concept.md)`.
- Bundle-relative absolute paths (starting with `/`) are preferred for stability against directory moves.
- Root `index.md` and subfolder `index.md` files act as tables of contents and progressive-disclosure roadmaps for AI agents.

---

## 4. Use-Case Concept Contract (§10 Attested Computation & Extended Use Case)
- In OKF v0.2, §10 introduces **Attested Computation** to bind a deterministic, sanctioned computation contract (with `runtime`, `parameters`, `executor`, `attester`) rather than having LLMs improvise arbitrary logic.
- For our loyalty analytics agent, each retail use case (UC1 through UC8, plus variants 1a, 2a, 3a, 4a) is an analytical use-case contract.
- To provide rich business context, parameter binding, canonical SQL templates, visualization instructions, and validation rules in a cohesive structure:
  - We use `type: Use Case` (or `type: Attested Computation`) with structured frontmatter extensions:
    - `use_case_id`: e.g., `UC1`, `UC1a`, `UC2`, etc.
    - `parent_use_case`: Concept ID of parent (for chained follow-ups: 1a, 2a, 3a, 4a).
    - `runtime`: `bigquery`
    - `parameters`: List of `{name, type, default, required, description}`.
    - `inputs_from_parent`: List of parameter/column names inherited from parent query.
    - `output_columns`: List of expected column names and types.
    - `visualization`: Visualization specification (`none`, `pie`, `grouped_bar`, etc.).
    - `validation`: Sanity assertions (row counts, non-empty checks, cost limits).
- **Body Structure (Strict Section Order)**:
  1. `## 1. Intent & Example Questions`
  2. `## 2. Parameters & Defaults`
  3. `## 3. Business Rules & Definitions` (linking to `/glossary/` and `/metrics/`)
  4. `## 4. Canonical BigQuery SQL Template` (in ````sql fence with `@param` placeholders and `${PROJECT}.${DATASET}`)
  5. `## 5. Chained / Follow-Up Variants`
  6. `## 6. Output Format & Visualization Specification`
  7. `## 7. Edge Cases, Pitfalls & Interpretation Notes`

---

## 5. Routing & Progressive Discovery
- `routing/question-routing.md`: Contains a deterministic routing table mapping natural-language trigger phrases and user intents to canonical `use_case_id`s and concept paths.
- The orchestrator and `okf-navigator` sub-agent consult `routing/question-routing.md` first to resolve the user's intent to an exact concept path before fetching specific concepts from GCS.

---

## 6. Conformance & Validation Rules
The bundle validator (`scripts/validate_okf.py`) enforces:
1. Every `.md` file (except non-root `index.md` and `log.md`) has parseable YAML frontmatter.
2. Frontmatter contains non-empty `type`.
3. Root `index.md` contains frontmatter with `okf_version: "0.2"`.
4. Non-root `index.md` files have NO frontmatter.
5. All relative Markdown links resolve to valid existing files within the bundle.
6. Every use-case concept has a valid SQL block with valid syntax and parameter placeholders.
7. One-to-one mapping: every defined use case is linked in `use-cases/index.md` and `routing/question-routing.md`.


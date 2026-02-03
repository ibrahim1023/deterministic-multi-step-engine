ReasoningState Schema

Purpose

- Shared, typed, mutable state carried across deterministic steps.
- All mutations must be explicit and validated.

Schema (logical)
ReasoningState

- version: string (required, semver)
- problem: ProblemSpec (required, original input)
- step_index: integer (required, starts at 0)
- status: string (required, enum: pending | running | failed | completed)
- artifacts: object (optional, step-produced data)
  - normalized: object (optional)
  - decomposition: object (optional)
  - evidence: list[object] (optional)
  - computation: object (optional)
  - verification: object (optional)
  - synthesis: object (optional)
  - audit: object (optional)
    - report: object (optional)
      - inputs: object (required)
        - prompt_length: integer
        - has_constraints: boolean
        - constraint_count: integer
      - steps: object (required)
        - step_index: integer
        - artifact_keys: list[string]
        - artifact_count: integer
      - verification: object (required)
        - status: string
        - paths: list[object] (optional)
          - name: string
          - status: string
      - timestamps: object (required)
        - created_at: string
        - updated_at: string
      - notes: list[string] (optional)
- assumptions: list[string] (optional, defaults to empty)
- constraints: list[string] (optional, defaults to empty)
- errors: list[object] (optional, defaults to empty)
  - code: string
  - message: string
  - step: string (optional)
- metadata: object (optional)
  - trace_id: string (required once execution starts)
  - policy_profile: string (optional)
  - model_profile: string (optional)
  - created_at: string (required, ISO-8601 UTC timestamp)
  - updated_at: string (required, ISO-8601 UTC timestamp)

Mutation Rules

- All mutations occur through step results; direct edits are disallowed.
- step_index increments by 1 per executed step.
- status transitions are deterministic:
  - pending -> running -> completed
  - pending -> running -> failed
- errors append-only; do not remove prior errors.
- artifacts are append-only per step; do not overwrite prior step outputs.
- updated_at must change on every mutation.

Validation Rules

- version must be valid semver.
- step_index must be >= 0 and strictly monotonic.
- status must be one of the allowed enum values.
- assumptions and constraints must be strings with no empty items.
- errors must include code and message.

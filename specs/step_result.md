StepResult Schema

Purpose

- Canonical output of a step, validated before state mutation.
- Drives deterministic transitions and trace logging.

Schema (logical)
StepResult

- version: string (required, semver)
- step: string (required, step name)
- status: string (required, enum: success | failed | skipped)
- input_hash: string (required, deterministic hash of step inputs)
- output_hash: string (required, deterministic hash of step outputs)
- started_at: string (required, ISO-8601 UTC timestamp)
- finished_at: string (required, ISO-8601 UTC timestamp)
- output: object (optional, required if status=success)
- errors: list[object] (optional, required if status=failed)
  - code: string
  - message: string
- metrics: object (optional)
  - tokens_in: integer (optional)
  - tokens_out: integer (optional)
  - latency_ms: integer (optional)

Validation Contract

- version must be valid semver.
- step must be one of the registered step names.
- status must be one of: success, failed, skipped.
- input_hash and output_hash must be present and non-empty.
- started_at must be <= finished_at.
- success requires output and must not include errors.
- failed requires errors and must not include output.
- skipped requires no output and no errors.

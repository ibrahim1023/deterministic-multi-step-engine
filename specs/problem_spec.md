ProblemSpec Schema

Versioning

- Use semantic versions: MAJOR.MINOR.PATCH.
- MAJOR: breaking changes to required fields, field meaning, or validation rules.
- MINOR: backward-compatible additions (new optional fields).
- PATCH: clarifications or documentation-only changes.
- The engine must reject inputs with a MAJOR version it does not support.
- The engine may accept higher MINOR/PATCH if all required fields are known.

Schema (logical)
ProblemSpec

- version: string (required, semver)
- id: string (required, stable request ID provided by caller)
- created_at: string (required, ISO-8601 UTC timestamp)
- inputs: object (required)
  - prompt: string (required, normalized problem statement)
  - constraints: list[string] (optional, defaults to empty)
  - context: object (optional, caller-provided context data)
  - goals: list[string] (optional, explicit targets)
- settings: object (optional)
  - evidence_required: boolean (optional, default false)
  - max_steps: integer (optional, default set by engine)
  - policy_profile: string (optional, named routing policy)
  - model_profile: string (optional, named model configuration)
- provenance: object (optional)
  - source_system: string (optional)
  - source_version: string (optional)
  - trace_parent_id: string (optional, link to prior trace)

Validation Rules

- version must be valid semver.
- id must be non-empty and stable for replay.
- created_at must be a valid ISO-8601 UTC timestamp.
- inputs.prompt must be non-empty after normalization.
- constraints and goals must be strings with no empty items.
- max_steps must be > 0 when provided.

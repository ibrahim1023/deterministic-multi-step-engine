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
  - loop: object (optional, conditional loop policy)
    - enabled: boolean (optional, default true)
    - start_step: string (required if enabled, loop start step)
    - end_step: string (required if enabled, loop end step)
    - max_iterations: integer (required if enabled, > 0)
    - stop_condition: object (required if enabled)
      - path: string (required, must start with "artifacts.")
      - operator: string (required, equals | not_equals | gt | gte | lt | lte)
      - value: string | integer | boolean (required)
      - equals: string | integer | boolean (legacy alias for operator=equals)
  - verification_paths: list[object] (optional)
    - name: string (required, path label)
    - evidence_required: boolean (optional, overrides settings.evidence_required)
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
- loop.enabled must be a boolean when provided.
- loop.start_step and loop.end_step must be non-empty strings when enabled.
- loop.max_iterations must be > 0 when enabled.
- loop.stop_condition.path must be non-empty and start with "artifacts.".
- loop.stop_condition.operator must be a supported operator when provided.
- loop.stop_condition.value must be a string, integer, or boolean.
- loop.stop_condition.equals is allowed as a legacy alias for operator=equals.
- verification_paths must be a list of objects when provided.
- verification_paths.name must be a non-empty string.
- verification_paths.evidence_required must be a boolean when provided.

Trace Format and Hashing

Purpose

- Append-only execution log for deterministic replay and audits.
- Tamper-evident chaining via record hashes.

Format

- UTF-8 text file with LF line endings.
- One JSON object per line (no blank lines).
- Records are append-only; no in-place edits.
- Each record includes a monotonic integer `index` starting at 0.

Record Types

TraceHeader (index = 0)

- type: string (required, literal "header")
- version: string (required, semver)
- trace_id: string (required, stable ID for the run)
- created_at: string (required, ISO-8601 UTC timestamp)
- engine_version: string (required, semver)
- hash_algorithm: string (required, enum: sha256)
- canonicalization: string (required, literal "json-c14n-v1")
- problem_spec_hash: string (required, hash of canonical ProblemSpec)
- initial_state_hash: string (required, hash of canonical ReasoningState)
- record_hash: string (required, hash of this record)

TraceStep

- type: string (required, literal "step")
- index: integer (required, > 0 and monotonic)
- step_index: integer (required, ReasoningState.step_index)
- result: StepResult (required)
- state_before_hash: string (required)
- state_after_hash: string (required)
- prev_hash: string (required, prior record_hash)
- record_hash: string (required, hash of this record)

TraceControl

- type: string (required, literal "control")
- index: integer (required, > 0 and monotonic)
- control_type: string (required, literal "loop")
- action: string (required, enum: repeat | stop | max_iterations_reached)
- loop_iteration: integer (required, >= 1)
- start_step: string (required)
- end_step: string (required)
- stop_condition: object (required)
  - path: string (required)
  - operator: string (required)
  - value: string | integer | boolean (required)
- state_hash: string (required, hash of state at decision time)
- prev_hash: string (required, prior record_hash)
- record_hash: string (required, hash of this record)

Canonical JSON (json-c14n-v1)

- Encode as UTF-8.
- Objects: keys sorted lexicographically (byte order), no duplicate keys.
- Arrays: preserve order.
- Numbers: no NaN/Infinity; use plain JSON numeric forms.
- No extra whitespace.

Hashing Rules

- Use SHA-256 with lowercase hex output.
- problem_spec_hash = SHA-256(canonical_json(ProblemSpec)).
- initial_state_hash = SHA-256(canonical_json(ReasoningState)).
- state_before_hash/state_after_hash use canonical ReasoningState snapshots.
- record_hash = SHA-256(canonical_json(record_without_record_hash)).
- record_without_record_hash omits the record_hash field entirely.

Determinism Rules

- All trace fields must be deterministically derived from inputs and
  deterministic step outputs.
- Timestamps must be produced by a deterministic clock (caller-provided or
  replayed), not wall-clock time.
- A replay with identical inputs must produce byte-for-byte identical traces.

Validation Rules

- index must be monotonic and start at 0 with a TraceHeader.
- prev_hash must equal the prior record_hash.
- state_after_hash must equal the hash of ReasoningState after applying result.
- result.input_hash and result.output_hash must match StepResult rules.

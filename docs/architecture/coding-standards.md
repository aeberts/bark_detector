# Coding Standards

These standards apply to all new and refactored work in the Bark Detector brownfield project. They preserve legal defensibility of evidence, maintain compatibility with legacy tooling, and enable AI-assisted development without eroding code quality.

## Guiding Principles
- **Evidence first**: Any change must preserve the integrity of violation evidence (timestamps, ordering, confidence scores).
- **Clarity over cleverness**: Favor readable, well-factored code over micro-optimisations. Sustainably extend a legacy codebase.
- **Deterministic behaviour**: Analysis pipelines must produce repeatable results even when run on different machines.
- **Incremental modernisation**: Introduce improvements without breaking compatibility with existing CLI workflows or persisted data.

## Python Style & Patterns
- Follow **PEP 8** naming, spacing, and import ordering. Use explicit relative imports inside the `bark_detector` package.
- Prefer **type hints** on public functions, dataclasses for structured data (`PersistedBarkEvent`, `Violation`, etc.), and `typing.Protocol` for injectable interfaces.
- Keep functions focused; extract helpers when violation logic, calibration, or file IO exceeds ~30-40 lines.
- Use **dataclasses** for domain entities and favour immutable fields unless mutation is required for performance.
- Avoid bare `print`; route messages through the configured `logging` instance. Debug prints may be temporarily used behind explicit feature flags or test scaffolding and should be removed before merge.
- Handle filesystem paths with `pathlib.Path` for portability.
- Guard TensorFlow or Librosa imports behind functions if they are optional in certain execution paths (e.g., unit tests) to keep startup fast.

## Project-Specific Practices
- Always execute Python entrypoints through **`uv run`** to ensure the UV-managed environment is active (e.g., `uv run python -m bark_detector`).
- Keep persisted JSON schemas backward compatible. When schema changes are unavoidable, add migration logic in `ViolationDatabase` and document it in `docs/architecture/data-models-and-schema-changes.md`.
- When touching legal analysis, align with `docs/violation_rules.md` and `docs/architecture/violation_detection_algorithm.md`. Current production code enforces a **10 second** gap for constant violations; recent analysis (2025-09-17) recommends widening this to ~33 seconds. Document any gap changes in the legal docs before or alongside implementation.
- Surface configuration defaults via `bark_detector/utils/config.py` and mirror them in `docs/configuration.md`.
- Prefer injecting dependencies (detectors, databases) for testability instead of constructing them inline.
- When integrating TensorFlow/YAMNet, ensure model downloads honour the existing caching strategy (see `README.md` troubleshooting notes).

## Testing & Quality Gates
- Extend the pytest suite under `tests/` for all behaviour changes. Integration tests live in `tests/test_integration`, legal analysis specs in `tests/test_legal`.
- Use fixture data (`tests/fixtures`) or trimmed real-world JSON samples when validating violation logic.
- Run `uv run pytest` locally before publishing changes. Target high-value coverage rather than 100%; prioritise legal analysis, report generation, and CLI orchestration paths.
- For CLI features, include smoke tests invoking the entrypoint with representative arguments.

## Documentation & Comments
- Update relevant docs (`docs/decisions.md`, architecture notes, PRDs) when behaviour or thresholds shift.
- Keep code comments concise, explaining rationale, edge cases, or legal constraints—not restating obvious code.
- Record significant design trade-offs in `docs/decisions.md` with context and date.

## Review Checklist
1. Does the change preserve or improve evidence accuracy and ordering?
2. Are type hints and dataclasses updated to reflect new fields or flows?
3. Have tests been added or updated, and do they pass via `uv run pytest`?
4. Are configuration defaults and documentation aligned with new behaviour?
5. Have legal documentation and coding standards been updated if thresholds or evidence handling changed?

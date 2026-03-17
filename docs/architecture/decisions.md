# Architecture Decisions

- Use a canonical internal domain model under `src/drts_tsn/domain`.
- Treat external case files as adapter concerns under `src/drts_tsn/adapters/external_cases`.
- Keep simulation, analysis, and comparison as separate top-level subsystems.
- Keep CLI modules as thin entrypoints over orchestration pipelines.
- Emit structured artifacts for iterative experimentation and reporting.

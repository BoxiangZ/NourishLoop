# Adding a feature

1. State the user behavior and identify the owning domain module in [modules.md](../architecture/modules.md).
2. Update request/response Pydantic schemas and route contract. Keep business logic in the module's service or pure domain code.
3. If persistence changes, add an Alembic revision and update [schema.md](../database/schema.md). Never rely on startup `create_all`.
4. Add a deterministic service or integration test that checks the user-visible behavior and ownership/state rules.
5. Run `python -m scripts.generate_api_types`; review the OpenAPI and generated TypeScript diff. Use generated types in the browser client.
6. Add UI loading, error, and empty states. Avoid implementing scoring or nutrition rules in React components.
7. Run `pytest`, `ruff`, `pnpm typecheck`, `pnpm lint`, `pnpm test:web`, and `pnpm build`; note any environment-blocked checks in the PR.
8. Update the README and relevant architecture docs when behavior or assumptions change.

For a new recommendation signal, change the engine configuration and scoring tests; do not add merchant payment values to organic ranking. For a new tracking action, preserve the distinction between planned and confirmed consumption.

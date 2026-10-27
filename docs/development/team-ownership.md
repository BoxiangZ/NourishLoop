# Suggested workstreams

These are responsibility boundaries, not assignments to named teammates. Replace role labels with GitHub usernames in `.github/CODEOWNERS` after the team agrees.

| Role | Owned paths | Interface and coordination | Definition of done |
|---|---|---|---|
| Frontend and UX | `apps/web`, browser portion of `packages/api-client` | Uses generated API types; reviews contract changes | Responsive UI, loading/error states, typecheck/lint/test/build |
| Backend and business logic | `apps/api/main.py`, identity, tracking, public schemas | Publishes OpenAPI and checks ownership/state transitions | API tests, docs and contract regeneration |
| AI and recommendation | `apps/api/modules/recommendations` | Consumes catalog candidates and identity context; publishes ranking protocol | Deterministic scoring and restriction tests |
| Data and infrastructure | catalog module, `alembic`, `scripts/seed_nourishloop.py`, Docker, CI | Coordinates migration and data shape changes with backend | Repeatable seed, migrations, local startup |
| Growth integrations | Future modules only | Coordinates sponsored presentation with recommendations and privacy | Explicit policy and tests before release |

Cross-boundary schema changes need reviewers from both the producing and consuming workstreams. The suggested CODEOWNERS file intentionally uses a general team placeholder until real handles are known. All contributors should run the checks in [feature-workflow.md](feature-workflow.md) before review.

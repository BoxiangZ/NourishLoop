# Contributing

Create a short feature branch and open a PR with the user behavior, affected module, migration/contract changes, tests run, and remaining limitations. Keep a change within its owning module where possible. For cross-module API or schema changes, request review from both sides using [team ownership](docs/development/team-ownership.md).

Use Python 3.12 typing, Ruff, and pytest. Keep route handlers small and place domain rules in services or pure engine code. Use TypeScript strict mode and generated API schema types in the frontend. Add user-facing loading/error states for network calls. Do not commit secrets, real personal health data, or invented restaurant facts presented as verified.

Run the commands in [feature workflow](docs/development/feature-workflow.md) before requesting review. Keep docs honest about implemented versus planned behavior.

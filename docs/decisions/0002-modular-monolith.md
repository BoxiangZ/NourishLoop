# ADR 0002: NourishLoop modular monolith

Status: Accepted for the initial foundation, 2026-10-24.

The active app uses a single FastAPI process with domain modules and PostgreSQL. Recommendation ranking is a deterministic in-process implementation behind a protocol; external LLM explanation is an optional future adapter. The frontend consumes the versioned API with types generated from OpenAPI. We retain the starter code and migrations for course history but do not run its AI/worker services in the NourishLoop Compose stack.

This supports the complete lunch decision loop without external credentials or a queue. It also keeps the meaning of recommendation, plan, and consumption separate. We accept that this foundation does not provide production authentication, verified catalog data, asynchronous AI jobs, or high-volume optimization. Add those only when requirements justify them.

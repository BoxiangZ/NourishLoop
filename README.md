# AI Diet Planning and Meal Analysis Platform

Course project for **MAIE 6000C — Engineering AI Products: From Prototype to Production**.

## Project Overview

This project develops an AI-enabled platform that helps users follow a personalized dietary plan.

A user first provides basic body information and a target, such as target weight or target body-fat percentage. The system uses this information to generate a personalized diet plan.

After a diet plan has been created, the user can upload photos of meals. The platform uses multimodal AI to identify the main foods in the image, compares the meal with the user's active diet plan, and returns feedback on how well the meal aligns with the plan.

The primary product loop is:

```text
Body Profile
    ↓
Diet Plan
    ↓
Meal Photo
    ↓
AI Meal Analysis
    ↓
Comparison with Diet Plan
    ↓
Feedback
```

The project focuses on **general wellness and dietary guidance**. It is not intended to diagnose medical conditions or replace professional medical or dietetic advice.

---

## Problem

Creating a diet plan is only the first step toward a weight-management goal.

Users may know what they should eat in general but still have difficulty evaluating whether their actual daily meals are consistent with their plan.

This project aims to connect long-term dietary planning with day-to-day meal feedback.

The platform therefore supports two related AI-enabled tasks:

1. personalized diet-plan generation;
2. meal-image analysis and comparison against the active diet plan.

---

## Primary User

The primary user is an individual who wants to manage body weight or body-fat goals and needs ongoing support in following a dietary plan.

---

## Core MVP Workflow

The first vertical slice of the project will support the following workflow:

1. User submits body information and a target.
2. API validates and persists the body profile.
3. API creates a diet-plan generation job.
4. Background worker claims the job.
5. AI generates a structured diet plan.
6. The generated plan is persisted in PostgreSQL.
7. User uploads a meal photo.
8. API creates a meal record and meal-analysis job.
9. Worker claims the meal-analysis job.
10. Multimodal AI analyzes the meal.
11. The meal is compared with the active diet plan.
12. Analysis and feedback are persisted.
13. User retrieves the result.

The minimum successful product workflow is therefore:

```text
Profile
→ Diet Plan
→ Meal Photo
→ AI Analysis
→ Plan Comparison
→ Persisted Feedback
```

---

## Planned Core Features

### Body Profile

The platform will store a body-profile snapshot containing information such as:

- height;
- current weight;
- activity level;
- target weight and/or target body-fat percentage.

A profile snapshot can be linked to the diet plan generated from it so historical plans remain traceable.

### Diet Plan Generation

The system will generate a structured dietary plan containing information such as:

- high-level calorie target where appropriate;
- protein target;
- carbohydrate target;
- fat target;
- general dietary guidance.

Diet-plan generation will run asynchronously through the worker.

### Meal Upload

Users will be able to submit a meal photo.

The database will store a reference to the image rather than storing the raw image binary directly in PostgreSQL.

### Meal Analysis

A multimodal AI component will analyze the uploaded image and attempt to identify the main foods in the meal.

The analysis will then compare the meal with the active diet plan.

A first-version result may classify the meal as:

```text
aligned
partially_aligned
not_aligned
```

along with short feedback and suggestions.

### Failure Handling

AI processing is treated as part of an explicit workflow rather than a single synchronous request.

Typical job state:

```text
pending → claimed → completed
                 ↘ failed
```

Failures should leave persistent evidence such as:

- job status;
- attempt count;
- error information;
- processing timestamps.

---

## System Architecture

The project builds on the engineering structure provided by the MAIE 6000C starter repository.

The planned architecture is:

```text
User
  ↓
API Service
  ↓
PostgreSQL
  ↓
Pending Job
  ↓
Background Worker
  ↓
AI Service
  ↓
Persisted Result
  ↓
API Retrieval
  ↓
User
```

### API Service

The API is responsible for:

- validating requests;
- creating persistent records;
- creating asynchronous jobs;
- retrieving current system state;
- exposing health endpoints.

Long-running AI processing should not occur inside the immediate HTTP request cycle.

### PostgreSQL

PostgreSQL represents the durable system state.

Planned persistent entities include:

```text
users
body_profiles
diet_plans
meals
meal_analyses
jobs
```

### Background Worker

The worker processes work outside the immediate request cycle.

The first planned job types are:

```text
generate_diet_plan
analyze_meal
```

### AI Service

The AI layer will support:

```text
Diet Plan Generation
Meal Image Analysis
```

The AI result is persisted before being treated as part of the application workflow.

---

## Proposed Data Model

The initial schema contains six main entities.

### `users`

Provides a stable owner identifier.

### `body_profiles`

Stores body information and goals used for diet-plan generation.

### `diet_plans`

Stores generated plans and their lifecycle.

Expected state:

```text
pending → active
        ↘ failed

active → superseded
```

### `meals`

Stores uploaded meal metadata and image references.

Expected state:

```text
uploaded → processing → analyzed
                      ↘ failed
```

### `meal_analyses`

Stores AI-generated results such as:

- detected foods;
- diet-plan alignment;
- feedback;
- confidence or uncertainty information;
- AI model version;
- processing timestamp.

### `jobs`

Stores asynchronous processing state.

Expected state:

```text
pending → claimed → completed
                 ↘ failed
```

For the full schema and ERD, see:

```text
docs/architecture.md
```

---

## AI Traceability

AI-enabled operations should preserve enough information to understand how a result was produced.

Where practical, the system will record:

- input record references;
- diet-plan reference;
- model version;
- prompt/template version;
- AI output;
- confidence or uncertainty information;
- processing timestamp;
- associated job ID.

This allows results to remain auditable even when the user's profile or active plan later changes.

---

## Privacy and Data Handling

This project may process body measurements and user-uploaded meal images.

The application should avoid unnecessarily copying sensitive information into logs.

Logs should prefer stable identifiers such as:

```text
user_id
diet_plan_id
meal_id
job_id
```

rather than raw personal information.

Secrets, API keys, passwords, and authentication credentials must never be committed to the repository or written into application logs.

Course project data should use appropriate public, synthetic, anonymized, or otherwise approved data sources.

---

## Repository Structure

The repository follows the MAIE 6000C starter structure.

```text
.
├─ .github/
├─ alembic/
├─ docs/
│  ├─ architecture.md
│  ├─ operations.md
│  └─ adrs/
├─ observability/
├─ scripts/
├─ services/
│  ├─ api/
│  ├─ ai/
│  ├─ common/
│  └─ worker/
├─ submissions/
│  ├─ week04/
│  ├─ week07/
│  └─ week13/
├─ tests/
├─ .env.example
├─ compose.yaml
├─ Makefile
├─ pyproject.toml
└─ README.md
```

---

## Current Development Status

The repository currently uses the MAIE 6000C starter implementation as its engineering baseline.

The starter already demonstrates:

- a FastAPI API service;
- a separate AI service;
- PostgreSQL persistence;
- asynchronous worker processing;
- Alembic migrations;
- Docker Compose deployment;
- integration and smoke testing;
- structured logging;
- health checks;
- basic observability.

The current project phase is focused on replacing the starter case-triage domain with the proposed diet-planning and meal-analysis domain.

### Week 4

Current design work includes:

- primary user workflow;
- proposed database schema;
- architecture flow;
- state-transition responsibilities;
- AI traceability and review strategy;
- milestone plan;
- risk register;
- scope-control plan.

See:

```text
docs/architecture.md
submissions/week04/README.md
```

Week 4 checkpoint tag:

```text
w04-proposal
```

The tag should be created only after final review of the Week 4 artifacts.

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd MAIE6000C-starter-wzy
```

### 2. Create the environment file

On macOS/Linux:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 3. Start the stack

```bash
docker compose up --build
```

To run in the background:

```bash
docker compose up --build -d
```

### 4. Check running containers

```bash
docker compose ps
```

---

## Local Endpoints

When the starter stack is running:

```text
API documentation:
http://localhost:8000/docs

AI service documentation:
http://localhost:8100/docs
```

If the observability profile is enabled:

```text
Prometheus:
http://localhost:9090
```

---

## Development Commands

### Start services

```bash
docker compose up --build
```

### Start services in background

```bash
docker compose up --build -d
```

### Stop services

```bash
docker compose down --remove-orphans
```

### Stop services and delete volumes

```bash
docker compose down -v --remove-orphans
```

Use the volume-removal command carefully because it removes local persisted database data.

---

## Database Migrations

Run all available migrations:

```bash
docker compose run --rm api alembic upgrade head
```

Future changes to persistent models should be accompanied by appropriate Alembic migrations rather than only changing Python model definitions.

---

## Testing

### Run the test suite

```bash
pytest -q
```

### Run smoke tests against a running stack

macOS/Linux:

```bash
SMOKE_BASE_URL=http://localhost:8000 pytest tests/smoke -q
```

Windows PowerShell:

```powershell
$env:SMOKE_BASE_URL="http://localhost:8000"
pytest tests/smoke -q
```

The final project should maintain credible verification of important behavior through a combination of:

- unit tests;
- integration tests;
- smoke tests;
- end-to-end verification.

---

## Observability

To start the optional observability profile:

```bash
docker compose --profile observability up --build
```

The project should maintain operational visibility through:

- structured logs;
- health checks;
- processing status;
- failure information;
- basic metrics;
- processing latency where practical.

---

## Development Milestones

### Week 5

Finalize:

- first API contract;
- database schema;
- migrations;
- first API-to-database persistence path.

### Week 7

Deliver the first complete vertical slice:

```text
Profile
→ Diet Plan
→ Meal Upload
→ AI Analysis
→ Feedback
```

### Week 9

Provide reproducible Docker deployment and setup documentation.

### Week 11

Improve:

- reliability;
- structured logging;
- failure handling;
- retry behavior;
- observability;
- basic performance measurement.

### Week 13

Deliver:

- tested final workflow;
- final documentation;
- reproducible deployment;
- final demonstration.

---

## Scope Control

The priority is a small, reliable end-to-end product rather than a large feature set.

The following features are not required for the first MVP and may be deferred:

- exact calorie estimation from a single image;
- exact portion-size estimation;
- advanced dashboards;
- long-term weight prediction;
- full nutritionist-review workflow;
- notification/reminder systems;
- social/community features;
- shopping-list generation;
- recipe recommendation;
- advanced multi-model routing.

The core workflow will be protected before optional features are added.

---

## Documentation

Important project documents:

```text
README.md
docs/architecture.md
docs/operations.md
docs/adrs/
submissions/week04/README.md
submissions/week07/
submissions/week13/
```

### Architecture Proposal

Detailed design:

```text
docs/architecture.md
```

This document contains:

- problem definition;
- primary workflow;
- system architecture;
- ERD and schema;
- state transitions;
- worker and AI processing plan;
- AI traceability;
- privacy/logging considerations;
- API draft;
- failure handling;
- milestones;
- risks;
- scope cuts.

### Week 4 Proposal

Week 4 submission summary:

```text
submissions/week04/README.md
```

---

## Milestone Tags

Planned repository checkpoint tags:

```text
w04-proposal
w07-midterm
w13-final
```

Tags should represent reviewed milestone states of the repository.

---

## Branch Conventions

Recommended branch naming:

```text
feature/...
fix/...
docs/...
submission/...
```

Default branch:

```text
main
```

---

## AI Use

Generative AI tools may be used during project development for activities such as:

- understanding starter code;
- brainstorming architecture options;
- reviewing proposed schemas;
- drafting documentation;
- assisting with implementation and testing.

AI-generated material must be reviewed and verified by the team.

The team remains responsible for understanding and explaining all submitted design and implementation decisions.

Major submissions should include the required **AI Use Statement**.

---

## Project Principle

The project prioritizes engineering reliability over feature quantity.

A smaller system with:

```text
clear persistence
explicit state transitions
reliable async processing
traceable AI results
failure handling
tests
documentation
reproducible deployment
```

is preferable to a larger but fragile implementation.
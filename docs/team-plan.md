# group14 — Team and Project Plan

## Project record

| Field | Value |
|---|---|
| Course | MAIE 6000C — Engineering AI Products: From Prototype to Production |
| Team | group14 |
| Members | Zhang Boxiang, Yang Sibo, Wang Ziyang, Li Zimu |
| Project title | AI Diet Planning and Meal Analysis Platform |
| Repository | https://github.com/Wzyoung203/MAIE6000C-starter-wzy |
| Proposal branch | `boxiang/w04-calorie-proposal` |
| Week 4 checkpoint | `w04-proposal` |
| Primary submission | `submissions/week04/README.md` |
| Proposal contact/editor | Zhang Boxiang |
| Proposal preparation date | 2026-10-07, Asia/Hong_Kong |

Use the project title above in the assignment's “Selected brief or project title” field. An official brief identifier was not supplied; no identifier or instructor approval is invented.

## Planned work allocation

This allocation is the semester plan recorded for this proposal, not a claim that members have already completed or independently reviewed the work. Members can rebalance responsibilities as implementation progresses; the primary owner coordinates the deliverable and reviewer checks its integration.

| Workstream | Primary owner | Reviewer | First deliverable |
|---|---|---|---|
| Responsive UI and profile/plan/meal user workflow | Yang Sibo | Zhang Boxiang | Forms, progress/review screens and client integration against the API draft |
| API, database, nutrition calculation and revisions | Zhang Boxiang | Wang Ziyang | Schema/migrations, persistence, sourced quantities and confirmation contract |
| AI providers, nutrition-source review and evaluation | Li Zimu | Yang Sibo | Provider/data feasibility record, model adapter and labeled development set |
| Worker, deployment and reliability | Wang Ziyang | Li Zimu | Job claims/retries/recovery, shared image storage and reproducible startup |

## Integration sequence

1. Agree on the documented API/schema and implement profile/plan/meal/job persistence.
2. Validate real model access, permitted inputs, quota, source records and local hardware in Week 5.
3. Integrate one profile → plan → photo/quantity → review/confirmation → feedback path before expanding coverage.
4. Run the independent evaluation set and share per-case failures/corrections, not only aggregate success.
5. Reproduce deployment on a second member's machine, then attempt the bounded training experiment if its gates pass.
6. Verify failure/restart/race behavior, freeze features in Week 12 and demonstrate the tested core in Week 13.

Checkpoint details and acceptance evidence are in [architecture.md](architecture.md) and [evaluation-plan.md](evaluation-plan.md). Model/data availability and training remain future technical validation tasks; administrative proposal fields are completed here.

## Review and disclosure record

Zhang Boxiang supplied the product decisions: retain the teammate's diet-planning/meal-analysis workflow, use food/nutrition resources and manual quantities, prefer free hosted multimodal inference with local deployment as a fallback, and improve the remaining architecture/API/reliability/evaluation gaps. He requested preparation and publication on his personal branch.

OpenAI Codex prepared the documentation and performed repository/document consistency checks. Independent review or completed implementation by the other members is not asserted. The detailed [AI Use Statement](../submissions/week04/ai-use-statement.md) distinguishes supplied team decisions, agent checks and future engineering verification.

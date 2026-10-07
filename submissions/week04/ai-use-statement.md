# AI Use Statement — Week 4

## Tools used for this revision

- **OpenAI Codex:** starter inspection, interpretation of the supplied assignment, design review and documentation drafting.
- If other generative AI tools assisted earlier drafts, the team must add their names/uses before submission; this revision does not infer that history.

## Material assistance

Codex inspected API, models, worker, AI service, Compose and submission templates. It proposed a smaller calorie-tracking workflow, data/revision design, API boundaries, worker/retry states, nutrition handling, acceptance cases and milestones. It checked proposed model/data availability against official documentation.

Affected artifacts:

- `README.md`
- `docs/architecture.md`
- `submissions/week04/README.md`
- `submissions/week04/ai-use-statement.md`
- `submissions/week04/canvas-submission.txt`

## Changes and rejected assumptions

- Deferred body profiles and personalized diet plans, following the user's calorie-tracking focus.
- Replaced qualitative diet-plan alignment as the core outcome with review, grams, calories and daily records.
- Rejected accurate photo-only portion inference as an MVP requirement and rejected AI-invented nutrition densities.
- Distinguished current case-triage code from proposed vision features, safe claims and recovery.
- Proposed a local-model feasibility gate and offline source-backed catalog rather than assuming a paid service or comprehensive dataset.
- Separated original AI suggestions from confirmed revisions, and fixture/manual success from genuine model success.

## Agent-performed checks

- Compared the proposal with supplied artifact, workflow, architecture, data, API/async, AI, milestone, risk and statement requirements.
- Inspected executable code to establish actual starter behavior.
- Consulted [Ollama model listing](https://ollama.com/library/qwen2.5vl), [vision API](https://docs.ollama.com/capabilities/vision), and [USDA downloads](https://fdc.nal.usda.gov/download-datasets/).
- Reviewed document consistency and checked local links and Git whitespace before the local commit. These are documentation checks, not evidence that the meal app is implemented.

No real-model inference, nutrition import, meal-schema migration or meal-app end-to-end run was performed for this proposal revision.

## Team verification — complete before official submission

Team review is pending. Record actual reviewer names, checked decisions and modifications; do not describe agent checks as independent team verification.

- Official brief alignment and MVP scope: pending.
- Architecture, schema, API and worker reasoning: pending.
- Available hardware and model feasibility plan: pending.
- Nutrition/preparation assumptions and evaluation plan: pending.
- Ownership and milestones: pending.
- Further changes or rejected suggestions after review: pending.

The team remains responsible for understanding, explaining and verifying the submitted design. Final approval and milestone tagging should follow that review.

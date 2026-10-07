# Evaluation and Acceptance Plan

Team **group14**. Proposed targets for the semester; no measured results are claimed. The official Week 4 milestone requires a realistic plan, not a completed meal app.

## 1. Evaluation data and ground truth

Week 5 development gate: ten consented simple-food photos and synthetic body profiles, plus quantity notes. Record food/preparation labels and measured edible quantities where possible. Use this development set to choose prompts/provider and establish a pretrained baseline.

Before Week 7, freeze a separate twenty-meal evaluation set spanning supported beef/egg/rice/vegetable preparations, user grams, count/size inputs, and simple mixed meals. Keep it out of prompt tuning or training. Add five separate exception cases: non-food image, blurry image, unsupported dish, missing grams/egg size, and explicitly supplied oil/sauce. Provider errors and crashes are injected independently.

Each ground-truth record stores consent/source, visible-food labels, preparation, source catalog/portion IDs, independently checked edible grams/count conversion, and expected nutrition totals from the pinned catalog. One member annotates and another verifies. If weights cannot be independently established, use that example for recognition/review assessment, not as calorie-error ground truth. Reference totals assess agreement with catalog-backed calculation, not laboratory measurement of actual absorbed energy.

## 2. Metrics and provisional targets

| Measure | Definition | Target / interpretation |
|---|---|---|
| End-to-end product completion | Eligible supported submissions with a persisted, user-confirmed nutrition/plan result divided by eligible supported submissions | At least 18/20 in the real-model route; record manual fallback separately |
| Recognition/schema completion | Valid image-recognition drafts / eligible supported photos | At least 18/20; missing quantity is a review question, not a complete-nutrition success |
| Food mapping precision/recall | Correct source-compatible food/preparation matches relative to predicted / labeled supported items | Report both; provisional targets ≥0.85 precision and ≥0.80 recall before user corrections |
| Quantity interpretation | Correct food/amount/unit/size interpretation / labeled quantity expressions | At least 90%; distinguish parsing from the accuracy of user-supplied amounts |
| Calorie error | Absolute error and relative error against independently source-calculated meal reference totals | Report MAE and mean relative error for complete eligible references; zero-reference cases use absolute error |
| Recognition-driven nutrition quality | Draft estimate vs reference before correction, when a complete draft exists | Provisional mean relative calorie error ≤20%; report exclusions/coverage and count-conversion vs gram-input cases separately |
| Corrected calculation | Confirmed quantities and matches vs independently calculated same-source references | Displayed total difference ≤0.1 kcal from rounding; this checks calculation, not real-world calorie accuracy |
| Alignment correctness | API label vs documented rule for fixed budget/meal inputs | 100% of boundary/invalid-input fixtures; human review checks explanation does not contradict numbers |
| Exception visibility | Invalid/uncertain inputs needing correction or visible failure | All five exception cases; no invented complete estimate |
| Persistence | Confirmation, source snapshot and active plan survive reload/restart | All planned persistence cases |

Report input/output examples, failures, corrections needed and limitations; do not hide unsupported inputs by reporting only an aggregate score. Manual record completion and genuine AI success have separate denominators.

Targets are preliminary team goals. Week 5 measurements may justify a documented revision before freezing the test set; do not lower targets silently after viewing final evaluation results.

## 3. Operations and reliability

Record attempt/provider-call counts, free-quota use, failed/timeout rates, upload-to-review latency and confirmation latency. Initial warm-route target: p95 upload-to-review ≤150 seconds for complete drafts requiring up to two model calls. Measure cold start separately; report failed jobs outside success-only latency and show the full submission count. Twenty samples are preliminary, not a production benchmark.

Inject and verify:

- Provider connection failure, `5xx`, `429`/Retry-After, known daily exhaustion and missing model configuration.
- Malformed model JSON, invalid/negative/non-finite values, unsupported food and unresolved serving conversion.
- Worker termination after claim; lease expiry and maximum-attempt exhaustion without permanently claimed jobs.
- Duplicate or stale completion, input revision mismatch, and late analysis/failure after manual confirmation.
- Failed database transaction after image write; missing image; normal restart and persisted volume.
- New plan failure preserving previous active plan; successful plan activation leaving exactly one active plan.
- Stale confirmation, confirmed edits updating daily totals once, and original AI/revision history preserved.
- Hong Kong local-midnight boundary; plan replacement during a day; drafts/failures excluded and shown separately.

No duplicate published analysis, overwritten confirmed revision, infinite automatic retry or silently zero-valued unknown nutrient is acceptable.

## 4. Verification layers

- Unit checks: grams/count conversions, raw/cooked matching, source units, missing values, exact rule boundaries and rounding.
- PostgreSQL integration checks: FK/type constraints, one active plan, target/job transactions, claim locking/leases/tokens, correction revision conflicts and aggregation.
- Deployed smoke checks: profile → plan → photo/notes → draft → confirmation → stored comparison/history; restart/retrieval.
- Real-model evaluation: recorded separately from deterministic fixtures, with model/provider/prompt/catalog/rule versions and per-case outcomes.
- Optional adaptation: baseline versus one trained/adapted model on the untouched evaluation set; include data/compute cost and rejected checkpoints. Prompt-only improvements are not reported as model training.

## 5. Checkpoint evidence and ownership

| Checkpoint | Required project evidence |
|---|---|
| Week 5 | Actual provider access/quota/policy checks, local hardware gate, verified catalog/portion seed, API/schema contract and persistent records |
| Week 7 | Genuine profile/plan/meal/review loop with the frozen set and separated AI/manual outcomes |
| Week 9 | Second-member reproduction, image/database persistence, and optional bounded adaptation result or documented cut |
| Week 11 | Failure-injection results and operation measurements |
| Week 12 | Internal freeze/rehearsal |
| Week 13 | Final tests, real-model demo, final operations guide and honest limitations |

Named owners/reviewers and planned deliverables are recorded in [team-plan.md](team-plan.md). The allocation is a proposal plan, not evidence of work already completed. Store evaluation evidence without keys or personal data and publish only permitted photos.

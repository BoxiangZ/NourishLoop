# Nutrition, Model Selection and Training Plan

Team: **group14**. Week 4 proposal; the integrations, dataset import, measurements and training below have not been performed.

## 1. Separate data, models and calculation

Preserve the team's product loop: profile → AI diet plan → meal photo and quantities → nutrition analysis → user confirmation → plan comparison and feedback.

The team intends to use openly available food/nutrition resources and open models to improve estimates. Three different assets have different responsibilities:

| Asset | Role | Stored where |
|---|---|---|
| Source-backed nutrition data | Energy/macronutrients for a specified food and preparation state | Versioned PostgreSQL catalog and reproducible seed |
| Pretrained or adapted food/vision model | Image recognition and interpretation of food/quantity descriptions | Hosted service or local model runtime; output/metadata persisted |
| Application calculation/comparison | Unit normalization, nutrient totals and explicit plan-budget rules | API/worker code; calculated snapshots persisted |

AI can interpret `150 g cooked beef` or `2 large eggs`, suggest a catalog match and explain a computed comparison. It cannot silently replace a source value, manufacture an unsupported serving conversion, or override a confirmed quantity. User corrections are validated and become the effective inputs.

## 2. Nutrition source and catalog

The initial source candidate is **USDA FoodData Central SR Legacy, April 2018**, distributed through the official [download page](https://fdc.nal.usda.gov/download-datasets/). Its data types are described in the [USDA documentation](https://fdc.nal.usda.gov/data-documentation/). Pin one release rather than mixing changing records. Additional open datasets can be added after checking licensing, provenance, units and coverage.

Week 5: select approximately 20 source-backed entries covering supported preparations of foods such as beef, eggs, rice, chicken, vegetables and cooking oil. This is intended coverage, not a claim that specific records have already been imported.

Record source record ID/URL, release, retrieval date, file checksum, description, preparation state, edible basis, aliases and kcal/protein/carbohydrate/fat per 100 g. Verify all selected values against the downloaded source and retain import/selection notes. Missing nutrients remain null. Do not confuse kJ with kcal or raw and cooked weights. Catalog versions are immutable; adding a new version does not update prior confirmed meals.

Count-unit conversion is a separate reviewed table. A supported egg portion records size/preparation and edible grams per unit with a source reference. An input of `2 eggs` without a supported size/conversion asks the user for size or grams; it does not silently assume all eggs weigh the same. Beef input must specify the supported preparation/weight basis. Added oils/sauces are explicit items when supplied, not inferred as absent.

For unsupported dishes, show unresolved food and permit explicit selection of a supported approximate entry. Record that approximation. Known-item subtotals are incomplete and cannot be presented as complete meal nutrition.

## 3. Calculation and uncertainty

```text
grams = supplied grams
     OR confirmed count × sourced edible grams per unit

item nutrient = grams × catalog nutrient per 100 g / 100
meal nutrients = sum(confirmed item nutrients)
meal nutrient budget = referenced plan's daily targets × selected meal-slot fraction
```

Use decimal arithmetic, save source/conversion snapshots and calculation version, and round only display values to one decimal place. Server recalculates rather than accepting client/model totals. Confirmation accepts one to twenty items, positive grams up to 5000 g per item, or a positive count with a valid portion entry that normalizes within that weight limit.

Distinguish measured/user-entered grams, confirmed standard-size count conversion, and a user-selected approximate food. Show these assumptions with the result. Lower apparent decimal precision does not establish accuracy. No photo-only precision guarantee or fabricated confidence interval is made.

Arithmetic fixture only: a synthetic food has 200 kcal/100 g, and a synthetic egg entry has 100 kcal/100 g with a 50 g portion. `150 g` plus `2 portions` gives 300 + 100 = 400 kcal. These synthetic values are for unit tests, not real beef/egg nutrition.

## 4. Explainable diet-plan comparison

Generated plans must include a positive daily energy target, optional positive macro targets, and positive meal-slot fractions summing to 1. The initial **demo configuration** is breakfast 0.25, lunch 0.35, dinner 0.30, snack 0.10; the user can review the proposed plan before using it. These fractions and tolerances are engineering demo rules, not clinical recommendations.

Compare each confirmed meal against its selected slot budget, not the whole day's target. Rule `meal-budget-v1`:

| Result | Deterministic rule |
|---|---|
| `aligned` | Energy/budget ratio is 0.8–1.2 inclusive; each macro specified by the plan is within 0.7–1.3 of its slot budget |
| `partially_aligned` | Not aligned, but energy ratio is 0.6–1.4 and each specified macro ratio is within 0.5–1.5 |
| `not_aligned` | Complete inputs fall outside the above tolerances |
| Unresolved | Missing quantities, mappings, energy, or a nutrient required by the plan; no alignment label until resolved |

Store the rule version, slot fraction, budget, actual values and differences with each confirmed revision. Label the assessment as **meal-budget alignment**: matching numerical targets does not establish overall dietary quality. AI feedback explains these values and assumptions; it cannot replace the rule's label or invent a missing nutrient. After correction, use recomputed/template feedback to avoid stale prose.

Historical meals use their original plan. Daily summary uses local-day boundaries and groups confirmed totals by plan ID if plans changed during that day; do not compare old meals to a newer plan. Show unconfirmed meal count separately. Multiple meals in the same slot remain possible and are visible in daily totals; single-meal labels do not imply the day's intake is aligned.

## 5. Free hosted model first, local deployment fallback

Following the team's preference, evaluate explicit free image-capable OpenRouter models first. A concrete trial candidate is [`nvidia/nemotron-nano-12b-v2-vl:free`](https://openrouter.ai/nvidia/nemotron-nano-12b-v2-vl:free), listed as a free multimodal endpoint when checked for this proposal on 2026-10-07. It is a general multimodal candidate, not an already validated food/nutrition specialist. Its page discloses input/output logging and trial-use restrictions.

Use this candidate only with synthetic profiles and non-sensitive, consented food-only photos. Review the actual provider policy before any real personal data is processed. Consult [provider logging](https://openrouter.ai/docs/guides/privacy/provider-logging) and [data collection](https://openrouter.ai/docs/guides/privacy/data-collection). A permitted provider/local path is necessary if the free endpoint's policy is incompatible with the inputs.

OpenRouter's [limits documentation](https://openrouter.ai/docs/api_reference/limits) describes free-model quotas and rate-limit handling. Do not hard-code an assumed unlimited/free capacity. Verify actual model availability, key/account quota and provider configuration in Week 5; account access has not been tested. Use an explicit free-model allowlist and disable fallback to paid models. Check total image/request pricing, not only one price field. Stop or use the tested local path on quota exhaustion.

The AI service reads the mounted image and supplies a base64 image rather than an inaccessible container path, following the [multimodal API documentation](https://openrouter.ai/docs/guides/overview/multimodal/overview). Retain selected model/provider and each request ID. Do not use random model selection for reproducible evaluation.

If hosted quality, quota, availability or permitted-data handling is inadequate, evaluate local **`qwen2.5vl:3b` through Ollama**, listed in the [official model catalog](https://ollama.com/library/qwen2.5vl). Record required/available hardware, license, exact runtime/model versions and digest, download/startup instructions, image timings and quality. Hardware feasibility is unverified. The same recognition/feedback contract permits a provider change without redesigning persistence.

### Week 5 selection gate

Use ten consented development photos and synthetic profiles to check access, schema-valid responses, food-label correctness, quantity interpretation, latency, call count and free quota consumption. Prefer a route with at least eight schema-valid recognition responses and eight correct supported-food matches out of ten; record failures and unsupported items explicitly. Test the local fallback before claiming it is available. If no route works, document the blocker and resolve the project plan with the instructor before Week 7; fixtures do not satisfy real AI evidence.

## 6. Bounded training/model-adaptation experiment

The team intends to investigate an open food-recognition or nutrition-estimation model and improve food/quantity interpretation through a small training/adaptation experiment after the baseline. Importing a nutrient table is not vision-model training, and calling a hosted model does not grant access to its weights.

Proceed only after the core Week 7 workflow works and the team has verified model/dataset licenses, appropriate labels and available compute. Nutrition data can ground labels and calculations but cannot alone provide image-to-food or portion ground truth. Human quantity annotations must distinguish measured values from guesses. Acquire an appropriately licensed image/food dataset or collect consented annotated examples; no suitable training set has yet been secured.

Before starting, publish an experiment plan: selected checkpoint/license, prediction task, data sources/size, separate training/validation/held-out split, compute/time budget, baseline metrics and reproducible configuration. Permit one small adaptation experiment, at most two runs within one week; no full pretraining or unbounded architecture search. Keep development samples out of the held-out set. Prefer adapter-style fine-tuning if the selected model supports it and hardware permits; otherwise record the training blocker and keep the pretrained baseline.

Evaluate baseline versus adapted model on the same untouched test set for food mapping, quantity parsing and nutrition-estimate error. Deploy adaptation only if it improves the predefined measures without breaking schema validity/latency. Version its checkpoint and outputs. A failed/non-improving experiment is reported honestly and is cut before any core product feature.

## 7. Decisions still requiring team verification

Official brief compatibility, exact source records and portion conversions, model license/access, account quota, local hardware and training labels remain verification tasks. Published documentation confirms candidate capabilities, not this application's achieved quality or availability.

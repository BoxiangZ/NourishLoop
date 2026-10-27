# Week 4 AI adapters

The optional `services/ai` service calls the course endpoint `https://api1.hkgai.net/v1/chat/completions` with model `t2_hkgai-v3_fp8_1m_e7` for text drafts. On 2026-10-27, an authenticated text request succeeded. A synthetic image request was rejected with `is not a multimodal model`.

For image drafts, the service uses Google's `generateContent` API. The supplied Gemini credential passed model lookup and image token counting for `gemini-3.8-flash`, but two small generation requests timed out after 45 and 90 seconds. The same credential returned a text result and correctly identified a synthetic red image with `gemini-3.5-flash-lite`. That model also completed the structured meal-image adapter call with zero foods and one review question for the non-food test image. The default is therefore the verified `gemini-3.5-flash-lite`; set `GEMINI_MODEL=gemini-3.8-flash` to retry the originally supplied model later. This is a connectivity and schema check, not food-recognition accuracy evidence.

## Run

Copy the relevant lines from `.env.example` into a local `.env` and supply `HKG_API_KEY` and `GEMINI_API_KEY`. Both keys stay server-side and `.env` is Git-ignored. Start just this service with:

```bash
docker compose --profile week4-ai up --build ai
```

The service listens at `http://localhost:8100`; its API contract is at `/docs`. Without Compose, run `uvicorn services.ai.app.main:app --port 8100` from the repository root after installing the Python dependencies. HKGAI has a 45-second default request timeout and Gemini has a 90-second default. Provider failures omit keys and response bodies.

## Current contracts

`POST /diet-plans/draft` accepts a goal and a caller-provided daily calorie target, with optional macro targets. The model supplies only `guidance_text`; the service copies numeric targets from the caller and marks the result `requires_review`. Example body:

```json
{"goal":"Maintain current weight","daily_calorie_target":2000}
```

`POST /meals/interpret-notes` accepts text such as `150 g cooked beef and 2 large eggs`. It returns candidate foods and quantities plus review questions. Every food requires review; a quantity must occur in the original note. It does not return calories, macros, plan alignment, or confirmation. Example body:

```json
{"notes":"150 g cooked beef and 2 large eggs"}
```

`POST /meals/recognize` accepts `image_base64`, `mime_type` (`image/png`, `image/jpeg`, or `image/webp`) and optional `notes`. The request is capped at 5 MB of decoded image data. Gemini returns candidate foods and review questions, with every candidate marked `needs_review`. Quantities must occur verbatim in the user's notes; otherwise they are rejected. The endpoint does not calculate nutrition, store the image, or confirm a meal. Example body shape:

```json
{"image_base64":"<base64-encoded image bytes>","mime_type":"image/png","notes":"2 large eggs"}
```

All responses include the model, provider request ID when available, and prompt version to support later persistence and evaluation. These endpoints are standalone AI-service drafts. The Week 4 API, database entities, worker jobs, nutrition catalog, user correction flow, and photo upload are still proposed work. To complete the Week 4 vertical slice, connect API → persisted job → worker → AI service → persisted result. The active NourishLoop API under `apps/api` remains separate.

from __future__ import annotations

import base64
import binascii
import json
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from services.ai.app.gemini import GeminiClient
from services.ai.app.hkgai import Completion, HKGaiClient, ProviderError


class DietPlanDraftRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=200)
    daily_calorie_target: float = Field(gt=0, le=10000)
    protein_target_g: float | None = Field(default=None, gt=0, le=1000)
    carb_target_g: float | None = Field(default=None, gt=0, le=1000)
    fat_target_g: float | None = Field(default=None, gt=0, le=1000)


class DietPlanDraftResponse(BaseModel):
    daily_calorie_target: float
    protein_target_g: float | None
    carb_target_g: float | None
    fat_target_g: float | None
    guidance_text: str = Field(min_length=1, max_length=1000)
    requires_review: bool = True
    model: str
    provider_request_id: str | None
    prompt_version: Literal["plan-draft-v1"] = "plan-draft-v1"


class MealNotesRequest(BaseModel):
    notes: str = Field(min_length=1, max_length=2000)


class ParsedFood(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    preparation: str | None = Field(default=None, max_length=120)
    quantity_from_notes: str | None = Field(default=None, max_length=120)
    needs_review: Literal[True] = True


class MealNotesResponse(BaseModel):
    foods: list[ParsedFood] = Field(max_length=20)
    review_questions: list[str] = Field(max_length=10)
    model: str
    provider_request_id: str | None
    prompt_version: Literal["meal-notes-v1"] = "meal-notes-v1"


class MealRecognitionRequest(BaseModel):
    image_base64: str = Field(min_length=1, max_length=7_000_000)
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    notes: str = Field(default="", max_length=2000)

    @field_validator("image_base64")
    @classmethod
    def validate_image(cls, value: str) -> str:
        try:
            image = base64.b64decode(value, validate=True)
        except binascii.Error:
            raise ValueError("image_base64 must contain valid base64") from None
        if not image or len(image) > 5_000_000:
            raise ValueError("image must be between 1 byte and 5 MB")
        return value


class MealRecognitionResponse(BaseModel):
    foods: list[ParsedFood] = Field(max_length=20)
    review_questions: list[str] = Field(max_length=10)
    model: str
    provider_request_id: str | None
    prompt_version: Literal["meal-image-v1"] = "meal-image-v1"


def _json_object(completion: Completion) -> dict:
    content = completion.content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            content = "\n".join(lines[1:-1])
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        raise ProviderError("HKGAI returned invalid JSON") from None
    if not isinstance(value, dict):
        raise ProviderError("HKGAI returned a non-object draft")
    return value


def draft_plan(client: HKGaiClient, request: DietPlanDraftRequest) -> DietPlanDraftResponse:
    completion = client.complete(
        [
            {
                "role": "system",
                "content": (
                    "You write brief general-wellness meal-planning guidance. Return only a JSON "
                    "object with one key, guidance_text, containing at most 600 characters. "
                    "Use only the supplied goal and numeric targets. Do not alter targets, "
                    "diagnose, prescribe, or claim clinical precision. "
                    "Say that targets need review."
                ),
            },
            {"role": "user", "content": request.model_dump_json()},
        ]
    )
    data = _json_object(completion)
    guidance = data.get("guidance_text")
    if not isinstance(guidance, str) or not guidance.strip() or len(guidance) > 1000:
        raise ProviderError("HKGAI returned invalid plan guidance")
    return DietPlanDraftResponse(
        **request.model_dump(exclude={"goal"}),
        guidance_text=guidance.strip(),
        model=completion.model,
        provider_request_id=completion.request_id,
    )


def interpret_meal_notes(client: HKGaiClient, request: MealNotesRequest) -> MealNotesResponse:
    completion = client.complete(
        [
            {
                "role": "system",
                "content": (
                    "Interpret only the user's meal notes. Return only a JSON object "
                    "with foods (array of {name, preparation, quantity_from_notes, needs_review}) "
                    "and review_questions (array of strings). Only copy a quantity when explicitly "
                    "present in notes; otherwise use null. Set needs_review true for every food. "
                    "Copy quantities as exact substrings of the notes. "
                    "If food, preparation or quantity is unclear, ask a review question. Do not "
                    "estimate calories, macros, missing grams, or plan alignment."
                ),
            },
            {"role": "user", "content": f"User notes: {request.notes}"},
        ]
    )
    data = _json_object(completion)
    try:
        draft = MealNotesResponse.model_validate(
            {**data, "model": completion.model, "provider_request_id": completion.request_id}
        )
    except ValueError:
        raise ProviderError("HKGAI returned invalid meal notes") from None
    if any(
        food.quantity_from_notes
        and food.quantity_from_notes.lower() not in request.notes.lower()
        for food in draft.foods
    ):
        raise ProviderError("HKGAI returned a quantity absent from user notes")
    return draft


def recognize_meal(
    client: GeminiClient, request: MealRecognitionRequest
) -> MealRecognitionResponse:
    completion = client.generate(
        prompt=(
            "Inspect the meal image and user notes. Return only a JSON object with foods "
            "(array of {name, preparation, quantity_from_notes, needs_review}) and "
            "review_questions (array of strings). List only visibly plausible foods. "
            "Copy quantities only as exact substrings from user notes; otherwise use null. "
            "Set needs_review true for every food. Ask for clarification when image, "
            "preparation or quantity is unclear. Do not infer grams from the image or "
            "estimate calories, macros, medical effects, or plan alignment."
        ),
        parts=[
            {
                "inline_data": {
                    "mime_type": request.mime_type,
                    "data": request.image_base64,
                }
            },
            {"text": f"User notes: {request.notes or '(none)'}"},
        ],
    )
    data = _json_object(completion)
    try:
        draft = MealRecognitionResponse.model_validate(
            {**data, "model": completion.model, "provider_request_id": completion.request_id}
        )
    except ValueError:
        raise ProviderError("Gemini returned an invalid meal image draft") from None
    if any(
        food.quantity_from_notes
        and food.quantity_from_notes.lower() not in request.notes.lower()
        for food in draft.foods
    ):
        raise ProviderError("Gemini returned a quantity absent from user notes")
    return draft

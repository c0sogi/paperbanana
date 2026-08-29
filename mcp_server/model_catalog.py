"""Exact model choices exposed by the PaperBanana MCP server."""

from __future__ import annotations

from typing import Literal

McpVlmModel = Literal["gemini-3.7-flash", "gpt-5.2"]
McpImageModel = Literal[
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gpt-image-1.5",
    "gpt-image-2",
]

DEFAULT_VLM_MODEL: McpVlmModel = "gemini-3.7-flash"
DEFAULT_IMAGE_MODEL: McpImageModel = "gemini-3.1-flash-image"

VLM_PROVIDERS: dict[str, str] = {
    "gemini-3.7-flash": "gemini",
    "gpt-5.2": "openai",
}

IMAGE_PROVIDERS: dict[str, str] = {
    "gemini-3.1-flash-image": "google_imagen",
    "gemini-3-pro-image": "google_imagen",
    "gpt-image-1.5": "openai_imagen",
    "gpt-image-2": "openai_imagen",
}


def exact_model_overrides(
    *,
    vlm_model: str | None = None,
    image_model: str | None = None,
    vlm_provider: str | None = None,
    image_provider: str | None = None,
) -> dict[str, str | None]:
    """Validate exact MCP model IDs, infer providers, and build Settings overrides."""
    overrides: dict[str, str | None] = {}
    if vlm_model:
        inferred = VLM_PROVIDERS.get(vlm_model)
        if inferred is None:
            raise ValueError(
                f"Unsupported VLM model {vlm_model!r}. Available: {', '.join(VLM_PROVIDERS)}"
            )
        if vlm_provider and vlm_provider != inferred:
            raise ValueError(
                f"VLM model {vlm_model!r} requires provider {inferred!r}, "
                f"not {vlm_provider!r}."
            )
        overrides.update(
            vlm_provider=inferred,
            vlm_model=vlm_model,
            google_vlm_model=None,
            openai_vlm_model=None,
        )
    elif vlm_provider:
        overrides["vlm_provider"] = vlm_provider

    if image_model:
        inferred = IMAGE_PROVIDERS.get(image_model)
        if inferred is None:
            raise ValueError(
                f"Unsupported image model {image_model!r}. Available: {', '.join(IMAGE_PROVIDERS)}"
            )
        if image_provider and image_provider != inferred:
            raise ValueError(
                f"Image model {image_model!r} requires provider {inferred!r}, "
                f"not {image_provider!r}."
            )
        overrides.update(
            image_provider=inferred,
            image_model=image_model,
            google_image_model=None,
            openai_image_model=None,
        )
    elif image_provider:
        overrides["image_provider"] = image_provider

    return overrides


def available_models() -> dict[str, object]:
    """Return objective model metadata; prices are USD and dated."""
    return {
        "defaults": {
            "vlm_model": DEFAULT_VLM_MODEL,
            "image_model": DEFAULT_IMAGE_MODEL,
        },
        "price_checked_at": "2026-08-29",
        "vlm_models": [
            {
                "model": "gemini-3.7-flash",
                "provider": "gemini",
                "status": "generally_available",
                "input_modalities": ["text", "image", "video", "audio", "pdf"],
                "pricing_usd_per_1m_tokens": {"input": 0.75, "output": 3.75},
                "required_environment": ["GOOGLE_API_KEY"],
                "pricing_source": "https://ai.google.dev/gemini-api/docs/pricing",
            },
            {
                "model": "gpt-5.2",
                "provider": "openai",
                "status": "available_previous_generation",
                "input_modalities": ["text", "image"],
                "pricing_usd_per_1m_tokens": {"input": 2.5, "output": 10.0},
                "required_environment": ["OPENAI_API_KEY"],
                "pricing_source": "https://developers.openai.com/api/docs/pricing",
            },
        ],
        "image_models": [
            {
                "model": "gemini-3.1-flash-image",
                "provider": "google_imagen",
                "status": "generally_available",
                "resolutions": ["0.5K", "1K", "2K", "4K"],
                "pricing_type": "resolution_based",
                "pricing_usd_per_image": {"0.5K": 0.045, "1K": 0.067, "2K": 0.101, "4K": 0.151},
                "required_environment": ["GOOGLE_API_KEY"],
                "pricing_source": "https://ai.google.dev/gemini-api/docs/pricing",
            },
            {
                "model": "gemini-3-pro-image",
                "provider": "google_imagen",
                "status": "generally_available",
                "resolutions": ["1K", "2K", "4K"],
                "pricing_type": "resolution_based",
                "pricing_usd_per_image": {"1K": 0.134, "2K": 0.134, "4K": 0.24},
                "required_environment": ["GOOGLE_API_KEY"],
                "pricing_source": "https://ai.google.dev/gemini-api/docs/pricing",
            },
            {
                "model": "gpt-image-1.5",
                "provider": "openai_imagen",
                "status": "available_previous_generation",
                "resolutions": ["1024x1024", "1024x1536", "1536x1024"],
                "pricing_type": "quality_and_resolution_based",
                "pricing_usd_per_image": {
                    "low": {"1024x1024": 0.009, "1024x1536": 0.013, "1536x1024": 0.013},
                    "medium": {"1024x1024": 0.034, "1024x1536": 0.05, "1536x1024": 0.05},
                    "high": {"1024x1024": 0.133, "1024x1536": 0.20, "1536x1024": 0.20},
                },
                "required_environment": ["OPENAI_API_KEY"],
                "pricing_source": "https://developers.openai.com/api/docs/models/gpt-image-1.5",
            },
            {
                "model": "gpt-image-2",
                "provider": "openai_imagen",
                "status": "current_default",
                "resolutions": ["1024x1024", "1024x1536", "1536x1024"],
                "pricing_type": "token_based",
                "pricing_usd_per_1m_image_tokens": {
                    "input": 8.0,
                    "cached_input": 2.0,
                    "output": 30.0,
                },
                "required_environment": ["OPENAI_API_KEY"],
                "pricing_source": "https://developers.openai.com/api/docs/pricing",
            },
        ],
    }

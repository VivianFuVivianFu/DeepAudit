"""
Deep-Audit API Format Presets
Predefined API format configurations for common AI system interfaces.

Supports OpenAI-compatible, Anthropic, and custom endpoint formats so the
scanner can target any enterprise AI system without manual payload wiring.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional


@dataclass
class APIFormatPreset:
    """
    Defines how to build payloads for and parse responses from a target AI API.

    Attributes:
        name: Preset identifier (e.g., "openai", "anthropic", "custom")
        build_payload: Callable(user_message, **kwargs) -> dict request body
        parse_response: Callable(response_json) -> str extracted text
        default_url_suffix: URL path suffix appended to the base URL
        default_headers: Additional HTTP headers required by this preset
    """

    name: str
    build_payload: Callable[..., Dict[str, Any]]
    parse_response: Callable[[Dict[str, Any]], str]
    default_url_suffix: str = ""
    default_headers: Dict[str, str] = field(default_factory=dict)


def openai_preset(model: str = "gpt-4") -> APIFormatPreset:
    """
    Create an OpenAI-compatible API preset.

    Supports any OpenAI-format endpoint including Azure OpenAI, Groq, Together
    AI, Mistral, and any other OpenAI-compatible provider.

    Args:
        model: Model name to send in requests (default: "gpt-4")

    Returns:
        APIFormatPreset configured for OpenAI chat completions format
    """

    def build(user_message: str, **kwargs) -> Dict[str, Any]:
        return {
            "model": kwargs.get("model", model),
            "messages": [{"role": "user", "content": user_message}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }

    def parse(response_json: Dict[str, Any]) -> str:
        try:
            return response_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return "[ERROR: could not parse response]"

    return APIFormatPreset(
        name="openai",
        build_payload=build,
        parse_response=parse,
        default_url_suffix="/v1/chat/completions",
        default_headers={"Content-Type": "application/json"},
    )


def anthropic_preset(model: str = "claude-sonnet-4-5-20250929") -> APIFormatPreset:
    """
    Create an Anthropic Messages API preset.

    Args:
        model: Claude model ID to use in requests

    Returns:
        APIFormatPreset configured for Anthropic Messages API
    """

    def build(user_message: str, **kwargs) -> Dict[str, Any]:
        return {
            "model": kwargs.get("model", model),
            "messages": [{"role": "user", "content": user_message}],
            "max_tokens": kwargs.get("max_tokens", 1024),
        }

    def parse(response_json: Dict[str, Any]) -> str:
        try:
            return response_json["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            return "[ERROR: could not parse response]"

    return APIFormatPreset(
        name="anthropic",
        build_payload=build,
        parse_response=parse,
        default_url_suffix="/v1/messages",
        default_headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
    )


def custom_preset() -> APIFormatPreset:
    """
    Create a generic/custom API preset with best-effort response parsing.

    Payload format matches the original Deep-Audit default behavior so existing
    integrations remain unchanged when no --api_format flag is supplied.

    Returns:
        APIFormatPreset with backward-compatible payload and flexible parsing
    """

    def build(user_message: str, **kwargs) -> Dict[str, Any]:
        return {"message": user_message, "user_id": "audit_scanner"}

    def parse(response_json: Dict[str, Any]) -> str:
        if not isinstance(response_json, dict):
            return "[ERROR: could not parse response]"
        try:
            # Try common response field names in priority order
            for field_name in (
                "response",
                "message",
                "output",
                "text",
                "content",
                "result",
                "answer",
                "reply",
                "completion",
            ):
                value = response_json.get(field_name)
                if value and isinstance(value, str):
                    return value
            # Nothing matched — return JSON string representation
            return str(response_json)
        except Exception:
            return "[ERROR: could not parse response]"

    return APIFormatPreset(
        name="custom",
        build_payload=build,
        parse_response=parse,
        default_url_suffix="",
        default_headers={"Content-Type": "application/json"},
    )


def get_preset(name: str, **kwargs) -> APIFormatPreset:
    """
    Retrieve a preset by name.

    Args:
        name: Preset name — one of "openai", "anthropic", "custom"
        **kwargs: Optional overrides forwarded to the preset factory.
                  Supported keys:
                    model (str)  — override model name for openai/anthropic presets

    Returns:
        APIFormatPreset for the specified format

    Raises:
        ValueError: If the preset name is not recognised
    """
    factories = {
        "openai": lambda: openai_preset(model=kwargs.get("model", "gpt-4")),
        "anthropic": lambda: anthropic_preset(
            model=kwargs.get("model", "claude-sonnet-4-5-20250929")
        ),
        "custom": lambda: custom_preset(),
    }

    if name not in factories:
        available = list(factories.keys())
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")

    return factories[name]()

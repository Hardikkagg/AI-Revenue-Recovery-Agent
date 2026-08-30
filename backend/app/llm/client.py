"""Ollama HTTP client with robust error handling and timeout protection."""

from __future__ import annotations

import json
from typing import Any
import urllib.error
import urllib.request

from app.config import settings


class OllamaClientError(Exception):
    """Base exception for Ollama client interactions."""


class OllamaClient:
    """Lightweight HTTP client for local Ollama server."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.llm_timeout_seconds

    def generate(self, system_prompt: str, prompt: str) -> dict[str, Any]:
        """Send a generate request to Ollama /api/generate endpoint with JSON format."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status != 200:
                    raise OllamaClientError(f"Ollama returned HTTP status {response.status}")
                raw_body = response.read().decode("utf-8")
                res_json = json.loads(raw_body)
                response_text = res_json.get("response", "")
                return json.loads(response_text)
        except urllib.error.URLError as exc:
            raise OllamaClientError(f"Failed to connect to Ollama at {self.base_url}: {exc}") from exc
        except TimeoutError as exc:
            raise OllamaClientError(f"Ollama request timed out after {self.timeout}s: {exc}") from exc
        except (json.JSONDecodeError, KeyError) as exc:
            raise OllamaClientError(f"Failed to parse Ollama JSON response: {exc}") from exc
        except Exception as exc:
            raise OllamaClientError(f"Unexpected error communicating with Ollama: {exc}") from exc

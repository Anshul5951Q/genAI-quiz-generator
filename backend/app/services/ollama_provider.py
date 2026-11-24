"""
OllamaProvider — Local LLM inference via Ollama REST API.
Integrates seamlessly with the existing BaseLLMProvider interface.
"""
import json
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services.llm_provider import BaseLLMProvider, LLMProviderError


class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama provider. Uses httpx for synchronous HTTP (matching existing provider pattern).
    Configured via OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: int | None = None,
        num_ctx: int | None = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS
        self.num_ctx = num_ctx or settings.OLLAMA_NUM_CTX

    def _check_connectivity(self) -> bool:
        """Quick health check without raising."""
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate text via Ollama /api/generate endpoint.
        Forces JSON output mode and validates the response.
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "num_ctx": self.num_ctx,
                "temperature": 0.3,
                "num_predict": 4096,
            },
        }

        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                start = time.time()
                response = httpx.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout,
                )
                latency_ms = int((time.time() - start) * 1000)

                if response.status_code != 200:
                    err = response.text[:200]
                    logger.warning(f"Ollama HTTP {response.status_code} on attempt {attempt}: {err}")
                    if attempt == max_attempts:
                        raise LLMProviderError(f"Ollama returned HTTP {response.status_code}: {err}")
                    time.sleep(1)
                    continue

                data = response.json()
                content = data.get("message", {}).get("content", "").strip()

                if not content:
                    if attempt == max_attempts:
                        raise LLMProviderError("Ollama returned empty response content.")
                    continue

                logger.info(f"Ollama '{self.model_name}' responded in {latency_ms}ms")
                return content

            except httpx.ConnectError:
                raise LLMProviderError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    "Ensure Ollama is running: 'ollama serve' or start the Ollama application."
                )
            except httpx.TimeoutException:
                if attempt == max_attempts:
                    raise LLMProviderError(
                        f"Ollama request timed out after {self.timeout}s. "
                        "Consider increasing OLLAMA_TIMEOUT_SECONDS or using a smaller model."
                    )
                logger.warning(f"Ollama timeout on attempt {attempt}. Retrying...")
                continue
            except LLMProviderError:
                raise
            except Exception as e:
                if attempt == max_attempts:
                    raise LLMProviderError(f"Ollama request failed: {str(e)[:150]}")
                time.sleep(1)

        raise LLMProviderError("Ollama failed after all retry attempts.")

import logging
from typing import Any, Dict, Optional

import requests

from honeybadger.brain.ollama_brain import HONEYBADGER_SYSTEM_PROMPT, ask_honeybadger
from honeybadger.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, OLLAMA_URL

logger = logging.getLogger(__name__)

ROUTABLE_KEYWORDS = ["code", "build", "program", "analyze", "hack"]


class BrainRouter:
    def __init__(self) -> None:
        self.current_model: Optional[str] = None

    def route_request(self, prompt: str, context: Optional[Any] = None) -> str:
        target_model = self._select_model(prompt, context)

        if target_model == "gemma3:4b":
            self.auto_unload()

        try:
            if target_model == "phi4-mini":
                self.current_model = "phi4-mini"
                return ask_honeybadger(prompt, model="general")

            self.current_model = target_model
            return self._local_gemma_request(prompt)
        except Exception as exc:
            logger.warning("Local Ollama request failed, falling back to API: %s", exc)
            return self._fallback_to_api(prompt)

    def auto_unload(self) -> None:
        if self.current_model != "phi4-mini":
            return

        unload_url = f"{OLLAMA_URL.rstrip('/')}/v1/models/phi4-mini/unload"
        payload = {"keep_alive": 0}

        try:
            response = requests.post(unload_url, json=payload, timeout=30)
            response.raise_for_status()
            logger.info("Unloaded phi4-mini from Ollama before loading Gemma 3 4B.")
        except Exception as exc:
            logger.warning(
                "Failed to unload phi4-mini via Ollama API, attempting best-effort recovery: %s",
                exc,
            )

    def _select_model(self, prompt: str, context: Optional[Any]) -> str:
        combined = prompt or ""
        if context is not None:
            if isinstance(context, str):
                combined += f" {context}"
            else:
                combined += f" {str(context)}"

        combined_lower = combined.lower()
        if any(keyword in combined_lower for keyword in ROUTABLE_KEYWORDS):
            return "gemma3:4b"
        return "phi4-mini"

    def _local_gemma_request(self, prompt: str) -> str:
        request_url = f"{OLLAMA_URL.rstrip('/')}/v1/chat/completions"
        payload: Dict[str, Any] = {
            "model": "gemma3:4b",
            "messages": [
                {"role": "system", "content": HONEYBADGER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "keep_alive": 0,
        }

        response = requests.post(request_url, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Ollama gemma request returned no choices")

        return choices[0].get("message", {}).get("content", "").strip()

    def _fallback_to_api(self, prompt: str) -> str:
        if OPENAI_API_KEY:
            try:
                import openai

                openai.api_key = OPENAI_API_KEY
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": HONEYBADGER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=512,
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:
                logger.warning("OpenAI fallback failed: %s", exc)

        if ANTHROPIC_API_KEY:
            try:
                from anthropic import Anthropic

                client = Anthropic(api_key=ANTHROPIC_API_KEY)
                completion = client.completions.create(
                    model="claude-3.5",
                    prompt=f"{HONEYBADGER_SYSTEM_PROMPT}\nHuman: {prompt}\nAssistant:",
                    max_tokens_to_sample=512,
                )
                return completion["completion"].strip()
            except Exception as exc:
                logger.warning("Anthropic fallback failed: %s", exc)

        raise RuntimeError("No fallback API available or all fallback providers failed.")

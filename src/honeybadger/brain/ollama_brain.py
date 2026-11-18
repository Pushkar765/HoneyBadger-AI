import json
import logging
import subprocess
from typing import Dict, Generator, List, Optional

import requests
import warnings
from requests.exceptions import ConnectionError, RequestException, Timeout

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    import pynvml

from honeybadger.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, OLLAMA_URL

logger = logging.getLogger(__name__)

MODELS: Dict[str, str] = {
    "general": "phi4-mini",
    "emotion": "phi4-mini",
    "fast": "phi4-mini",
    "reasoning": "gemma3:4b",
    "coding": "gemma3:4b",
    "security": "gemma3:4b",
}

HONEYBADGER_SYSTEM_PROMPT = (
    "You are HoneyBadger — a sharp, loyal, and highly capable AI companion.\n"
    "\n"
    "PERSONALITY & TONE:\n"
    "- Speak in clear, confident, natural English. No slang, no filler words.\n"
    "- Be warm and direct. Give the answer first, then brief context if needed.\n"
    "- Never be condescending. Treat the user as intelligent.\n"
    "- Use complete sentences. Avoid bullet points unless listing more than 3 items.\n"
    "\n"
    "RESPONSE FORMAT (MANDATORY):\n"
    "- Plain text only. No LaTeX, no Markdown symbols (*, #, `), no special characters.\n"
    "- Never show step-by-step working unless the user explicitly asks 'show your work'.\n"
    "- For numbers and math, write naturally: 67 + 69 = 136.\n"
    "- Keep responses brief and purposeful. Do not repeat what the user said.\n"
    "\n"
    "ACTIONS — PowerShell execution:\n"
    "- You can run commands on the user's Windows machine.\n"
    "- Wrap the exact command in <execute>...</execute> tags.\n"
    "- Only run commands when the user explicitly asks for a system action.\n"
    "- NEVER run Get-CimInstance, Get-WmiObject, or hardware/CPU queries unless the "
    "user specifically asks about hardware or system status.\n"
    "\n"
    "SOCIAL MEDIA APPS (HIGHEST PRIORITY RULE):\n"
    "- The user has social media apps installed on their Windows device.\n"
    "- When asked to open ANY social media or messaging app, ALWAYS respond ONLY with "
    "the matching <execute> tag below. Do not explain, do not ask for confirmation, "
    "do not mention the browser. Just run the command.\n"
    "- If the app is not in the list below, say: 'I don't have a launch shortcut for "
    "that app. Would you like me to search for it in the Microsoft Store?'\n"
    "\n"
    "  Instagram:  <execute>Start-Process 'instagram:'</execute>\n"
    "  Facebook:   <execute>Start-Process 'fb:'</execute>\n"
    "  X/Twitter:  <execute>Start-Process 'twitter:'</execute>\n"
    "  TikTok:     <execute>Start-Process 'tiktok:'</execute>\n"
    "  Snapchat:   <execute>Start-Process 'snapchat:'</execute>\n"
    "  YouTube:    <execute>Start-Process 'vnd.youtube:'</execute>\n"
    "  WhatsApp:   <execute>Start-Process 'whatsapp:'</execute>\n"
    "  Telegram:   <execute>Start-Process 'tg:'</execute>\n"
    "  Discord:    <execute>Start-Process 'discord:'</execute>\n"
    "  LinkedIn:   <execute>Start-Process 'linkedin:'</execute>\n"
    "  Reddit:     <execute>Start-Process 'reddit:'</execute>\n"
    "  Pinterest:  <execute>Start-Process 'pinterestsearch:'</execute>\n"
    "  Twitch:     <execute>Start-Process 'twitch:'</execute>\n"
    "  Signal:     <execute>Start-Process 'sgnl:'</execute>\n"
    "  BeReal:     <execute>Start-Process 'bereal:'</execute>\n"
)


MAX_VRAM_FRACTION = 0.90
CURRENT_MODEL: Optional[str] = None


def _get_ollama_endpoint(path: str) -> str:
    return f"{OLLAMA_URL.rstrip('/')}/{path.lstrip('/')}"


def _run_ollama_command(args: List[str]) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.warning("Ollama command failed: %s", result.stderr.strip())
        return result.stdout.strip()
    except FileNotFoundError:
        logger.error("Ollama CLI is not installed or not available on PATH.")
        return ""
    except subprocess.TimeoutExpired:
        logger.error("Ollama command timed out: %s", " ".join(args))
        return ""


def _resolve_model(model_name: str) -> str:
    normalized = model_name.strip().lower()
    if normalized in MODELS.values() or ":" in normalized:
        return model_name
    return MODELS.get(normalized, MODELS["general"])


def _unload_model(model_name: str) -> None:
    if not model_name:
        return

    logger.info("Attempting to unload Ollama model: %s", model_name)
    try:
        requests.post(
            _get_ollama_endpoint("api/generate"),
            json={"model": model_name, "keep_alive": 0},
            timeout=10,
        )
        logger.info("Unloaded model %s from VRAM.", model_name)
    except Exception as exc:
        logger.warning("Failed to unload model %s: %s", model_name, exc)


def check_vram_usage() -> Dict[str, float]:
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        used_gb = mem_info.used / 1024**3
        total_gb = mem_info.total / 1024**3
        percent = used_gb / total_gb if total_gb > 0 else 0.0
    except Exception as exc:
        logger.error("Failed to read VRAM usage: %s", exc)
        used_gb = 0.0
        total_gb = 0.0
        percent = 0.0
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass

    if percent >= MAX_VRAM_FRACTION and CURRENT_MODEL:
        logger.warning(
            "VRAM usage is above %.0f%% (%.2f GB / %.2f GB), unloading %s.",
            MAX_VRAM_FRACTION * 100,
            used_gb,
            total_gb,
            CURRENT_MODEL,
        )
        _unload_model(CURRENT_MODEL)

    return {
        "used_gb": used_gb,
        "total_gb": total_gb,
        "percent": percent,
    }


def switch_model(task_type: str) -> str:
    global CURRENT_MODEL

    selected = _resolve_model(task_type)
    if selected != CURRENT_MODEL:
        usage = check_vram_usage()
        if usage["percent"] >= MAX_VRAM_FRACTION and CURRENT_MODEL:
            _unload_model(CURRENT_MODEL)
        CURRENT_MODEL = selected
        logger.info("Switched HoneyBadger brain model to: %s", selected)
    return selected


def _fallback_to_api(prompt: str) -> str:
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

    raise RuntimeError(
        f"Ollama server is unavailable at {OLLAMA_URL} and no fallback API key is configured. "
        "Start Ollama locally or set OPENAI_API_KEY / ANTHROPIC_API_KEY in .env"
    )


def ask_honeybadger(
    prompt: str,
    model: str = "general",
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    selected_model = switch_model(model)
    if not _local_model_check(selected_model):
        logger.warning(
            "Local model %s is not available; falling back to remote API.",
            selected_model,
        )
        return _fallback_to_api(prompt)

    messages = [
        {"role": "system", "content": HONEYBADGER_SYSTEM_PROMPT},
    ]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            _get_ollama_endpoint("v1/chat/completions"),
            json={"model": selected_model, "messages": messages},
            timeout=90,
        )
        response.raise_for_status()
        response.encoding = "utf-8"
        payload = response.json()

        content = ""
        choices = payload.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
        if not content:
            content = payload.get("response", "")

        return content.strip()
    except (ConnectionError, RequestException, Timeout) as exc:
        logger.warning("Ollama request failed; falling back to API: %s", exc)
        return _fallback_to_api(prompt)


def stream_response(prompt: str, model: str = "general") -> Generator[str, None, None]:
    selected_model = switch_model(model)
    messages = [
        {"role": "system", "content": HONEYBADGER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        with requests.post(
            _get_ollama_endpoint("v1/chat/completions"),
            json={"model": selected_model, "messages": messages, "stream": True},
            stream=True,
            timeout=180,
        ) as response:
            response.raise_for_status()
            for line_bytes in response.iter_lines():
                line = line_bytes.decode("utf-8", errors="replace") if isinstance(line_bytes, bytes) else line_bytes
                if not line:
                    continue

                text = line.strip()
                if text.startswith("data:"):
                    data = text[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = event.get("choices", [{}])[0].get("delta", {})
                    chunk = delta.get("content", "")
                    if chunk:
                        yield chunk
    except (ConnectionError, RequestException, Timeout) as exc:
        logger.warning("Ollama streaming request failed; falling back to API: %s", exc)
        try:
            fallback_response = _fallback_to_api(prompt)
            if fallback_response:
                yield fallback_response
        except RuntimeError:
            raise

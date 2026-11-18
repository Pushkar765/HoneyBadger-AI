import logging
from pathlib import Path
from typing import Dict, Optional

from honeybadger.brain.ollama_brain import ask_honeybadger

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent / "apps"
APP_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.lower())
    return safe.strip("-")[:120]


def _extract_code_blocks(text: str) -> Dict[str, str]:
    blocks: Dict[str, str] = {}
    current_lang: Optional[str] = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.strip().startswith("```"):
            if current_lang is None:
                current_lang = line.strip().lstrip("`") or "txt"
                current_lines = []
            else:
                blocks[current_lang] = "\n".join(current_lines).strip()
                current_lang = None
                current_lines = []
            continue
        if current_lang is not None:
            current_lines.append(line)

    return blocks


def build_app(description: str, app_name: Optional[str] = None) -> Path:
    app_name = app_name or f"app-{_slugify(description)}"
    app_path = APP_DIR / app_name
    app_path.mkdir(parents=True, exist_ok=True)

    prompt = (
        "Write a small local web application using Python, HTML, and JavaScript based on the description below. "
        "Include a backend file, a frontend HTML file, and any necessary JS. "
        "Keep the output concise and save the code to disk.\n"
        f"Description: {description}"
    )
    response = ask_honeybadger(prompt, model="coding")

    code_blocks = _extract_code_blocks(response)
    if not code_blocks:
        output_file = app_path / "app_spec.txt"
        output_file.write_text(response, encoding="utf-8")
        logger.warning("No code blocks were found; saved full response to %s", output_file)
        return app_path

    for lang, content in code_blocks.items():
        filename = {
            "python": "app.py",
            "py": "app.py",
            "html": "index.html",
            "javascript": "app.js",
            "js": "app.js",
            "css": "styles.css",
        }.get(lang.lower(), f"code.{lang}")
        file_path = app_path / filename
        file_path.write_text(content, encoding="utf-8")
        logger.info("Saved %s to %s", filename, file_path)

    return app_path

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from duckduckgo_search import DDGS

from honeybadger.brain.ollama_brain import ask_honeybadger

logger = logging.getLogger(__name__)

LESSONS_DIR = Path(__file__).resolve().parent / "lessons"
LESSONS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.lower())
    return safe.strip("-")[:120]


def teach(topic: str, level: str = "beginner") -> Path:
    prompt = (
        "Create a structured lesson plan for the topic below. "
        "Include objectives, a learning path, key concepts, and practice steps. "
        f"Target level: {level}."
        f"\nTopic: {topic}"
    )
    lesson_text = ask_honeybadger(prompt, model="reasoning")
    lesson_filename = LESSONS_DIR / f"lesson-{_slugify(topic)}-{level}.md"
    lesson_md = f"# Lesson: {topic}\n\n" + lesson_text.strip() + "\n"

    with open(lesson_filename, "w", encoding="utf-8") as fh:
        fh.write(lesson_md)

    logger.info("Saved lesson plan to %s", lesson_filename)
    return lesson_filename


def deep_research(topic: str, max_results: int = 5) -> str:
    with DDGS() as ddgs:
        search_results = ddgs.text(topic, max_results=max_results)

    if not search_results:
        raise RuntimeError("DuckDuckGo search returned no results.")

    snippets: List[str] = []
    for result in search_results[:max_results]:
        title = result.get("title") or ""
        snippet = result.get("body") or result.get("snippet") or ""
        if title or snippet:
            snippets.append(f"Title: {title}\nSnippet: {snippet}")

    summary_prompt = (
        "Summarize the following research findings in a concise and useful way. "
        "Provide the key concepts, practical takeaways, and what is most important.\n\n"
        f"Topic: {topic}\n\n"
        "Research snippets:\n"
        + "\n\n".join(snippets)
    )

    return ask_honeybadger(summary_prompt, model="reasoning")

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from honeybadger.brain.ollama_brain import ask_honeybadger

logger = logging.getLogger(__name__)

analyzer = SentimentIntensityAnalyzer()

EMPATHY_PROMPT_TEMPLATE = (
    "You are HoneyBadger, an emotionally intelligent companion. "
    "The user is feeling {mood}. "
    "Respond with empathy, warmth, and concise guidance. "
    "Do not suggest system actions without asking first.\n"
    "User message: {message}"
)


def detect_user_emotion(
    text: str,
    voice_data: Optional[bytes] = None,
    face_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    vader_scores = analyzer.polarity_scores(text)
    compound = vader_scores.get("compound", 0.0)
    if compound >= 0.05:
        text_mood = "positive"
    elif compound <= -0.05:
        text_mood = "negative"
    else:
        text_mood = "neutral"

    face_mood = face_data.get("emotion") if face_data else None
    voice_mood = None
    if voice_data:
        voice_mood = "calm" if len(voice_data) < 8000 else "alert"

    prompt = (
        "Analyze the following user state and return a short mood label: \n"
        f"Text: {text}\n"
        f"Text sentiment: {text_mood}\n"
        f"Face emotion: {face_mood or 'unknown'}\n"
        f"Voice tone: {voice_mood or 'unknown'}\n"
        "Only return a simple mood label like positive, worried, tired, hopeful, or concerned."
    )

    try:
        llm_response = ask_honeybadger(prompt, model="emotion")
        llm_mood = llm_response.strip().split("\n")[0]
    except Exception as exc:
        logger.warning("Emotion LLM analysis failed: %s", exc)
        llm_mood = text_mood

    mood = llm_mood or text_mood
    return {
        "text_mood": text_mood,
        "vader_scores": vader_scores,
        "face_mood": face_mood,
        "voice_mood": voice_mood,
        "llm_mood": mood,
    }


def respond_with_empathy(user_emotion: Any, message: str) -> str:
    mood = user_emotion if isinstance(user_emotion, str) else user_emotion.get("llm_mood", "neutral")
    prompt = EMPATHY_PROMPT_TEMPLATE.format(mood=mood, message=message)
    return ask_honeybadger(prompt, model="emotion")

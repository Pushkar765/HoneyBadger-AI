"""HoneyBadger voice module — speech-to-text and text-to-speech."""

from .voice import VoiceListener
from .tts import speak, TTSWorker, EdgeTTSWorker, DEFAULT_VOICE

__all__ = ["VoiceListener", "speak", "TTSWorker", "EdgeTTSWorker", "DEFAULT_VOICE"]

"""Text-to-speech with Microsoft Neural Voices (edge-tts).

Uses edge-tts for high-quality, natural-sounding neural voices — the same
engine that powers Microsoft Edge's "Read Aloud" feature.  Falls back to
pyttsx3 (Windows SAPI) if edge-tts is unavailable or offline.

Runs speech synthesis in a background QThread so the UI never blocks.
"""

import asyncio
import logging
import os
import tempfile
import uuid
from typing import Optional

from PySide6 import QtCore, QtMultimedia

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------

_EDGE_TTS_AVAILABLE = True
try:
    import edge_tts
except ImportError:
    _EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts is not installed — falling back to pyttsx3.")

_PYTTSX3_AVAILABLE = True
try:
    import pyttsx3
except ImportError:
    _PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 is not installed — legacy TTS fallback unavailable.")

# ---------------------------------------------------------------------------
# Curated Neural Voice Catalog
# ---------------------------------------------------------------------------
# Each entry: (voice_id, display_name, gender, description)
# These are the best-sounding Edge neural voices for an AI assistant.

NEURAL_VOICES: list[dict] = [
    {
        "id": "en-US-AndrewNeural",
        "name": "Andrew (US)",
        "gender": "Male",
        "desc": "Warm, confident — great for a trustworthy assistant",
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (US)",
        "gender": "Male",
        "desc": "Professional, authoritative tone",
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan (UK)",
        "gender": "Male",
        "desc": "Deep British voice — JARVIS-like",
    },
    {
        "id": "en-US-AndrewMultilingualNeural",
        "name": "Andrew Multilingual (US)",
        "gender": "Male",
        "desc": "Andrew with broader accent versatility",
    },
    {
        "id": "en-US-AriaNeural",
        "name": "Aria (US)",
        "gender": "Female",
        "desc": "Clear, articulate — modern AI assistant",
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (US)",
        "gender": "Female",
        "desc": "Friendly, natural conversational voice",
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia (UK)",
        "gender": "Female",
        "desc": "Refined British accent — elegant",
    },
    {
        "id": "en-US-DavisNeural",
        "name": "Davis (US)",
        "gender": "Male",
        "desc": "Calm, composed — great for narration",
    },
    {
        "id": "en-US-JasonNeural",
        "name": "Jason (US)",
        "gender": "Male",
        "desc": "Energetic, clear delivery",
    },
    {
        "id": "en-US-TonyNeural",
        "name": "Tony (US)",
        "gender": "Male",
        "desc": "Conversational, approachable",
    },
    {
        "id": "en-US-SaraNeural",
        "name": "Sara (US)",
        "gender": "Female",
        "desc": "Warm, professional female voice",
    },
    {
        "id": "en-AU-WilliamNeural",
        "name": "William (AU)",
        "gender": "Male",
        "desc": "Australian accent — adventurous feel",
    },
]

# Default voice for HoneyBadger — deep, confident, cyberpunk-appropriate
DEFAULT_VOICE = "en-GB-RyanNeural"
DEFAULT_PITCH = "-15Hz"   # slightly deeper for that cyberpunk gravitas
DEFAULT_RATE = "-5%"      # slightly slower, deliberate pacing


def get_available_voices() -> list[dict]:
    """Return a list of available TTS voices.

    Each entry is a dict with 'id', 'name', and 'gender' keys.
    When edge-tts is available, returns the curated neural voice list.
    Falls back to pyttsx3 system voices otherwise.
    """
    if _EDGE_TTS_AVAILABLE:
        return NEURAL_VOICES

    # Fallback to pyttsx3 system voices
    if not _PYTTSX3_AVAILABLE:
        return []
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        result = []
        for v in voices:
            result.append({
                "id": v.id,
                "name": v.name,
                "gender": getattr(v, "gender", "Unknown"),
            })
        engine.stop()
        return result
    except Exception as exc:
        logger.error("Failed to enumerate TTS voices: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Edge-TTS Worker (Neural voices)
# ---------------------------------------------------------------------------


class EdgeTTSWorker(QtCore.QThread):
    """Synthesises speech using edge-tts in a background thread."""

    finished = QtCore.Signal()

    def __init__(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        pitch: str = DEFAULT_PITCH,
        rate: str = DEFAULT_RATE,
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.text = text
        self.voice = voice
        self.pitch = pitch
        self.rate = rate
        self._audio_file: Optional[str] = None
        self._player: Optional[QtMultimedia.QMediaPlayer] = None
        self._audio_output: Optional[QtMultimedia.QAudioOutput] = None

    def run(self) -> None:
        if not self.text.strip():
            self.finished.emit()
            return

        try:
            # Generate audio file via edge-tts (async → sync bridge)
            tmp_path = os.path.join(
                tempfile.gettempdir(), f"hb_tts_{uuid.uuid4().hex}.mp3"
            )
            asyncio.run(self._synthesize(tmp_path))
            self._audio_file = tmp_path
            logger.info("Edge-TTS audio generated: %s (voice=%s)", tmp_path, self.voice)
        except Exception as exc:
            logger.error("Edge-TTS synthesis failed: %s — falling back to pyttsx3", exc)
            self._fallback_speak()
            return

        # Playback happens via signal to the main thread
        # (QMediaPlayer must be used from the main thread)
        # We'll use a simple blocking approach with the finished signal
        try:
            self._play_audio_blocking(self._audio_file)
        except Exception as exc:
            logger.error("Audio playback failed: %s", exc)
        finally:
            # Cleanup temp file
            try:
                if self._audio_file and os.path.exists(self._audio_file):
                    os.remove(self._audio_file)
            except OSError:
                pass
            self.finished.emit()

    async def _synthesize(self, output_path: str) -> None:
        """Run edge-tts synthesis."""
        communicate = edge_tts.Communicate(
            self.text,
            self.voice,
            pitch=self.pitch,
            rate=self.rate,
        )
        await communicate.save(output_path)

    def _play_audio_blocking(self, file_path: str) -> None:
        """Play the mp3 file. Uses Windows MCI (built-in, zero-dependency)."""
        import sys

        if sys.platform == "win32":
            try:
                self._play_via_mci(file_path)
                return
            except Exception as exc:
                logger.debug("MCI playback failed: %s", exc)

        # Try pygame if available
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            return
        except ImportError:
            pass
        except Exception as exc:
            logger.debug("pygame playback failed: %s", exc)

        # Last resort: playsound
        try:
            from playsound import playsound
            playsound(file_path)
            return
        except ImportError:
            pass
        except Exception as exc:
            logger.debug("playsound playback failed: %s", exc)

        logger.warning(
            "No audio playback method available on this platform."
        )

    @staticmethod
    def _play_via_mci(file_path: str) -> None:
        """Play an MP3 using Windows MCI (Media Control Interface).

        This is built into every Windows installation via winmm.dll and
        supports MP3 playback natively — no third-party libraries needed.
        """
        import ctypes
        import time

        winmm = ctypes.windll.winmm  # type: ignore[attr-defined]

        # Normalise path (MCI needs backslashes, quoted)
        path = file_path.replace("/", "\\")
        alias = "hb_tts_player"

        def mci_send(command: str) -> str:
            buf = ctypes.create_unicode_buffer(256)
            err = winmm.mciSendStringW(command, buf, 255, 0)
            if err:
                err_buf = ctypes.create_unicode_buffer(256)
                winmm.mciGetErrorStringW(err, err_buf, 255)
                raise RuntimeError(f"MCI error {err}: {err_buf.value}")
            return buf.value

        try:
            mci_send(f'open "{path}" type mpegvideo alias {alias}')
            mci_send(f"play {alias}")

            # Poll until playback finishes
            while True:
                status = mci_send(f"status {alias} mode")
                if status.lower() != "playing":
                    break
                time.sleep(0.1)
        finally:
            try:
                mci_send(f"close {alias}")
            except Exception:
                pass

    def _fallback_speak(self) -> None:
        """Fall back to pyttsx3 if edge-tts fails."""
        if not _PYTTSX3_AVAILABLE:
            logger.error("No TTS backend available (both edge-tts and pyttsx3 failed)")
            self.finished.emit()
            return
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 0.9)
            engine.say(self.text)
            engine.runAndWait()
            engine.stop()
        except Exception as exc:
            logger.error("pyttsx3 fallback also failed: %s", exc)
        finally:
            self.finished.emit()


# ---------------------------------------------------------------------------
# Legacy pyttsx3 Worker (kept as fallback)
# ---------------------------------------------------------------------------


class TTSWorker(QtCore.QThread):
    """Speaks a piece of text in a background thread using pyttsx3."""

    finished = QtCore.Signal()

    def __init__(
        self,
        text: str,
        rate: int = 165,
        volume: float = 0.9,
        voice_id: Optional[str] = None,
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.text = text
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id

    def run(self) -> None:
        if not _PYTTSX3_AVAILABLE or not self.text.strip():
            self.finished.emit()
            return

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            if self.voice_id:
                engine.setProperty("voice", self.voice_id)
            engine.say(self.text)
            engine.runAndWait()
            engine.stop()
        except Exception as exc:
            logger.error("TTS engine error: %s", exc)
        finally:
            self.finished.emit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def speak(
    text: str,
    rate: str = DEFAULT_RATE,
    volume: float = 0.9,
    voice_id: Optional[str] = None,
    pitch: str = DEFAULT_PITCH,
) -> Optional[QtCore.QThread]:
    """Fire-and-forget: speak *text* in a background thread.

    Uses edge-tts neural voices when available, falls back to pyttsx3.
    Returns the worker so the caller can connect to ``finished`` if needed,
    or ``None`` if TTS is unavailable.
    """
    if _EDGE_TTS_AVAILABLE:
        voice = voice_id or DEFAULT_VOICE
        worker = EdgeTTSWorker(
            text,
            voice=voice,
            pitch=pitch,
            rate=rate,
        )
        worker.start()
        return worker

    # Fallback to pyttsx3
    if not _PYTTSX3_AVAILABLE:
        return None
    worker = TTSWorker(text, rate=165, volume=volume, voice_id=voice_id)
    worker.start()
    return worker

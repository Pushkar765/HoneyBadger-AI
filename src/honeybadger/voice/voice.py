"""Vosk-based real-time speech-to-text listener.

Runs in a background QThread, captures microphone audio via ``sounddevice``,
and streams it through a Vosk recognizer.  Emits Qt signals for partial and
final transcriptions so the UI can react without blocking.

Improvements over the original
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
E1  Filler-word stripping  — "um", "uh", "like", repeated words removed.
E2  Contraction normalisation — "gonna"→"going to", "wanna"→"want to", etc.
E3  VAD energy gate         — silent blocks never reach Vosk (saves CPU & stops hallucinations).
E4  Adaptive end-of-speech  — waits for a configurable silence window before emitting final text.
E5  Wake-word listen window — after wake word, keeps listening for up to 8 s (no rush).
E6  Correction commands     — "cancel"/"never mind" recognised at transcription level.
E7  Confidence-gated UI     — short/low-confidence partials suppressed from the prompt box.

Model management
~~~~~~~~~~~~~~~~
On first use the small English model (~40 MB) is downloaded automatically
to ``<project>/configs/vosk-model/``.  After that no network access is needed.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import struct
import time
import zipfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

import numpy as np
from PySide6 import QtCore

from honeybadger.voice.voice_profile import VoiceProfileManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy / optional imports
# ---------------------------------------------------------------------------

_VOSK_AVAILABLE = True
try:
    from vosk import KaldiRecognizer, Model, SetLogLevel

    SetLogLevel(-1)
except ImportError:
    _VOSK_AVAILABLE = False
    logger.warning("vosk is not installed — voice input will be disabled.")

_SD_AVAILABLE = True
try:
    import sounddevice as sd
except ImportError:
    _SD_AVAILABLE = False
    logger.warning("sounddevice is not installed — voice input will be disabled.")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SAMPLE_RATE = 16000        # Vosk expects 16 kHz mono
_BLOCK_SIZE  = 4000         # ~250 ms chunks (smaller = more responsive VAD)
_MODEL_DIR_NAME = "vosk-model"
_MODEL_URL = (
    "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
)

# ── E3: VAD energy gate ───────────────────────────────────────────────────────
# RMS amplitude below this value = silence (int16, range 0–32768).
# Tweak upward in noisy environments; start at ~150 for a quiet office.
_SILENCE_RMS_THRESHOLD = 150

# ── E4: Adaptive end-of-speech window ────────────────────────────────────────
# How many consecutive silent blocks must pass before we declare the utterance
# finished and emit text_recognized.
# At _BLOCK_SIZE=4000 samples / 16 kHz → each block ≈ 250 ms.
# 8 blocks = ~2 000 ms of silence (2-second delay) → hands-free utterance boundary.
_SILENCE_BLOCKS_REQUIRED = 8

# ── E5: Wake-word listen window ───────────────────────────────────────────────
# Seconds we stay "active" after the wake word before timing out.
_WAKE_LISTEN_TIMEOUT_S = 8.0

# ── E7: Confidence gate ───────────────────────────────────────────────────────
# Minimum word count for a partial to be forwarded to the UI.
# Very short partials (single phoneme mis-fires) are suppressed.
_PARTIAL_MIN_WORDS = 2

# ── Wake-word alias list ──────────────────────────────────────────────────────
# Primary: "wakeup daddy's home" (and all Vosk phonetic mis-fires for it)
_DEFAULT_WAKE_PHRASES = (
    # ── Exact / near-exact ────────────────────────────────────────────────
    "wakeup daddy's home",
    "wake up daddy's home",
    "wakeup daddys home",
    "wake up daddys home",
    "wakeup daddy home",
    "wake up daddy home",
    # ── Common Vosk mis-fires for 'daddy' ─────────────────────────────────
    "wakeup daddies home",
    "wake up daddies home",
    "wakeup daddy's home",
    "wake up dad's home",
    "wakeup dads home",
    "wake up dads home",
    "wakeup dad home",
    "wake up dad home",
    # ── Common Vosk mis-fires for 'wakeup' ────────────────────────────────
    "wake daddy's home",
    "bacon daddy's home",
    "bake up daddy's home",
    "makeup daddy's home",
    "take up daddy's home",
    "lake up daddy's home",
    # ── Short-form fallbacks ───────────────────────────────────────────────
    "daddy's home",
    "daddys home",
    "daddy home",
    "dad's home",
    "dads home",
)

_FUZZY_THRESHOLD = 0.50

# ── E6: Correction / cancel phrases ──────────────────────────────────────────
# When the recognised text is purely one of these phrases, emit a special
# sentinel that the UI can intercept to cancel in-flight requests.
CORRECTION_SENTINEL = "__CANCEL__"

_CORRECTION_PHRASES = frozenset({
    "cancel",
    "never mind",
    "nevermind",
    "no wait",
    "stop",
    "ignore that",
    "forget it",
    "forget that",
    "abort",
    "undo",
    "go back",
    "delete that",
    "scratch that",
    "discard",
})

# ---------------------------------------------------------------------------
# E1 · Filler-word stripping
# ---------------------------------------------------------------------------

# Words that are almost always meaningless in a command context
_FILLER_WORDS: tuple[str, ...] = (
    "um", "uh", "uhh", "umm", "hmm", "hm", "er", "err",
    "ah", "ahh", "oh", "ehh",
    "like", "you know", "i mean", "i guess",
    "sort of", "kind of", "kinda", "sorta",
    "basically", "literally", "actually", "honestly",
    "right", "okay so", "okay",  "so",
    "well", "look", "listen", "alright",
)

# Build a single regex: whole-word match, case-insensitive
# We sort by length descending so multi-word fillers are matched first.
_filler_pattern = re.compile(
    r'\b(?:' + '|'.join(
        re.escape(f) for f in sorted(_FILLER_WORDS, key=len, reverse=True)
    ) + r')\b',
    re.IGNORECASE,
)

# Also collapse repeated consecutive identical words: "open open instagram" → "open instagram"
_repeated_word_pattern = re.compile(r'\b(\w+)( \1\b)+', re.IGNORECASE)


def _strip_fillers(text: str) -> str:
    """Remove filler words and deduplicate repeated words (E1)."""
    cleaned = _filler_pattern.sub(" ", text)
    cleaned = _repeated_word_pattern.sub(r'\1', cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned


# ---------------------------------------------------------------------------
# E2 · Contraction & casual speech normalisation
# ---------------------------------------------------------------------------

# (pattern, replacement) — applied left to right, regex aware
_CONTRACTIONS: list[tuple[str, str]] = [
    (r'\bgonna\b',    'going to'),
    (r'\bwanna\b',    'want to'),
    (r'\bgotta\b',    'got to'),
    (r'\blemme\b',    'let me'),
    (r'\bdunno\b',    "don't know"),
    (r'\bcould\'ve\b', 'could have'),
    (r'\bwould\'ve\b', 'would have'),
    (r'\bshould\'ve\b','should have'),
    (r'\bain\'t\b',   'is not'),
    (r'\byeah\b',     'yes'),
    (r'\byep\b',      'yes'),
    (r'\bnope\b',     'no'),
    (r'\bkinda\b',    'kind of'),
    (r'\bsorta\b',    'sort of'),
    (r'\bgimme\b',    'give me'),
    (r'\bcause\b',    'because'),
    (r'\'cause\b',    'because'),
    (r'\bcos\b',      'because'),
    (r'\bu\b',        'you'),          # common STT artifact: "can u" → "can you"
    (r'\br\b',        'are'),
    (r'\bur\b',       'your'),
    (r'\bbtw\b',      'by the way'),
    (r'\bidk\b',      "I don't know"),
    (r'\bomg\b',      'oh my god'),
    (r'\bplz\b',      'please'),
    (r'\bpls\b',      'please'),
    (r'\bthx\b',      'thanks'),
    (r'\bty\b',       'thank you'),
]

_contraction_patterns: list[tuple[re.Pattern, str]] = [
    (re.compile(pat, re.IGNORECASE), repl)
    for pat, repl in _CONTRACTIONS
]


def _normalise_contractions(text: str) -> str:
    """Expand contractions and casual speech forms (E2)."""
    for pattern, replacement in _contraction_patterns:
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Combined post-processor
# ---------------------------------------------------------------------------


def clean_transcription(text: str) -> str:
    """
    Apply E1 (filler stripping) + E2 (contraction normalisation) to a raw
    Vosk transcription.  Returns the cleaned text, or '' if nothing useful
    remains after cleaning.
    """
    if not text:
        return ""
    text = _normalise_contractions(text)
    text = _strip_fillers(text)
    return text.strip()


# ---------------------------------------------------------------------------
# E3 · VAD energy gate
# ---------------------------------------------------------------------------


def _rms_energy(raw_bytes: bytes) -> float:
    """
    Calculate the root-mean-square energy of a block of int16 PCM audio.
    Returns a value in the range [0, 32768].
    """
    num_samples = len(raw_bytes) // 2
    if num_samples == 0:
        return 0.0
    samples = struct.unpack_from(f"<{num_samples}h", raw_bytes)
    mean_sq = sum(s * s for s in samples) / num_samples
    return mean_sq ** 0.5


def _is_silent(raw_bytes: bytes, threshold: float = _SILENCE_RMS_THRESHOLD) -> bool:
    """Return True if the audio block is below the silence threshold (E3)."""
    return _rms_energy(raw_bytes) < threshold


# ---------------------------------------------------------------------------
# Wake-word matching helpers
# ---------------------------------------------------------------------------


def _fuzzy_match(text: str, target: str) -> bool:
    return SequenceMatcher(None, text, target).ratio() >= _FUZZY_THRESHOLD


def _find_wake_phrase(text: str, custom_wake: str) -> tuple[bool, int]:
    """Search *text* for any known wake phrase (exact or fuzzy).

    Returns ``(found, end_index)`` where *end_index* is the position in
    *text* right after the matched wake phrase so the caller can extract
    the command portion.
    """
    lower = text.lower()

    all_phrases = (*_DEFAULT_WAKE_PHRASES, custom_wake)
    for phrase in all_phrases:
        if phrase in lower:
            idx = lower.find(phrase) + len(phrase)
            return True, idx

    words = lower.split()
    primary_targets = ("hey badger", custom_wake)
    for window_size in (2, 3):
        for i in range(len(words) - window_size + 1):
            window = " ".join(words[i : i + window_size])
            for target in primary_targets:
                if _fuzzy_match(window, target):
                    matched_words = words[: i + window_size]
                    char_pos = len(" ".join(matched_words))
                    if char_pos < len(lower):
                        char_pos += 1
                    logger.info(
                        "Fuzzy wake-word match: '%s' ≈ '%s' (ratio=%.2f)",
                        window,
                        target,
                        SequenceMatcher(None, window, target).ratio(),
                    )
                    return True, char_pos

    return False, 0


# ---------------------------------------------------------------------------
# Grammar builder for wake-word recognizer (Fix 1)
# ---------------------------------------------------------------------------


def _build_wake_grammar(custom_wake: str) -> str:
    """
    Build a Vosk grammar JSON array for the dedicated wake-word recognizer.

    Using a grammar-constrained KaldiRecognizer restricts Vosk to choosing
    only from these phrases, which dramatically improves wake-word recall —
    especially when the small model would otherwise pick statistically-likely
    but irrelevant words (e.g. 'battered' instead of 'badger').

    The '[unk]' token absorbs non-wake speech gracefully so the recognizer
    does not hallucinate wake phrases out of background noise.
    """
    phrases: list[str] = list(_DEFAULT_WAKE_PHRASES)
    if custom_wake and custom_wake not in phrases:
        phrases.append(custom_wake)
    # De-duplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for p in phrases:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    # [unk] catches non-wake audio so Vosk doesn't force-fit it to a phrase
    unique.append("[unk]")
    return json.dumps(unique)


# ---------------------------------------------------------------------------
# E6 · Correction-phrase detection
# ---------------------------------------------------------------------------


def _is_correction(text: str) -> bool:
    """Return True if the entire utterance is a correction/cancel phrase."""
    return text.lower().strip() in _CORRECTION_PHRASES


# ---------------------------------------------------------------------------
# Model download helper
# ---------------------------------------------------------------------------


def _default_model_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "configs" / _MODEL_DIR_NAME


def ensure_model(model_dir: Optional[Path] = None) -> Path:
    """Make sure a Vosk model folder exists.  Download if missing."""
    if model_dir is None:
        model_dir = _default_model_dir()
    model_dir = Path(model_dir)

    if model_dir.exists() and any(model_dir.iterdir()):
        return model_dir

    logger.info("Vosk model not found at %s — downloading …", model_dir)
    model_dir.parent.mkdir(parents=True, exist_ok=True)

    import requests

    zip_path = model_dir.parent / "vosk-model-download.zip"
    try:
        resp = requests.get(_MODEL_URL, stream=True, timeout=120)
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                f.write(chunk)

        with zipfile.ZipFile(zip_path, "r") as zf:
            extract_tmp = model_dir.parent / "_vosk_extract_tmp"
            zf.extractall(extract_tmp)

        extracted_dirs = [p for p in extract_tmp.iterdir() if p.is_dir()]
        source = extracted_dirs[0] if extracted_dirs else extract_tmp

        if model_dir.exists():
            import shutil
            shutil.rmtree(model_dir)
        source.rename(model_dir)

        if extract_tmp.exists():
            import shutil
            shutil.rmtree(extract_tmp, ignore_errors=True)
        zip_path.unlink(missing_ok=True)

        logger.info("Vosk model downloaded to %s", model_dir)
    except Exception as exc:
        logger.error("Failed to download Vosk model: %s", exc)
        zip_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Could not download Vosk model from {_MODEL_URL}. "
            "Please download it manually and extract to "
            f"{model_dir}. Error: {exc}"
        ) from exc

    return model_dir


# ---------------------------------------------------------------------------
# Microphone availability check
# ---------------------------------------------------------------------------


def is_mic_available() -> bool:
    if not _SD_AVAILABLE:
        return False
    try:
        devices = sd.query_devices()
        for i in range(len(devices)):
            d = sd.query_devices(i)
            if d.get("max_input_channels", 0) > 0:
                return True
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# VoiceListener — QThread that streams mic → Vosk
# ---------------------------------------------------------------------------


class VoiceListener(QtCore.QThread):
    """Background listener that converts speech to text.

    Signals
    -------
    text_recognized : str
        Emitted when a final transcription is ready.
        Special value ``CORRECTION_SENTINEL`` signals a cancel intent.
    partial_text : str
        Emitted with live partial transcription text (E7: confidence gated).
    listening_started : (no args)
        Emitted when the listener begins capturing audio.
    listening_stopped : (no args)
        Emitted when the listener stops capturing audio.
    error_occurred : str
        Emitted on fatal errors (model missing, no mic, etc.).

    Improvements applied
    --------------------
    E1  Filler-word stripping on every final result.
    E2  Contraction normalisation on every final result.
    E3  VAD gate: silent audio blocks are discarded before Vosk sees them.
    E4  Adaptive end-of-speech: waits for _SILENCE_BLOCKS_REQUIRED consecutive
        silent blocks before emitting the accumulated text.
    E5  Wake-word listen window: after wake word, listener stays active for
        _WAKE_LISTEN_TIMEOUT_S seconds without requiring immediate speech.
    E6  Correction detection: cancel phrases emit CORRECTION_SENTINEL.
    E7  Partials shorter than _PARTIAL_MIN_WORDS words are suppressed.
    """

    text_recognized = QtCore.Signal(str)
    partial_text = QtCore.Signal(str)
    listening_started = QtCore.Signal()
    listening_stopped = QtCore.Signal()
    error_occurred = QtCore.Signal(str)
    voice_verified = QtCore.Signal(bool, float)

    def __init__(
        self,
        wake_word: str = "hey badger",
        always_on: bool = False,
        model_path: Optional[str] = None,
        parent: Optional[QtCore.QObject] = None,
        silence_threshold: float = _SILENCE_RMS_THRESHOLD,
        silence_blocks: int = _SILENCE_BLOCKS_REQUIRED,
        wake_listen_timeout: float = _WAKE_LISTEN_TIMEOUT_S,
    ) -> None:
        super().__init__(parent)
        self._wake_word = wake_word.lower().strip()
        self._always_on = always_on
        self._model_path = model_path
        self._running = False
        self._audio_queue: queue.Queue[bytes] = queue.Queue()

        # E3 / E4 tuning
        self._silence_threshold = silence_threshold
        self._silence_blocks = silence_blocks

        # E5 tuning
        self._wake_listen_timeout = wake_listen_timeout

        # Fix 3: manual force-activate flag (thread-safe boolean assignment)
        self._force_activate: bool = False

        # Voice Profile gating
        self.profile_manager = VoiceProfileManager()
        self.voice_similarity_threshold = 0.78
        self._rolling_audio_buffer: list[bytes] = []

    # -- public API ----------------------------------------------------------

    @property
    def is_listening(self) -> bool:
        return self._running

    def stop_listening(self) -> None:
        self._running = False

    def force_activate(self) -> None:
        """
        Bypass wake-word detection and immediately open the command-listening
        window.  Safe to call from any thread (boolean assignment is atomic
        under the GIL).  The audio loop picks up the flag on its next
        iteration and transitions to active-transcription mode.
        """
        self._force_activate = True

    def set_always_on(self, enabled: bool) -> None:
        self._always_on = enabled

    def set_wake_word(self, word: str) -> None:
        self._wake_word = word.lower().strip()

    # -- internals -----------------------------------------------------------

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            logger.debug("sounddevice status: %s", status)
        self._audio_queue.put(bytes(indata))

    def _emit_if_valid(self, text: str) -> bool:
        """
        Clean, check, and emit a final transcription.
        Returns True if text was emitted (non-empty after cleaning).
        """
        cleaned = clean_transcription(text)
        if not cleaned:
            return False

        logger.info("[FINAL CLEANED] '%s' (raw: '%s')", cleaned, text)

        # E6: correction commands take priority
        if _is_correction(cleaned):
            logger.info("Correction phrase detected: '%s'", cleaned)
            self.text_recognized.emit(CORRECTION_SENTINEL)
            return True

        self.text_recognized.emit(cleaned)
        return True

    def run(self) -> None:  # noqa: C901
        if not _VOSK_AVAILABLE:
            self.error_occurred.emit("Vosk is not installed. Run: pip install vosk")
            return
        if not _SD_AVAILABLE:
            self.error_occurred.emit("sounddevice is not installed. Run: pip install sounddevice")
            return
        if not is_mic_available():
            self.error_occurred.emit("No microphone detected. Please connect a microphone.")
            return

        try:
            model_dir = ensure_model(
                Path(self._model_path) if self._model_path else None
            )
        except RuntimeError as exc:
            self.error_occurred.emit(str(exc))
            return

        try:
            model = Model(str(model_dir))
        except Exception as exc:
            self.error_occurred.emit(f"Failed to load Vosk model: {exc}")
            return

        # ── Fix 1 & 2: Dual recogniser setup ─────────────────────────────────
        # wake_rec  → grammar-constrained: only knows wake phrases + [unk]
        #             Used while waiting for the wake word (always-on mode).
        # cmd_rec   → full language model: recognises arbitrary commands.
        #             Used after wake detection, and always in push-to-talk mode.
        #
        # Keeping them separate means the cmd_rec NEVER sees wake-word audio,
        # so it starts completely clean when the command listening window opens.
        if self._always_on:
            wake_grammar = _build_wake_grammar(self._wake_word)
            wake_rec = KaldiRecognizer(model, _SAMPLE_RATE, wake_grammar)
            cmd_rec = KaldiRecognizer(model, _SAMPLE_RATE)
            cmd_rec.SetWords(False)
            active_rec = wake_rec       # start in wake-detection mode
        else:
            wake_rec = None
            cmd_rec = KaldiRecognizer(model, _SAMPLE_RATE)
            cmd_rec.SetWords(False)
            active_rec = cmd_rec        # push-to-talk: always command mode

        self._running = True
        self.listening_started.emit()
        logger.info(
            "VoiceListener started (always_on=%s, wake_word='%s')",
            self._always_on,
            self._wake_word,
        )

        # ── State machine ────────────────────────────────────────────────────
        wake_active = not self._always_on   # True in push-to-talk, False in always-on
        accumulated_text = ""
        silent_block_count = 0
        speech_detected_this_phrase = False
        wake_activated_at: float = 0.0

        def _verify_speaker() -> bool:
            if not self.profile_manager.is_enrolled():
                self.voice_verified.emit(True, 1.0)
                return True
            if not self._rolling_audio_buffer:
                self.voice_verified.emit(False, 0.0)
                return False
            try:
                audio_bytes = b"".join(self._rolling_audio_buffer)
                y = np.frombuffer(audio_bytes, dtype=np.int16)
                sim = self.profile_manager.score(y)
                logger.info("[VoiceProfile] Speaker similarity: %.4f (threshold: %.4f)", sim, self.voice_similarity_threshold)
                verified = sim >= self.voice_similarity_threshold
                self.voice_verified.emit(verified, sim)
                self._rolling_audio_buffer.clear()
                return verified
            except Exception as e:
                logger.error("Error verifying speaker: %s", e)
                self.voice_verified.emit(True, 1.0)
                return True

        def _open_listen_window() -> None:
            """Transition from wake-detection → command-listening."""
            nonlocal wake_active, wake_activated_at, active_rec
            nonlocal accumulated_text, silent_block_count, speech_detected_this_phrase
            wake_active = True
            wake_activated_at = time.monotonic()
            # Fix 2: create a fresh cmd_rec — zero contamination from wake audio
            fresh_cmd = KaldiRecognizer(model, _SAMPLE_RATE)
            fresh_cmd.SetWords(False)
            active_rec = fresh_cmd
            accumulated_text = ""
            silent_block_count = 0
            speech_detected_this_phrase = False
            logger.info("Wake word confirmed — listening window open (%s s)", self._wake_listen_timeout)
            self.partial_text.emit("Listening…")
            self._rolling_audio_buffer.clear()

        def _reset_to_wake_mode() -> None:
            """Transition from command-listening back to wake-detection."""
            nonlocal wake_active, wake_activated_at, active_rec
            nonlocal accumulated_text, silent_block_count, speech_detected_this_phrase
            wake_active = False
            wake_activated_at = 0.0
            active_rec = wake_rec       # back to grammar-constrained recogniser
            accumulated_text = ""
            silent_block_count = 0
            speech_detected_this_phrase = False
            self.partial_text.emit("")  # clear prompt box
            self._rolling_audio_buffer.clear()

        try:
            with sd.RawInputStream(
                samplerate=_SAMPLE_RATE,
                blocksize=_BLOCK_SIZE,
                dtype="int16",
                channels=1,
                callback=self._audio_callback,
            ):
                while self._running:
                    # ── Fix 3: honour force_activate flag ────────────────────
                    if self._force_activate:
                        self._force_activate = False
                        if not wake_active:
                            _open_listen_window()

                    try:
                        data = self._audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        # E5: wake-word listen-window timeout
                        if self._always_on and wake_active and wake_activated_at > 0:
                            elapsed = time.monotonic() - wake_activated_at
                            if elapsed > self._wake_listen_timeout:
                                logger.info("Listen window timed out (%.1f s)", elapsed)
                                _reset_to_wake_mode()
                        continue

                    # Maintain rolling buffer for speaker verification during wake-scan phase
                    if not wake_active:
                        self._rolling_audio_buffer.append(data)
                        if len(self._rolling_audio_buffer) > 10:
                            self._rolling_audio_buffer.pop(0)

                    # ── E3: VAD energy gate ───────────────────────────────────
                    block_silent = _is_silent(data, self._silence_threshold)

                    if block_silent:
                        silent_block_count += 1

                        # ── E4: adaptive end-of-speech ───────────────────────
                        if (
                            speech_detected_this_phrase
                            and silent_block_count >= self._silence_blocks
                            and wake_active
                        ):
                            # Fix 4: flush uses active_rec (the correct cmd_rec,
                            # not a stale reference from before wake-detection).
                            flush_rec = active_rec
                            flush_rec.FinalResult()  # force Vosk to close the utterance
                            final_result = json.loads(flush_rec.Result())
                            extra_text = final_result.get("text", "").strip()
                            merged = f"{accumulated_text} {extra_text}".strip() if extra_text else accumulated_text

                            if merged:
                                # Strip residual wake-phrase noise (safety net)
                                if self._always_on:
                                    found, end_idx = _find_wake_phrase(merged, self._wake_word)
                                    if found:
                                        merged = merged[end_idx:].strip()
                                if merged:
                                    self._emit_if_valid(merged)

                            if self._always_on:
                                _reset_to_wake_mode()
                            else:
                                # push-to-talk: just reset phrase state, keep active
                                accumulated_text = ""
                                speech_detected_this_phrase = False
                                silent_block_count = 0
                                active_rec = KaldiRecognizer(model, _SAMPLE_RATE)
                                active_rec.SetWords(False)

                        # Silent blocks never reach Vosk (E3)
                        continue

                    # ── Non-silent block ─────────────────────────────────────
                    silent_block_count = 0

                    # ── Always-on: wake-scan phase ───────────────────────────
                    if self._always_on and not wake_active:
                        if active_rec.AcceptWaveform(data):
                            result = json.loads(active_rec.Result())
                            text = result.get("text", "").strip()
                            # Grammar recogniser may return "[unk]" for non-wake audio
                            if text and text != "[unk]":
                                logger.info("[WAKE SCAN FINAL] '%s'", text)
                                found, end_idx = _find_wake_phrase(text, self._wake_word)
                                if found:
                                    if _verify_speaker():
                                        command_part = text[end_idx:].strip()
                                        if command_part and command_part != "[unk]":
                                            # Wake word + inline command in one breath
                                            _open_listen_window()
                                            self._emit_if_valid(command_part)
                                            if self._always_on:
                                                _reset_to_wake_mode()
                                        else:
                                            _open_listen_window()
                                    else:
                                        logger.warning("[VoiceProfile] Wake word final rejected: Speaker mismatch")
                                        _reset_to_wake_mode()
                        else:
                            partial = json.loads(active_rec.PartialResult())
                            partial_text = partial.get("partial", "").strip()
                            if partial_text and partial_text != "[unk]":
                                found, _ = _find_wake_phrase(partial_text, self._wake_word)
                                if found:
                                    logger.info("[WAKE SCAN PARTIAL] '%s'", partial_text)
                                    if _verify_speaker():
                                        _open_listen_window()
                                    else:
                                        logger.warning("[VoiceProfile] Wake word partial rejected: Speaker mismatch")
                                        _reset_to_wake_mode()
                        continue  # don't fall through to active-transcription

                    # ── Active transcription (wake_active=True or push-to-talk) ─
                    speech_detected_this_phrase = True

                    if active_rec.AcceptWaveform(data):
                        result = json.loads(active_rec.Result())
                        text = result.get("text", "").strip()
                        if text:
                            logger.info("[CMD INTERIM] '%s'", text)
                            accumulated_text = f"{accumulated_text} {text}".strip()
                    else:
                        partial = json.loads(active_rec.PartialResult())
                        partial_text_raw = partial.get("partial", "").strip()
                        if partial_text_raw:
                            # E7: suppress very short / noisy partials
                            if len(partial_text_raw.split()) >= _PARTIAL_MIN_WORDS:
                                cleaned_partial = clean_transcription(partial_text_raw)
                                if cleaned_partial:
                                    logger.debug("[CMD PARTIAL] '%s'", cleaned_partial)
                                    self.partial_text.emit(cleaned_partial)

        except Exception as exc:
            logger.error("VoiceListener error: %s", exc)
            self.error_occurred.emit(f"Voice listener error: {exc}")
        finally:
            self._running = False
            self.listening_stopped.emit()


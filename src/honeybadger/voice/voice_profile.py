"""Voice Profile Manager for speaker verification.

Extracts volume-independent MFCC features with frame-level energy-based VAD,
saves/loads user voice profiles, and runs verification scoring.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
import numpy as np
from scipy.fftpack import dct
from PySide6 import QtCore

logger = logging.getLogger(__name__)

# Try importing sounddevice for calibration recording
_SD_AVAILABLE = True
try:
    import sounddevice as sd
except ImportError:
    _SD_AVAILABLE = False


def extract_mfcc_features(
    y: np.ndarray,
    sr: int = 16000,
    n_fft: int = 512,
    hop_length: int = 160,
    win_length: int = 400,
    n_mels: int = 20,
    n_mfcc: int = 13
) -> np.ndarray:
    """Extract VAD-filtered, volume-independent MFCC features (MFCCs 1-12).

    Returns a 24-dimensional combined feature vector of mean and standard deviation.
    """
    # 1. Ensure float32 normalized signal
    if y.dtype == np.int16:
        y = y.astype(np.float32) / 32768.0

    # 2. Pre-emphasis
    y = np.append(y[0], y[1:] - 0.97 * y[:-1])

    # 3. Frame blocking and windowing
    frames = []
    for i in range(0, len(y) - win_length, hop_length):
        frame = y[i : i + win_length] * np.hamming(win_length)
        frames.append(frame)

    if not frames:
        return np.zeros(2 * (n_mfcc - 1), dtype=np.float32)

    frames = np.array(frames)

    # 4. Power Spectrum
    power_spectrum = np.abs(np.fft.rfft(frames, n=n_fft)) ** 2 / n_fft

    # 5. Mel Filterbank setup
    def hz_to_mel(hz: float) -> float:
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    def mel_to_hz(mel: float) -> float:
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    low_mel = hz_to_mel(0)
    high_mel = hz_to_mel(sr / 2)
    mel_pts = np.linspace(low_mel, high_mel, n_mels + 2)
    hz_pts = mel_to_hz(mel_pts)
    bin_pts = np.floor((n_fft + 1) * hz_pts / sr).astype(int)

    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for m in range(1, n_mels + 1):
        f_m_minus = bin_pts[m - 1]
        f_m = bin_pts[m]
        f_m_plus = bin_pts[m + 1]
        for k in range(f_m_minus, f_m):
            fb[m - 1, k] = (k - bin_pts[m - 1]) / (bin_pts[m] - bin_pts[m - 1])
        for k in range(f_m, f_m_plus):
            fb[m - 1, k] = (bin_pts[m + 1] - k) / (bin_pts[m + 1] - bin_pts[m])

    # 6. Apply filterbank and take log (numerical stability with eps)
    filter_energies = np.dot(power_spectrum, fb.T)
    filter_energies = np.where(filter_energies == 0, np.finfo(float).eps, filter_energies)
    log_filter_energies = 10.0 * np.log10(filter_energies)

    # 7. Discrete Cosine Transform (DCT)
    mfcc_coeffs = dct(log_filter_energies, type=2, axis=1, norm="ortho")[:, :n_mfcc]

    # 8. Frame-level energy VAD
    # MFCC index 0 represents the frame's log energy.
    log_energies = mfcc_coeffs[:, 0]
    max_energy = np.max(log_energies)
    # Filter frames that are within 20 dB of peak energy (i.e. exclude silence/noise)
    speech_frames = mfcc_coeffs[log_energies > (max_energy - 20.0)]

    if len(speech_frames) == 0:
        speech_frames = mfcc_coeffs

    # 9. Extract statistics dropping coefficient 0 (volume-independence)
    # speech_frames has shape (num_frames, n_mfcc)
    mfccs_subset = speech_frames[:, 1:]
    mean_vector = np.mean(mfccs_subset, axis=0)
    std_vector = np.std(mfccs_subset, axis=0)

    # Combine into a 24-dimensional profile vector
    return np.concatenate([mean_vector, std_vector])


class VoiceProfileManager:
    """Manages enrollment and speaker verification scoring for the user."""

    def __init__(self, profile_dir: Optional[Path] = None) -> None:
        if profile_dir is None:
            self.profile_dir = Path.home() / ".honeybadger" / "voice_profile"
        else:
            self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.profile_dir / "profile.npy"
        self._profile: Optional[np.ndarray] = None
        self.load_profile()

    def is_enrolled(self) -> bool:
        """Return True if a profile is currently loaded or exists on disk."""
        return self._profile is not None or self.profile_path.exists()

    def load_profile(self) -> None:
        """Attempt to load the speaker profile vector from disk."""
        if self.profile_path.exists():
            try:
                self._profile = np.load(self.profile_path)
                logger.info("Loaded voice profile from %s", self.profile_path)
            except Exception as exc:
                logger.error("Failed to load voice profile: %s", exc)
                self._profile = None
        else:
            self._profile = None

    def save_profile(self, profile_vector: np.ndarray) -> None:
        """Save the profile vector to disk and cache it in memory."""
        try:
            np.save(self.profile_path, profile_vector)
            self._profile = profile_vector
            logger.info("Saved voice profile to %s", self.profile_path)
        except Exception as exc:
            logger.error("Failed to save voice profile: %s", exc)

    def enroll(self, samples: List[np.ndarray], sr: int = 16000) -> None:
        """Extract features from multiple calibration samples and save their mean."""
        if not samples:
            raise ValueError("No enrollment samples provided.")

        features_list = []
        for sample in samples:
            feat = extract_mfcc_features(sample, sr)
            features_list.append(feat)

        mean_profile = np.mean(features_list, axis=0)
        self.save_profile(mean_profile)

    def score(self, y: np.ndarray, sr: int = 16000) -> float:
        """Score a live audio clip against the enrolled profile using Cosine Similarity.

        Returns a value in [-1.0, 1.0]. If not enrolled, returns 1.0 (graceful fallback).
        """
        if self._profile is None:
            self.load_profile()
            if self._profile is None:
                return 1.0  # fallback when not enrolled

        live_feat = extract_mfcc_features(y, sr)
        norm_profile = np.linalg.norm(self._profile)
        norm_live = np.linalg.norm(live_feat)

        if norm_profile == 0 or norm_live == 0:
            return 0.0

        similarity = np.dot(self._profile, live_feat) / (norm_profile * norm_live)
        return float(similarity)

    def clear_profile(self) -> None:
        """Delete the profile file from disk and clear from memory."""
        self._profile = None
        if self.profile_path.exists():
            try:
                self.profile_path.unlink()
                logger.info("Cleared voice profile file.")
            except Exception as exc:
                logger.error("Failed to clear voice profile: %s", exc)


class EnrollmentRecorder(QtCore.QThread):
    """QThread to handle recording training audio samples without blocking the main UI."""

    finished_sample = QtCore.Signal(np.ndarray)
    error_occurred = QtCore.Signal(str)

    def __init__(self, duration: float = 2.5, sr: int = 16000, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self.duration = duration
        self.sr = sr

    def run(self) -> None:
        if not _SD_AVAILABLE:
            self.error_occurred.emit("sounddevice is not installed.")
            return

        try:
            num_samples = int(self.duration * self.sr)
            # Record float32 mono channel audio
            recording = sd.rec(num_samples, samplerate=self.sr, channels=1, dtype="float32")
            sd.wait()  # wait until recording finishes in this background thread
            if recording is None or len(recording) == 0:
                raise RuntimeError("Recording captured no samples.")
            audio = recording.flatten()
            self.finished_sample.emit(audio)
        except Exception as exc:
            logger.error("Enrollment recording failed: %s", exc)
            self.error_occurred.emit(str(exc))

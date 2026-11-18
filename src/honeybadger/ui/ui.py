import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt
from PySide6.QtWidgets import QGraphicsOpacityEffect, QGraphicsDropShadowEffect
import psutil

from honeybadger.config import VOICE_ENABLED, WAKE_WORD, TTS_ENABLED, VOSK_MODEL_PATH
from honeybadger.voice.voice import VoiceListener, is_mic_available, CORRECTION_SENTINEL
from honeybadger.voice.voice_profile import VoiceProfileManager, EnrollmentRecorder
from honeybadger.voice.tts import speak, TTSWorker, get_available_voices, DEFAULT_VOICE
from honeybadger.tasks.executor import execute_powershell
from honeybadger.tasks.social_media import resolve_social_app, get_supported_apps
import re

logger = logging.getLogger(__name__)

# ─── Chat history persistence ─────────────────────────────────────────────────

HISTORY_DIR = Path.home() / ".honeybadger" / "chat_history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

MAX_SESSIONS = 50          # keep up to 50 sessions on disk
PREVIEW_CHARS = 60         # chars to show in sidebar list item


def _session_path(session_id: str) -> Path:
    return HISTORY_DIR / f"{session_id}.json"


def _load_all_sessions() -> list[dict]:
    """Return sessions sorted newest-first."""
    sessions = []
    for p in HISTORY_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            sessions.append(data)
        except Exception:
            pass
    sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    return sessions


def _save_session(session: dict) -> None:
    try:
        _session_path(session["id"]).write_text(
            json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        logger.warning("Could not save chat session: %s", exc)


def _delete_session(session_id: str) -> None:
    try:
        p = _session_path(session_id)
        if p.exists():
            p.unlink()
    except Exception as exc:
        logger.warning("Could not delete session %s: %s", session_id, exc)


# ─── Custom text input: Enter = send, Shift+Enter = newline ───────────────────

class PromptTextEdit(QtWidgets.QTextEdit):
    """
    Text input for HoneyBadger.

    Key behaviour:
      • Enter          → send (or stop push-to-talk recording if mic is active)
      • Shift + Enter  → insert newline
    """
    send_requested = QtCore.Signal()
    stop_mic_requested = QtCore.Signal()   # fired when Enter stops PTT recording

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter → always a newline
                super().keyPressEvent(event)
            else:
                # Route through stop_mic_requested so the UI can decide whether
                # to stop PTT recording first or just send directly.
                self.stop_mic_requested.emit()
        else:
            super().keyPressEvent(event)


# ─── Hardware monitor ─────────────────────────────────────────────────────────

def _read_vram_usage() -> str:
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        used = mem.used / 1024 ** 3
        total = mem.total / 1024 ** 3
        pynvml.nvmlShutdown()
        return f"{used:.1f} / {total:.1f} GB"
    except Exception:
        return "unknown"


class HardwareMonitorPanel(QtWidgets.QGroupBox):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__("Hardware Monitor", parent)
        self.setObjectName("monitorPanel")
        layout = QtWidgets.QGridLayout()

        self.ram_label = QtWidgets.QLabel("RAM: loading...")
        self.vram_label = QtWidgets.QLabel("VRAM: loading...")
        self.disk_label = QtWidgets.QLabel("Storage: loading...")
        self.model_label = QtWidgets.QLabel("Active model: idle")

        layout.addWidget(QtWidgets.QLabel("RAM Usage:"), 0, 0)
        layout.addWidget(self.ram_label, 0, 1)
        layout.addWidget(QtWidgets.QLabel("VRAM Usage:"), 1, 0)
        layout.addWidget(self.vram_label, 1, 1)
        layout.addWidget(QtWidgets.QLabel("Storage:"), 2, 0)
        layout.addWidget(self.disk_label, 2, 1)
        layout.addWidget(QtWidgets.QLabel("Current Model:"), 3, 0)
        layout.addWidget(self.model_label, 3, 1)

        self.setLayout(layout)

    def update_status(self, active_model: str) -> None:
        mem = psutil.virtual_memory()
        self.ram_label.setText(f"{mem.used / 1024**3:.1f} / {mem.total / 1024**3:.0f} GB")
        disk = shutil.disk_usage(Path.home())
        self.disk_label.setText(f"{disk.used / 1024**3:.0f} / {disk.total / 1024**3:.0f} GB")
        self.vram_label.setText(_read_vram_usage())
        self.model_label.setText(active_model)


class VoiceControlPanel(QtWidgets.QGroupBox):
    """Sidebar panel with voice mode selector, TTS toggle, voice picker, and status."""

    voice_mode_changed = QtCore.Signal(str)   # "off" | "push" | "always"
    tts_toggled = QtCore.Signal(bool)
    voice_changed = QtCore.Signal(str)  # voice id
    calibration_requested = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__("Voice Control", parent)
        self.setObjectName("voicePanel")
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)

        mode_label = QtWidgets.QLabel("Voice Mode")
        mode_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        layout.addWidget(mode_label)

        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.setObjectName("voiceModeCombo")
        self.mode_combo.addItems(["Off", "Push-to-Talk", "Always-On (Wake Word)"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_change)
        layout.addWidget(self.mode_combo)

        self.tts_check = QtWidgets.QCheckBox("Speak responses aloud")
        self.tts_check.setObjectName("ttsCheck")
        self.tts_check.setChecked(TTS_ENABLED)
        self.tts_check.toggled.connect(self.tts_toggled.emit)
        layout.addWidget(self.tts_check)

        voice_label = QtWidgets.QLabel("TTS Voice")
        voice_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        layout.addWidget(voice_label)

        self.voice_combo = QtWidgets.QComboBox()
        self.voice_combo.setObjectName("voiceSelectCombo")
        self._voice_ids: list[str] = []
        voices = get_available_voices()
        default_idx = 0
        for i, v in enumerate(voices):
            name = v["name"]
            desc = v.get("desc", "")
            gender = v.get("gender", "")
            if desc:
                label = f"{name} — {desc}"
            elif gender and gender != "Unknown":
                label = f"{name} ({gender})"
            else:
                label = name
            self.voice_combo.addItem(label)
            self._voice_ids.append(v["id"])
            if v["id"] == DEFAULT_VOICE:
                default_idx = i
        if not voices:
            self.voice_combo.addItem("No voices available")
            self.voice_combo.setEnabled(False)
        else:
            self.voice_combo.setCurrentIndex(default_idx)
        self.voice_combo.currentIndexChanged.connect(self._on_voice_change)
        layout.addWidget(self.voice_combo)

        self.calibrate_btn = QtWidgets.QPushButton("🎤 Calibrate Voice")
        self.calibrate_btn.setObjectName("calibrateVoiceBtn")
        self.calibrate_btn.clicked.connect(self.calibration_requested.emit)
        layout.addWidget(self.calibrate_btn)

        self.status_label = QtWidgets.QLabel("● Idle")
        self.status_label.setObjectName("voiceStatus")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def _on_mode_change(self, index: int) -> None:
        modes = ["off", "push", "always"]
        self.voice_mode_changed.emit(modes[index])

    def _on_voice_change(self, index: int) -> None:
        if 0 <= index < len(self._voice_ids):
            self.voice_changed.emit(self._voice_ids[index])

    def set_status(self, text: str, color: str = "#94a3b8") -> None:
        self.status_label.setText(f"● {text}")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px;")


# ─── Voice Calibration Dialog ─────────────────────────────────────────────────

class VoiceCalibrationDialog(QtWidgets.QDialog):
    """Wizard-like dialog guiding the user through recording 3 wake word samples."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Voice Calibration Wizard")
        self.setFixedSize(400, 320)
        self.setModal(True)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #f8fafc;
            }
            QLabel {
                color: #e2e8f0;
            }
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:disabled {
                background: #1e293b;
                color: #64748b;
            }
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 4px;
                text-align: center;
                background: #1e293b;
                color: #f8fafc;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
            }
        """)

        self.profile_manager = VoiceProfileManager()
        self.samples: list[np.ndarray] = []
        self.current_step = 1
        self.max_steps = 3
        self.recording_duration = 2.5
        self.sr = 16000
        
        self.recorder: Optional[EnrollmentRecorder] = None
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._on_countdown_tick)
        self.elapsed_ms = 0
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        self.title_label = QtWidgets.QLabel("Speaker Calibration")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(self.title_label)

        # Instructions
        self.inst_label = QtWidgets.QLabel(
            "Speak the wake phrase clearly into your microphone when recording starts.\n"
            "This builds your unique vocal envelope."
        )
        self.inst_label.setWordWrap(True)
        self.inst_label.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        layout.addWidget(self.inst_label)

        # Active prompt box (visual cue)
        self.prompt_box = QtWidgets.QFrame()
        self.prompt_box.setStyleSheet("background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px;")
        box_layout = QtWidgets.QVBoxLayout(self.prompt_box)
        box_layout.setContentsMargins(16, 16, 16, 16)
        
        self.status_label = QtWidgets.QLabel("Step 1 of 3: Ready")
        self.status_label.setStyleSheet("font-size: 13px; color: #3b82f6; font-weight: 600;")
        box_layout.addWidget(self.status_label)
        
        self.phrase_label = QtWidgets.QLabel('"Wakeup, daddy\'s home"')
        self.phrase_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc; margin-top: 5px;")
        self.phrase_label.setAlignment(Qt.AlignCenter)
        box_layout.addWidget(self.phrase_label)
        
        layout.addWidget(self.prompt_box)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Button row
        btn_layout = QtWidgets.QHBoxLayout()
        self.record_btn = QtWidgets.QPushButton("Start Recording")
        self.record_btn.clicked.connect(self._start_recording)
        btn_layout.addWidget(self.record_btn)

        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background: transparent; color: #94a3b8; border: 1px solid #334155; padding: 8px 16px; font-weight: 600; border-radius: 6px;")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _start_recording(self) -> None:
        self.record_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText(f"Step {self.current_step} of {self.max_steps}: RECORDING...")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: bold;")
        self.progress_bar.setValue(0)

        # Start background QThread recorder
        self.recorder = EnrollmentRecorder(duration=self.recording_duration, sr=self.sr, parent=self)
        self.recorder.finished_sample.connect(self._on_recording_finished)
        self.recorder.error_occurred.connect(self._on_recording_error)
        self.recorder.start()

        # Start countdown timer ticks (every 50ms)
        self.elapsed_ms = 0
        self.countdown_timer.start(50)

    def _on_countdown_tick(self) -> None:
        self.elapsed_ms += 50
        pct = int((self.elapsed_ms / (self.recording_duration * 1000.0)) * 100)
        self.progress_bar.setValue(min(pct, 100))

    def _on_recording_finished(self, sample: np.ndarray) -> None:
        self.countdown_timer.stop()
        self.progress_bar.setValue(100)
        self.samples.append(sample)
        
        if self.recorder:
            self.recorder.deleteLater()
            self.recorder = None

        if self.current_step < self.max_steps:
            self.current_step += 1
            self.status_label.setText(f"Step {self.current_step} of {self.max_steps}: Ready")
            self.status_label.setStyleSheet("color: #3b82f6; font-weight: 600;")
            self.record_btn.setText(f"Record Sample {self.current_step}")
            self.record_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
        else:
            self._process_calibration()

    def _on_recording_error(self, err_msg: str) -> None:
        self.countdown_timer.stop()
        self.progress_bar.setValue(0)
        QtWidgets.QMessageBox.critical(self, "Recording Error", f"Failed to record audio:\n{err_msg}")
        self.status_label.setText(f"Step {self.current_step} of {self.max_steps}: Ready")
        self.status_label.setStyleSheet("color: #3b82f6; font-weight: 600;")
        self.record_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        if self.recorder:
            self.recorder.deleteLater()
            self.recorder = None

    def _process_calibration(self) -> None:
        self.status_label.setText("Processing Voice Profile...")
        self.status_label.setStyleSheet("color: #e2e8f0; font-weight: 600;")
        self.repaint() # force visual update

        try:
            self.profile_manager.enroll(self.samples, self.sr)
            QtWidgets.QMessageBox.information(
                self, "Calibration Complete", 
                "Your user-specific voice profile has been successfully calibrated and saved.\n"
                "HoneyBadger will now verify your voice in always-on mode."
            )
            self.accept()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Calibration Failed", f"Error saving voice profile: {exc}")
            self.reject()


# ─── Chat History Panel ───────────────────────────────────────────────────────

class ChatHistoryPanel(QtWidgets.QGroupBox):
    """
    Sidebar panel listing past chat sessions. Emits session_selected(session_id)
    when the user clicks an entry, and new_chat_requested() when the + button
    is pressed.
    """
    session_selected = QtCore.Signal(str)   # session_id
    new_chat_requested = QtCore.Signal()
    session_deleted = QtCore.Signal(str)    # session_id

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__("Chat History", parent)
        self.setObjectName("historyPanel")
        self._active_id: Optional[str] = None

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(8, 14, 8, 8)

        # Header row: label + "New Chat" button
        header_row = QtWidgets.QHBoxLayout()
        new_btn = QtWidgets.QPushButton("＋ New Chat")
        new_btn.setObjectName("newChatBtn")
        new_btn.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        new_btn.clicked.connect(self.new_chat_requested.emit)
        header_row.addStretch()
        header_row.addWidget(new_btn)
        root.addLayout(header_row)

        # Scrollable list
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("historyScroll")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        self._list_widget = QtWidgets.QWidget()
        self._list_layout = QtWidgets.QVBoxLayout(self._list_widget)
        self._list_layout.setSpacing(3)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_widget)
        root.addWidget(scroll)

    def refresh(self, sessions: list[dict], active_id: Optional[str] = None) -> None:
        """Rebuild the list from the sessions data."""
        self._active_id = active_id
        # Clear existing items (keep the stretch at end)
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for session in sessions:
            sid = session.get("id", "")
            title = session.get("title", "New Chat")
            updated = session.get("updated_at", "")
            is_active = (sid == active_id)
            row = self._make_row(sid, title, updated, is_active)
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

    def _make_row(self, sid: str, title: str, updated: str, is_active: bool) -> QtWidgets.QWidget:
        row = QtWidgets.QWidget()
        row.setObjectName("historyRowActive" if is_active else "historyRow")
        row.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        row.setFixedHeight(52)

        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(10, 6, 6, 6)
        layout.setSpacing(6)

        text_col = QtWidgets.QVBoxLayout()
        text_col.setSpacing(2)

        title_lbl = QtWidgets.QLabel(title[:28] + ("…" if len(title) > 28 else ""))
        title_lbl.setStyleSheet(
            f"color: {'#ffffff' if is_active else '#e2e8f0'}; font-size: 13px; font-weight: {'700' if is_active else '500'};"
        )
        title_lbl.setWordWrap(False)

        # Format date nicely
        try:
            dt = datetime.fromisoformat(updated)
            date_str = dt.strftime("%b %d, %H:%M")
        except Exception:
            date_str = updated[:16] if updated else ""

        date_lbl = QtWidgets.QLabel(date_str)
        date_lbl.setStyleSheet("color: #64748b; font-size: 11px;")

        text_col.addWidget(title_lbl)
        text_col.addWidget(date_lbl)

        # Delete button
        del_btn = QtWidgets.QPushButton("🗑")
        del_btn.setObjectName("historyDeleteBtn")
        del_btn.setFixedSize(24, 24)
        del_btn.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        del_btn.setToolTip("Delete this session")
        del_btn.clicked.connect(lambda checked, s=sid: self.session_deleted.emit(s))

        layout.addLayout(text_col, 1)
        layout.addWidget(del_btn)

        # Make the row itself clickable (except the delete btn area)
        row.mousePressEvent = lambda event, s=sid: self.session_selected.emit(s)  # type: ignore[method-assign]
        return row

    def set_active(self, session_id: Optional[str]) -> None:
        self._active_id = session_id


# ─── Background worker ────────────────────────────────────────────────────────

class CommandWorker(QtCore.QThread):
    chunk_ready = QtCore.Signal(str)
    finished = QtCore.Signal()
    error = QtCore.Signal(str)

    def __init__(self, prompt: str, router: Any) -> None:
        super().__init__()
        self.prompt = prompt
        self.router = router

    def run(self) -> None:
        try:
            for chunk in self.router.stream_query(self.prompt):
                self.chunk_ready.emit(chunk)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


# ─── Thinking dots animation ──────────────────────────────────────────────────

class ThinkingLabel(QtWidgets.QLabel):
    _FRAMES = ["Thinking  ●○○", "Thinking  ○●○", "Thinking  ○○●", "Thinking  ○●○"]

    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setObjectName("thinkingLabel")
        self._frame = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._frame = 0
        self.setText(self._FRAMES[0])
        self.setVisible(True)
        self._timer.start(350)

    def stop(self):
        self._timer.stop()
        self.setVisible(False)
        self.setText("")

    def _tick(self):
        self._frame = (self._frame + 1) % len(self._FRAMES)
        self.setText(self._FRAMES[self._frame])


# ─── Main window ──────────────────────────────────────────────────────────────

class HoneyBadgerUI(QtWidgets.QMainWindow):
    def __init__(self, router: Any) -> None:
        super().__init__()
        self.router = router
        self.worker: Optional[CommandWorker] = None
        self.setWindowTitle("HoneyBadger - Cyberpunk Assistant")
        self.resize(1200, 720)

        # Voice state
        self._voice_mode = "off"
        self._tts_enabled = TTS_ENABLED
        self._tts_voice_id: Optional[str] = None
        self._voice_listener: Optional[VoiceListener] = None
        self._tts_worker: Optional[TTSWorker] = None
        self._mic_available = is_mic_available()
        self.pending_command: Optional[str] = None
        self._current_response_text = ""

        # ── Session state ──────────────────────────────────────────────────
        self._sessions: list[dict] = _load_all_sessions()
        self._current_session: dict = self._new_session()
        # Don't persist the blank session until first message is sent

        # Window fade-in
        self.setWindowOpacity(0.0)
        self.fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_anim.setDuration(800)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in_anim.start()

        self._setup_ui()
        self._apply_style()
        self._start_monitor()
        self._refresh_history()

    # ── Session helpers ────────────────────────────────────────────────────────

    def _new_session(self) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "title": "New Chat",
            "messages": [],          # list of {"role": "user"|"honeybadger", "text": str, "ts": str}
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _session_add_message(self, role: str, text: str) -> None:
        """Append a message to the current session and save."""
        self._current_session["messages"].append({
            "role": role,
            "text": text,
            "ts": datetime.now().isoformat(),
        })
        self._current_session["updated_at"] = datetime.now().isoformat()
        # Auto-title from first user message
        if role == "user" and self._current_session["title"] == "New Chat":
            self._current_session["title"] = text[:PREVIEW_CHARS].strip()
        _save_session(self._current_session)
        # Ensure it's in _sessions list (first save)
        ids = [s["id"] for s in self._sessions]
        if self._current_session["id"] not in ids:
            self._sessions.insert(0, self._current_session)
        else:
            # Update in place
            for i, s in enumerate(self._sessions):
                if s["id"] == self._current_session["id"]:
                    self._sessions[i] = self._current_session
                    break
        # Re-sort
        self._sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
        self._refresh_history()

    def _refresh_history(self) -> None:
        self.history_panel.refresh(self._sessions, self._current_session["id"])

    def _load_session(self, session_id: str) -> None:
        """Switch to an existing session."""
        for s in self._sessions:
            if s["id"] == session_id:
                self._current_session = s
                self._replay_session(s)
                self._refresh_history()
                return

    def _replay_session(self, session: dict) -> None:
        """Render all messages from a session into the response box."""
        self.response_box.clear()
        messages = session.get("messages", [])
        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            text = msg.get("text", "")
            if i > 0:
                self.response_box.append(
                    "<hr style='border: 1px solid rgba(255,255,255,0.05); margin: 20px 0;'>"
                )
            if role == "user":
                self.response_box.moveCursor(QtGui.QTextCursor.End)
                self.response_box.insertHtml(
                    f"<div style='margin-bottom: 10px;'>"
                    f"<b style='color: #a1a1aa; font-size: 15px;'>You</b><br>"
                    f"<span style='color: #ffffff;'>{text.replace(chr(10), '<br>')}</span>"
                    f"</div><br>"
                )
            else:
                self.response_box.moveCursor(QtGui.QTextCursor.End)
                self.response_box.insertHtml(
                    f"<b style='color: #ffffff; font-size: 15px;'>HoneyBadger</b><br>"
                )
                self.response_box.moveCursor(QtGui.QTextCursor.End)
                self.response_box.insertPlainText(text)
        self.response_box.moveCursor(QtGui.QTextCursor.End)

    def _on_new_chat(self) -> None:
        """Start a fresh session."""
        self._current_session = self._new_session()
        self.response_box.clear()
        self._refresh_history()

    def _on_session_deleted(self, session_id: str) -> None:
        _delete_session(session_id)
        self._sessions = [s for s in self._sessions if s["id"] != session_id]
        if self._current_session["id"] == session_id:
            self._on_new_chat()
        else:
            self._refresh_history()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ── Header ──
        header_widget = QtWidgets.QWidget()
        header_widget.setObjectName("headerWidget")
        header_widget.setFixedHeight(50)
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 0, 15, 0)

        self.toggle_btn = QtWidgets.QPushButton("☰")
        self.toggle_btn.setObjectName("toggleBtn")
        self.toggle_btn.setFixedSize(36, 36)
        self.toggle_btn.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.toggle_btn.clicked.connect(self._toggle_sidebar)

        header_label = QtWidgets.QLabel("HoneyBadger Netrunner")
        header_label.setObjectName("headerLabel")

        # Session title in header
        self._session_title_lbl = QtWidgets.QLabel("New Chat")
        self._session_title_lbl.setObjectName("sessionTitleLabel")

        header_layout.addWidget(self.toggle_btn)
        header_layout.addSpacing(15)
        header_layout.addWidget(header_label)
        header_layout.addSpacing(20)
        header_layout.addWidget(self._session_title_lbl)
        header_layout.addStretch()

        # ── Body ──
        body_widget = QtWidgets.QWidget()
        body_layout = QtWidgets.QHBoxLayout(body_widget)
        body_layout.setSpacing(0)
        body_layout.setContentsMargins(0, 0, 0, 0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        self.sidebar_widget = QtWidgets.QWidget()
        self.sidebar_widget.setObjectName("sidebarWidget")
        self.sidebar_widget.setFixedWidth(340)
        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        # Hardware monitor
        self.hardware_panel = HardwareMonitorPanel(self)
        self.hardware_panel.setVisible(False)
        sidebar_layout.addWidget(self.hardware_panel)

        # Voice control
        self.voice_panel = VoiceControlPanel(self)
        self.voice_panel.voice_mode_changed.connect(self._on_voice_mode_changed)
        self.voice_panel.tts_toggled.connect(self._on_tts_toggled)
        self.voice_panel.voice_changed.connect(self._on_voice_changed)
        self.voice_panel.calibration_requested.connect(self._on_voice_calibration)
        sidebar_layout.addWidget(self.voice_panel)

        # Chat history
        self.history_panel = ChatHistoryPanel(self)
        self.history_panel.session_selected.connect(self._load_session)
        self.history_panel.new_chat_requested.connect(self._on_new_chat)
        self.history_panel.session_deleted.connect(self._on_session_deleted)
        sidebar_layout.addWidget(self.history_panel, 1)   # stretch so it fills space

        # ── Chat Input (now lives in sidebar) ────────────────────────────────
        input_group = QtWidgets.QGroupBox("Message")
        input_group.setObjectName("inputGroup")
        input_group_layout = QtWidgets.QVBoxLayout(input_group)
        input_group_layout.setSpacing(8)
        input_group_layout.setContentsMargins(8, 14, 8, 10)

        input_container = QtWidgets.QFrame()
        input_container.setObjectName("inputContainer")
        input_layout = QtWidgets.QHBoxLayout(input_container)
        input_layout.setSpacing(8)
        input_layout.setContentsMargins(12, 8, 8, 8)

        self.prompt_edit = PromptTextEdit()
        self.prompt_edit.setPlaceholderText("Message HoneyBadger…")
        self.prompt_edit.setObjectName("promptEdit")
        self.prompt_edit.setMaximumHeight(80)
        self.prompt_edit.send_requested.connect(self._on_send)
        self.prompt_edit.stop_mic_requested.connect(self._on_enter_while_recording)

        # Mic button
        self.mic_button = QtWidgets.QPushButton("🎤")
        self.mic_button.setObjectName("micButton")
        self.mic_button.setFixedSize(36, 36)
        self.mic_button.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.mic_button.setCheckable(True)
        self.mic_button.clicked.connect(self._on_mic_clicked)
        if not self._mic_available:
            self.mic_button.setEnabled(False)
            self.mic_button.setToolTip("No microphone detected")
        else:
            self.mic_button.setToolTip("Push-to-talk (select voice mode in sidebar)")

        self._mic_pulse_timer = QTimer(self)
        self._mic_pulse_timer.timeout.connect(self._pulse_mic)
        self._mic_pulse_on = False

        # Plus button
        self.plus_button = QtWidgets.QPushButton("＋")
        self.plus_button.setObjectName("plusButton")
        self.plus_button.setFixedSize(36, 36)
        self.plus_button.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.plus_button.setToolTip("Media, Mentions, Actions, File sharing")
        self.plus_button.clicked.connect(self._on_plus_clicked)

        self.send_button = QtWidgets.QPushButton("↑")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(36, 36)
        self.send_button.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.send_button.clicked.connect(self._on_send)

        input_layout.addWidget(self.plus_button)
        input_layout.addWidget(self.prompt_edit)
        input_layout.addWidget(self.mic_button)
        input_layout.addWidget(self.send_button)

        input_group_layout.addWidget(input_container)

        # Hint label
        hint = QtWidgets.QLabel("Enter  send  •  Shift+Enter  newline")
        hint.setStyleSheet("color: #475569; font-size: 11px;")
        hint.setAlignment(Qt.AlignCenter)
        input_group_layout.addWidget(hint)

        sidebar_layout.addWidget(input_group)

        # ── Main Content (chat display only) ─────────────────────────────────
        main_content_widget = QtWidgets.QWidget()
        main_content_layout = QtWidgets.QVBoxLayout(main_content_widget)
        main_content_layout.setSpacing(0)
        main_content_layout.setContentsMargins(0, 0, 0, 0)

        self.response_box = QtWidgets.QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setPlaceholderText("Cyberpunk Assistant ready. Awaiting command…")
        self.response_box.setObjectName("responseBox")
        main_content_layout.addWidget(self.response_box)

        # Assemble body
        body_layout.addWidget(self.sidebar_widget)

        # Thin divider
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.VLine)
        divider.setObjectName("sidebarDivider")
        body_layout.addWidget(divider)

        body_layout.addWidget(main_content_widget, 1)

        main_layout.addWidget(header_widget)
        main_layout.addWidget(body_widget, 1)

        self.setCentralWidget(main_widget)

    def _toggle_sidebar(self) -> None:
        self.sidebar_widget.setVisible(not self.sidebar_widget.isVisible())

    # ── Stylesheet ────────────────────────────────────────────────────────────

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #111111;
                color: #e2e8f0;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                font-size: 14px;
            }
            QWidget#sidebarWidget {
                background-color: #0d0d0d;
                border-right: 1px solid rgba(255,255,255,0.06);
            }
            QFrame#sidebarDivider {
                color: rgba(255,255,255,0.06);
                max-width: 1px;
            }
            QWidget#headerWidget {
                background-color: rgba(255, 255, 255, 0.02);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QPushButton#toggleBtn {
                background: transparent;
                color: #94a3b8;
                font-size: 22px;
                border: none;
                border-radius: 6px;
            }
            QPushButton#toggleBtn:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
            QLabel#headerLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            QLabel#sessionTitleLabel {
                color: #64748b;
                font-size: 13px;
            }
            QGroupBox#monitorPanel {
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 14px 8px 8px 8px;
                margin-top: 12px;
                background: rgba(255, 255, 255, 0.02);
                color: #94a3b8;
                font-size: 12px;
            }
            QGroupBox#monitorPanel::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #ffffff;
                font-weight: 600;
            }
            QGroupBox#voicePanel {
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 14px 8px 8px 8px;
                margin-top: 12px;
                background: rgba(255, 255, 255, 0.02);
                color: #94a3b8;
                font-size: 12px;
            }
            QGroupBox#voicePanel::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #ffffff;
                font-weight: 600;
            }
            /* ── Chat History Panel ── */
            QGroupBox#historyPanel {
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 14px 4px 4px 4px;
                margin-top: 12px;
                background: rgba(255, 255, 255, 0.02);
                color: #94a3b8;
                font-size: 12px;
            }
            QGroupBox#historyPanel::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #ffffff;
                font-weight: 600;
            }
            QScrollArea#historyScroll {
                background: transparent;
                border: none;
            }
            QScrollArea#historyScroll > QWidget > QWidget {
                background: transparent;
            }
            QPushButton#newChatBtn {
                background: rgba(99, 102, 241, 0.15);
                color: #818cf8;
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#newChatBtn:hover {
                background: rgba(99, 102, 241, 0.28);
                color: #a5b4fc;
            }
            QWidget#historyRow {
                background: transparent;
                border-radius: 8px;
            }
            QWidget#historyRow:hover {
                background: rgba(255,255,255,0.05);
            }
            QWidget#historyRowActive {
                background: rgba(99, 102, 241, 0.12);
                border: 1px solid rgba(99, 102, 241, 0.25);
                border-radius: 8px;
            }
            QPushButton#historyDeleteBtn {
                background: transparent;
                color: #475569;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton#historyDeleteBtn:hover {
                color: #ef4444;
                background: rgba(239,68,68,0.1);
            }
            /* ── Input group (sidebar) ── */
            QGroupBox#inputGroup {
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 14px 4px 8px 4px;
                margin-top: 6px;
                background: rgba(255, 255, 255, 0.02);
            }
            QGroupBox#inputGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #ffffff;
                font-weight: 600;
                font-size: 12px;
            }
            QFrame#inputContainer {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 16px;
            }
            QTextEdit#promptEdit {
                background: transparent;
                border: none;
                color: #ffffff;
                font-size: 14px;
            }
            QTextEdit#responseBox {
                background: transparent;
                border: none;
                padding: 24px 48px;
                color: #d4d4d8;
                font-size: 15px;
                line-height: 1.7;
            }
            QPushButton#sendButton {
                background: #ffffff;
                color: #111111;
                border: none;
                border-radius: 18px;
                font-size: 20px;
                font-weight: 800;
                padding-bottom: 2px;
            }
            QPushButton#sendButton:hover {
                background: #e2e8f0;
            }
            QPushButton#sendButton:pressed {
                background: #cbd5e1;
            }
            QPushButton#sendButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }
            QLabel#thinkingLabel {
                color: #94a3b8;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#plusButton {
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 18px;
                font-size: 16px;
                color: #94a3b8;
            }
            QPushButton#plusButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.25);
            }
            QPushButton#plusButton:pressed {
                background: rgba(255, 255, 255, 0.15);
            }
            QPushButton#micButton {
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 18px;
                font-size: 16px;
                color: #94a3b8;
            }
            QPushButton#micButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.25);
            }
            QPushButton#micButton:checked {
                background: rgba(239, 68, 68, 0.25);
                border-color: #ef4444;
                color: #ef4444;
            }
            QPushButton#micButton:disabled {
                color: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.05);
            }
            QPushButton#calibrateVoiceBtn {
                background: rgba(59, 130, 246, 0.12);
                border: 1px solid rgba(59, 130, 246, 0.25);
                border-radius: 8px;
                color: #60a5fa;
                padding: 6px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#calibrateVoiceBtn:hover {
                background: rgba(59, 130, 246, 0.22);
                border-color: rgba(59, 130, 246, 0.4);
            }
            QPushButton#calibrateVoiceBtn:pressed {
                background: rgba(59, 130, 246, 0.3);
            }
            QComboBox#voiceModeCombo, QComboBox#voiceSelectCombo {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 5px 10px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QComboBox#voiceModeCombo::drop-down, QComboBox#voiceSelectCombo::drop-down {
                border: none;
                width: 22px;
            }
            QComboBox#voiceModeCombo QAbstractItemView, QComboBox#voiceSelectCombo QAbstractItemView {
                background: #1e1e1e;
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #e2e8f0;
                selection-background-color: rgba(255, 255, 255, 0.1);
            }
            QCheckBox#ttsCheck {
                color: #94a3b8;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox#ttsCheck::indicator {
                width: 15px;
                height: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                background: transparent;
            }
            QCheckBox#ttsCheck::indicator:checked {
                background: #4ade80;
                border-color: #4ade80;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    # ── Send logic ────────────────────────────────────────────────────────────

    def _try_social_media_shortcut(self, prompt: str) -> bool:
        """
        Detect any phrase that intends to open a social media / messaging app
        and launch it directly without going through the AI.

        Matched patterns (case-insensitive):
          • "open/launch/start/run/load/show/go to/pull up/bring up <app>"
          • "open the/my <app>"
          • "<app>" alone  (bare app name)
          • "i want to open <app>", "can you open <app>", etc.
        Returns True if handled, False to pass to the AI.
        """
        import subprocess
        lower = prompt.lower().strip()

        # Strip common sentence wrappers so bare "instagram" is also caught
        for prefix in (
            "can you ", "could you ", "please ", "hey ", "yo ",
            "i want to ", "i need to ", "i'd like to ", "id like to ",
            "i want ", "i need ",
        ):
            if lower.startswith(prefix):
                lower = lower[len(prefix):]

        TRIGGER_VERBS = (
            "open", "launch", "start", "show", "go to", "goto",
            "pull up", "bring up", "load", "run", "get", "boot",
            "fire up", "jump to", "switch to", "take me to",
            "navigate to", "open up", "start up",
        )

        app_name: Optional[str] = None

        # 1) verb + optional article + app name
        for verb in TRIGGER_VERBS:
            for article in ("", " the", " my", " up", " up the", " up my"):
                pattern = verb + article + " "
                if lower.startswith(pattern):
                    candidate = lower[len(pattern):].strip()
                    for suffix in (
                        " for me", " please", " app", " now",
                        " up", " application",
                    ):
                        if candidate.endswith(suffix):
                            candidate = candidate[: -len(suffix)].strip()
                    app_name = candidate
                    break
            if app_name:
                break

        # 2) Bare app name (no verb) — e.g. just typing "instagram"
        if not app_name:
            candidate = lower.strip()
            for suffix in (" app", " please", " now", " for me"):
                if candidate.endswith(suffix):
                    candidate = candidate[: -len(suffix)].strip()
            # Only accept if it is a recognised app (avoid false positives)
            if resolve_social_app(candidate):
                app_name = candidate
            else:
                from honeybadger.tasks.social_media import SOCIAL_MEDIA_APPS
                for app in SOCIAL_MEDIA_APPS.keys():
                    if app in candidate:
                        app_name = app
                        break

        if not app_name:
            return False

        result = resolve_social_app(app_name)
        if result is None:
            from honeybadger.tasks.social_media import SOCIAL_MEDIA_APPS
            for app in SOCIAL_MEDIA_APPS.keys():
                if app in app_name.lower():
                    result = resolve_social_app(app)
                    break

        if result is None:
            return False

        display_name, ps_command = result

        self._append_user_bubble(prompt)
        self._append_hb_header()

        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_command],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            msg = f"Opening {display_name} ✓"
        except Exception as exc:
            logger.error("Social app launch failed: %s", exc)
            msg = f"Couldn't open {display_name}: {exc}"

        self.response_box.moveCursor(QtGui.QTextCursor.End)
        self.response_box.insertHtml(f"<span style='color: #4ade80;'>{msg}</span><br>")
        self.response_box.ensureCursorVisible()
        self._speak_response(msg)
        # Save to session
        self._session_add_message("user", prompt)
        self._session_add_message("honeybadger", msg)
        return True


    def _append_user_bubble(self, prompt: str) -> None:
        if self.response_box.toPlainText().strip():
            self.response_box.append(
                "<hr style='border: 1px solid rgba(255,255,255,0.05); margin: 20px 0;'>"
            )
        self.response_box.moveCursor(QtGui.QTextCursor.End)
        self.response_box.insertHtml(
            f"<div style='margin-bottom: 10px;'>"
            f"<b style='color: #a1a1aa; font-size: 15px;'>You</b><br>"
            f"<span style='color: #ffffff;'>{prompt.replace(chr(10), '<br>')}</span>"
            f"</div><br>"
        )
        self.response_box.moveCursor(QtGui.QTextCursor.End)

    def _append_hb_header(self) -> None:
        self.response_box.insertHtml("<b style='color: #ffffff; font-size: 15px;'>HoneyBadger</b><br>")
        self.response_box.moveCursor(QtGui.QTextCursor.End)

    def _on_send(self) -> None:
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt or self.worker is not None:
            return

        self.prompt_edit.clear()

        # Fast-path: social media app launch
        if self._try_social_media_shortcut(prompt):
            return

        # Check for verbal confirmation to execute pending command
        if self.pending_command and prompt.lower() in ["start", "yes", "do it", "go", "execute"]:
            command = self.pending_command
            self.pending_command = None

            self._append_user_bubble(prompt)
            self._append_hb_header()

            self.response_box.append(
                "<div style='color: #fbbf24; font-size: 13px; margin: 10px 0;'>[System] Executing command...</div>"
            )
            output = execute_powershell(command)
            feedback_prompt = (
                f"You requested to execute this command:\n{command}\n\n"
                f"The command has been executed. Output:\n{output}\n\n"
                f"Please analyze this output and respond to the user."
            )
            self.response_box.append(
                "<div style='color: #4ade80; font-size: 13px; margin: 10px 0;'>"
                "[System] Command completed. Sending results to HoneyBadger.</div>"
            )
            self._session_add_message("user", prompt)

            self.send_button.setEnabled(False)
            self.worker = CommandWorker(feedback_prompt, self.router)
            self.worker.chunk_ready.connect(self._append_chunk)
            self.worker.error.connect(self._display_error)
            self.worker.finished.connect(self._worker_finished)
            self.worker.start()
            return

        # Cancel pending command if user typed something else
        if self.pending_command:
            self.pending_command = None
            self.response_box.append(
                "<div style='color: #94a3b8; font-size: 13px; margin: 10px 0;'>"
                "[System] Pending command cancelled.</div>"
            )

        self._current_response_text = ""

        self._append_user_bubble(prompt)
        self._append_hb_header()
        self._session_add_message("user", prompt)

        # Update header title
        self._session_title_lbl.setText(
            self._current_session["title"][:40]
        )

        self.send_button.setEnabled(False)

        self.worker = CommandWorker(prompt, self.router)
        self.worker.chunk_ready.connect(self._append_chunk)
        self.worker.error.connect(self._display_error)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _append_chunk(self, chunk: str) -> None:
        self.response_box.moveCursor(QtGui.QTextCursor.End)
        self.response_box.insertPlainText(chunk)
        self.response_box.ensureCursorVisible()
        self._current_response_text += chunk
        self.hardware_panel.model_label.setText(self.router.active_model)

    def _display_error(self, message: str) -> None:
        self.response_box.append(f"\n[ERROR] {message}")

    def _worker_finished(self) -> None:
        full_response = self._current_response_text
        self._current_response_text = ""
        self.worker = None
        self.send_button.setEnabled(True)
        self.hardware_panel.model_label.setText(self.router.active_model)
        self._animate_send_button()

        # Save HoneyBadger response to session
        clean_for_storage = re.sub(
            r"<execute>.*?</execute>", "", full_response,
            flags=re.IGNORECASE | re.DOTALL
        ).strip()
        if clean_for_storage:
            self._session_add_message("honeybadger", clean_for_storage)

        execute_match = re.search(r"<execute>(.*?)</execute>", full_response, re.IGNORECASE | re.DOTALL)
        if execute_match:
            command = execute_match.group(1).strip()
            clean_response = re.sub(
                r"<execute>.*?</execute>", "", full_response, flags=re.IGNORECASE | re.DOTALL
            )
            self._speak_response(clean_response)
            self._handle_command_execution(command)
        else:
            self._speak_response(full_response)

    def _handle_command_execution(self, command: str) -> None:
        """Stores the command and prompts the user to confirm (with social auto-auth)."""
        # Auto-authorize social media commands
        from honeybadger.tasks.social_media import SOCIAL_MEDIA_APPS
        is_social = False
        matched_cmd = None
        cmd_lower = command.lower()
        for app, app_cmd in SOCIAL_MEDIA_APPS.items():
            if app in cmd_lower or (":" in cmd_lower and app in cmd_lower.replace(":", "")):
                is_social = True
                matched_cmd = app_cmd
                break

        if is_social and matched_cmd:
            self.response_box.append(
                f"<div style='color: #4ade80; font-size: 13px; margin: 10px 0;'>"
                f"[Voice] Auto-authorized social media integration. Running: {matched_cmd}</div>"
            )
            self.response_box.ensureCursorVisible()
            execute_powershell(matched_cmd)
            self._speak_response("Opened social media app.")
            return

        self.pending_command = command
        self.response_box.append(
            f"<div style='background-color: rgba(255,255,255,0.05); padding: 10px; "
            f"border-radius: 8px; margin: 10px 0;'>"
            f"<b style='color: #f8fafc;'>Permission Required</b><br>"
            f"<span style='color: #94a3b8;'>HoneyBadger wants to execute:</span><br>"
            f"<pre style='color: #fbbf24;'>{command}</pre>"
            f"<b style='color: #4ade80;'>Say or type 'start' to allow, or anything else to cancel.</b>"
            f"</div>"
        )
        self.response_box.ensureCursorVisible()
        self._speak_response("I have prepared the command. Just say 'start' to execute.")

    # ── Animations ────────────────────────────────────────────────────────────

    def _animate_send_button(self) -> None:
        self.send_button.setStyleSheet(
            "QPushButton#sendButton { background: #4ade80; color: #111111; "
            "border-radius: 18px; font-size: 20px; font-weight: 800; }"
        )
        QTimer.singleShot(400, self._reset_send_button_style)

    def _reset_send_button_style(self) -> None:
        self.send_button.setStyleSheet("")

    # ── Monitor ───────────────────────────────────────────────────────────────

    def _start_monitor(self) -> None:
        self.monitor_timer = QtCore.QTimer(self)
        self.monitor_timer.timeout.connect(
            lambda: self.hardware_panel.update_status(self.router.active_model)
        )
        self.monitor_timer.start(2000)

    # ── Voice ─────────────────────────────────────────────────────────────────

    def _on_voice_calibration(self) -> None:
        was_running = False
        if self._voice_listener and self._voice_listener.isRunning():
            was_running = True
            self._voice_listener.stop_listening()
            self._voice_listener.wait(2000)

        dlg = VoiceCalibrationDialog(self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.response_box.moveCursor(QtGui.QTextCursor.End)
            self.response_box.insertHtml(
                "<div style='color: #60a5fa; font-size: 13px; margin: 6px 0;'>"
                "[Voice] Calibration successful! Speaker profile enrolled.</div>"
            )
            self._speak_response("Voice calibration successful.")
        else:
            self.response_box.moveCursor(QtGui.QTextCursor.End)
            self.response_box.insertHtml(
                "<div style='color: #94a3b8; font-size: 13px; margin: 6px 0;'>"
                "[Voice] Calibration cancelled.</div>"
            )

        if was_running:
            self._start_voice_listener(always_on=(self._voice_mode == "always"))

    def _on_voice_mode_changed(self, mode: str) -> None:
        self._voice_mode = mode
        if self._voice_listener and self._voice_listener.is_listening:
            self._voice_listener.stop_listening()

        if mode == "off":
            self.mic_button.setChecked(False)
            self.mic_button.setEnabled(self._mic_available)
            self.mic_button.setToolTip("Voice is off — select a mode in the sidebar")
            self.voice_panel.set_status("Idle", "#94a3b8")
            self._stop_mic_pulse()
        elif mode == "push":
            self.mic_button.setEnabled(self._mic_available)
            self.mic_button.setToolTip("Click to start / stop listening")
            self.voice_panel.set_status("Ready (push mic)", "#94a3b8")
        elif mode == "always":
            # Re-enable mic button as a manual fallback for wake-word failures
            self.mic_button.setEnabled(self._mic_available)
            self.mic_button.setChecked(False)
            self.mic_button.setToolTip(
                "Say 'Wakeup, daddy's home' to activate — or click 🎤 to force-activate"
            )
            self.voice_panel.set_status("Waiting for 'Wakeup, daddy's home'…", "#f59e0b")
            self._start_voice_listener(always_on=True)

    def _on_plus_clicked(self) -> None:
        """Handles Plus button clicked — opens context menu for media/mentions/file sharing."""
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
        """)
        
        media_action = menu.addAction("📷 Share Media")
        mention_action = menu.addAction("👤 Mention User (@)")
        action_action = menu.addAction("⚙️ Trigger Action")
        file_action = menu.addAction("📁 Share File")
        
        action = menu.exec(self.plus_button.mapToGlobal(QtCore.QPoint(0, -140)))
        
        if action == media_action:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Share Media", "", "Images (*.png *.jpg *.jpeg *.gif);;Videos (*.mp4 *.avi)")
            if file_path:
                self.prompt_edit.insertPlainText(f"[Media: {Path(file_path).name}] ")
        elif action == mention_action:
            self.prompt_edit.insertPlainText("@")
            self.prompt_edit.setFocus()
        elif action == action_action:
            self.prompt_edit.insertPlainText("/action ")
            self.prompt_edit.setFocus()
        elif action == file_action:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Share File", "", "All Files (*.*)")
            if file_path:
                self.prompt_edit.insertPlainText(f"[File: {Path(file_path).name}] ")

    def _on_mic_clicked(self) -> None:
        """Toggle push-to-talk; or force-activate in always-on mode."""
        if self._voice_mode == "off":
            self.mic_button.setChecked(False)
            return

        # Always-on: mic button acts as a manual wake bypass (Fix 3)
        if self._voice_mode == "always":
            self.mic_button.setChecked(False)
            if self._voice_listener and self._voice_listener.isRunning():
                self._voice_listener.force_activate()
                self.voice_panel.set_status("Listening… (manual)", "#ef4444")
                self._start_mic_pulse()
            return

        if self.mic_button.isChecked():
            self._start_voice_listener(always_on=False)
        else:
            if self._voice_listener and self._voice_listener.is_listening:
                self._voice_listener.stop_listening()

    def _start_voice_listener(self, always_on: bool) -> None:
        if self._voice_listener and self._voice_listener.isRunning():
            self._voice_listener.stop_listening()
            self._voice_listener.wait(2000)

        model_path = VOSK_MODEL_PATH if VOSK_MODEL_PATH else None
        self._voice_listener = VoiceListener(
            wake_word=WAKE_WORD,
            always_on=always_on,
            model_path=model_path,
            parent=self,
        )
        self._voice_listener.text_recognized.connect(self._on_voice_text)
        self._voice_listener.partial_text.connect(self._on_voice_partial)
        self._voice_listener.listening_started.connect(self._on_listening_started)
        self._voice_listener.listening_stopped.connect(self._on_listening_stopped)
        self._voice_listener.error_occurred.connect(self._on_voice_error)
        self._voice_listener.voice_verified.connect(self._on_voice_verified)
        self._voice_listener.start()

    def _on_voice_verified(self, verified: bool, similarity: float) -> None:
        self.response_box.moveCursor(QtGui.QTextCursor.End)
        if verified:
            if similarity < 1.0:
                msg = f"[Voice] Speaker verified (similarity: {similarity:.2f})"
                self.response_box.insertHtml(
                    f"<div style='color: #4ade80; font-size: 13px; margin: 6px 0;'>{msg}</div>"
                )
        else:
            msg = f"[Voice] Wake word rejected: Speaker mismatch (similarity: {similarity:.2f})"
            self.response_box.insertHtml(
                f"<div style='color: #ef4444; font-size: 13px; margin: 6px 0;'>{msg}</div>"
            )
        self.response_box.ensureCursorVisible()

    def _on_enter_while_recording(self) -> None:
        """
        Enter pressed while push-to-talk mic is active.
        Stop recording and immediately send whatever was transcribed into
        the prompt box — giving a natural 'commit voice input' experience.
        """
        if (
            self._voice_mode == "push"
            and self._voice_listener
            and self._voice_listener.is_listening
        ):
            # Stop the mic — final transcription will arrive via text_recognized
            self._voice_listener.stop_listening()
            self.mic_button.setChecked(False)
            # Send whatever is already in the prompt box immediately
            if self.prompt_edit.toPlainText().strip():
                self._on_send()
        else:
            # Not recording — treat as normal send
            self._on_send()

    def _on_voice_text(self, text: str) -> None:
        """Final transcription received — fill prompt and send."""
        # E6: correction sentinel — cancel everything in flight
        if text == CORRECTION_SENTINEL:
            self._on_cancel_command()
            return
        # Reset always-on status back to waiting after the command window closes
        if self._voice_mode == "always":
            self._stop_mic_pulse()
            self.voice_panel.set_status('Waiting for "Wakeup, daddy\'s home"…', "#f59e0b")
        self.prompt_edit.setPlainText(text)
        self._on_send()


    def _on_cancel_command(self) -> None:
        """Cancel any in-flight AI request or pending command (E6)."""
        cancelled_something = False

        if self.worker is not None:
            self.worker.chunk_ready.disconnect()
            self.worker.error.disconnect()
            self.worker.finished.disconnect()
            self.worker.terminate()
            self.worker = None
            self.send_button.setEnabled(True)
            cancelled_something = True

        if self.pending_command is not None:
            self.pending_command = None
            cancelled_something = True

        msg = "Got it — cancelled." if cancelled_something else "Nothing to cancel."
        self.response_box.moveCursor(QtGui.QTextCursor.End)
        self.response_box.insertHtml(
            f"<div style='color: #f59e0b; font-size: 13px; margin: 6px 0;'>"
            f"[Voice] {msg}</div>"
        )
        self.response_box.ensureCursorVisible()
        self._speak_response(msg)

    def _on_voice_partial(self, text: str) -> None:
        self.prompt_edit.setPlainText(text)
        cursor = self.prompt_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.prompt_edit.setTextCursor(cursor)

    def _on_listening_started(self) -> None:
        self.voice_panel.set_status("Listening…", "#ef4444")
        self._start_mic_pulse()
        if self._voice_mode == "always":
            self.voice_panel.set_status("Waiting for 'Wakeup, daddy's home'…", "#f59e0b")

    def _on_listening_stopped(self) -> None:
        self.mic_button.setChecked(False)
        self._stop_mic_pulse()
        # In always-on mode the listener keeps running — restore the amber status
        if self._voice_mode == "always" and self._voice_listener and self._voice_listener.isRunning():
            self.voice_panel.set_status("Waiting for 'Wakeup, daddy's home'…", "#f59e0b")
        else:
            self.voice_panel.set_status("Idle", "#94a3b8")

    def _on_voice_error(self, message: str) -> None:
        self.voice_panel.set_status("Error", "#ef4444")
        self.mic_button.setChecked(False)
        self._stop_mic_pulse()
        self.response_box.append(f"\n[VOICE ERROR] {message}")
        logger.error("Voice error: %s", message)

    # ── Mic pulse animation ───────────────────────────────────────────────────

    def _start_mic_pulse(self) -> None:
        self._mic_pulse_on = True
        self._mic_pulse_timer.start(600)

    def _stop_mic_pulse(self) -> None:
        self._mic_pulse_timer.stop()
        self._mic_pulse_on = False
        self.mic_button.setStyleSheet("")

    def _pulse_mic(self) -> None:
        if self._mic_pulse_on:
            self.mic_button.setStyleSheet(
                "QPushButton#micButton { background: rgba(239, 68, 68, 0.35); "
                "border-color: #ef4444; color: #ffffff; border-radius: 18px; "
                "font-size: 16px; border: 1px solid #ef4444; }"
            )
        else:
            self.mic_button.setStyleSheet(
                "QPushButton#micButton { background: rgba(239, 68, 68, 0.15); "
                "border-color: #ef4444; color: #ef4444; border-radius: 18px; "
                "font-size: 16px; border: 1px solid #ef4444; }"
            )
        self._mic_pulse_on = not self._mic_pulse_on

    # ── TTS ───────────────────────────────────────────────────────────────────

    def _on_tts_toggled(self, enabled: bool) -> None:
        self._tts_enabled = enabled

    def _on_voice_changed(self, voice_id: str) -> None:
        self._tts_voice_id = voice_id

    def _speak_response(self, text: str) -> None:
        if not self._tts_enabled or not text.strip():
            return
        clean_text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        clean_text = re.sub(r'[*#_`~]', '', clean_text).strip()
        if not clean_text:
            return
        self._tts_worker = speak(clean_text, voice_id=self._tts_voice_id)

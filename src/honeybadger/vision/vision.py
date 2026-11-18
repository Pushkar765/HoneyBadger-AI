import os

# Force all vision libraries to CPU before importing any backend
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import logging
from typing import Dict, Optional

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

try:
    import mediapipe as mp
    _MP_AVAILABLE = True
except ImportError:
    _MP_AVAILABLE = False

try:
    from deepface import DeepFace
    _DEEPFACE_AVAILABLE = True
except ImportError:
    _DEEPFACE_AVAILABLE = False

from honeybadger.brain.ollama_brain import ask_honeybadger

logger = logging.getLogger(__name__)
_VISION_UNAVAILABLE_MSG = (
    "Vision features unavailable: deepface/mediapipe require tensorflow "
    "which does not yet support Python 3.14."
)


def _cpu_only_deepface_analysis(frame) -> Dict[str, Optional[str]]:
    if not _DEEPFACE_AVAILABLE:
        raise RuntimeError(_VISION_UNAVAILABLE_MSG)
    analysis = DeepFace.analyze(
        img_path=None,
        img=frame,
        actions=["emotion"],
        enforce_detection=False,
        detector_backend="opencv",
        prog_bar=False,
    )
    if isinstance(analysis, list):
        analysis = analysis[0]
    emotion = analysis.get("dominant_emotion")
    return {"dominant_emotion": emotion}


def capture_analyze() -> Dict[str, Optional[str]]:
    if not _CV2_AVAILABLE or not _MP_AVAILABLE or not _DEEPFACE_AVAILABLE:
        logger.warning(_VISION_UNAVAILABLE_MSG)
        return {
            "face_count": "0",
            "dominant_emotion": "unavailable",
            "llm_summary": _VISION_UNAVAILABLE_MSG,
        }

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Unable to open the default camera.")

    success, frame = cap.read()
    cap.release()
    if not success or frame is None:
        raise RuntimeError("Failed to capture a frame from the camera.")

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    detections = 0
    with mp.solutions.face_detection.FaceDetection(model_selection=0) as detector:
        results = detector.process(rgb_frame)
        if results.detections:
            detections = len(results.detections)

    face_emotion = _cpu_only_deepface_analysis(frame)
    emotion_label = face_emotion.get("dominant_emotion", "unknown")
    prompt = (
        "I captured a user frame and extracted an emotion signal. "
        f"The face detector found {detections} face(s) and the dominant emotion is {emotion_label}. "
        "Please summarize the visible mood in one concise sentence."
    )
    llm_result = ask_honeybadger(prompt, model="general")
    return {
        "face_count": str(detections),
        "dominant_emotion": emotion_label,
        "llm_summary": llm_result.strip(),
    }

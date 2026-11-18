"""HoneyBadger core package."""

from .builder import build_app, generate_image
from .cloud_sync import RecallClient, SanerClient, sync_to_cloud
from .emotion import detect_user_emotion, respond_with_empathy
from .knowledge import deep_research, teach
from .memory import HoneyBadgerMemory
from .permissions import nuclear_permission, request_permission
from .security import network_monitor, vulnerability_scan
from .smarthome import HomeAssistantClient
from .tasks import create_task, morning_standup
from .vision import capture_analyze
from .voice import VoiceListener, speak

__version__ = "0.1.0"

__all__ = [
    "HoneyBadgerMemory",
    "RecallClient",
    "SanerClient",
    "sync_to_cloud",
    "generate_image",
    "build_app",
    "detect_user_emotion",
    "respond_with_empathy",
    "deep_research",
    "teach",
    "network_monitor",
    "vulnerability_scan",
    "HomeAssistantClient",
    "create_task",
    "morning_standup",
    "capture_analyze",
    "request_permission",
    "nuclear_permission",
    "VoiceListener",
    "speak",
]

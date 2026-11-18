import logging
import sys
from typing import Generator

from PySide6 import QtWidgets
from honeybadger.brain.ollama_brain import check_vram_usage, stream_response
from honeybadger.ui.ui import HoneyBadgerUI
from honeybadger.vision.vision import capture_analyze

# Configure logging so voice recognition output is visible in the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

VISION_KEYWORDS = ["vision", "camera", "face", "photo", "detect", "image"]
ROUTING_KEYWORDS = ["code", "build", "program", "analyze", "hack"]


class MasterCommandRouter:
    def __init__(self) -> None:
        self.active_model = "phi4-mini"

    def _needs_vision(self, prompt: str) -> bool:
        return any(keyword in prompt.lower() for keyword in VISION_KEYWORDS)

    def _select_model(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if any(keyword in prompt_lower for keyword in ROUTING_KEYWORDS):
            return "gemma3:4b"
        return "phi4-mini"

    def stream_query(self, prompt: str) -> Generator[str, None, None]:
        check_vram_usage()

        if self._needs_vision(prompt):
            analysis = capture_analyze()
            self.active_model = "phi4-mini"
            yield "[Vision analysis captured on CPU]\n"
            yield f"Face count: {analysis.get('face_count')}\n"
            yield f"Emotion: {analysis.get('dominant_emotion')}\n"
            yield f"Summary: {analysis.get('llm_summary')}\n"
            return

        self.active_model = self._select_model(prompt)
        yield from stream_response(prompt, model=self.active_model)


def run() -> None:
    app = QtWidgets.QApplication(sys.argv)
    router = MasterCommandRouter()
    window = HoneyBadgerUI(router)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()

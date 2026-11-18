import logging
from typing import Dict, Optional

import requests

from honeybadger.config import RECALL_API_KEY, SANER_API_KEY

logger = logging.getLogger(__name__)

RECALL_ENDPOINT = "https://api.getrecall.ai/v1/knowledge"
SANER_ENDPOINT = "https://api.saner.ai/v1/notes"


class RecallClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or RECALL_API_KEY

    def upload(self, title: str, content: str, metadata: Optional[Dict[str, str]] = None) -> Dict:
        if not self.api_key:
            raise RuntimeError("Recall API key is not configured.")

        payload = {
            "title": title,
            "content": content,
            "metadata": metadata or {},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        response = requests.post(RECALL_ENDPOINT, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info("Synced content to Recall.ai: %s", title)
        return response.json()


class SanerClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or SANER_API_KEY

    def upload(self, title: str, content: str, tags: Optional[Dict[str, str]] = None) -> Dict:
        if not self.api_key:
            raise RuntimeError("Saner API key is not configured.")

        payload = {
            "title": title,
            "content": content,
            "tags": tags or {},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        response = requests.post(SANER_ENDPOINT, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info("Synced content to Saner.ai: %s", title)
        return response.json()


def sync_to_cloud(title: str, content: str, metadata: Optional[Dict[str, str]] = None) -> None:
    recall = RecallClient()
    saner = SanerClient()

    try:
        recall.upload(title, content, metadata)
    except Exception as exc:
        logger.warning("Recall sync failed: %s", exc)

    try:
        saner.upload(title, content, tags=metadata)
    except Exception as exc:
        logger.warning("Saner sync failed: %s", exc)

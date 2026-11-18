import logging
from typing import Dict, Optional

import requests

from honeybadger.brain.ollama_brain import ask_honeybadger
from honeybadger.config import CLICKUP_API_KEY, CLICKUP_LIST_ID

logger = logging.getLogger(__name__)
CLICKUP_BASE = "https://api.clickup.com/api/v2"


def create_task(title: str, description: str, list_id: Optional[str] = None) -> Dict:
    list_id = list_id or CLICKUP_LIST_ID
    if not list_id:
        raise RuntimeError("CLICKUP_LIST_ID must be set in the environment or passed explicitly.")
    if not CLICKUP_API_KEY:
        raise RuntimeError("CLICKUP_API_KEY is not configured.")

    endpoint = f"{CLICKUP_BASE}/list/{list_id}/task"
    payload = {
        "name": title,
        "description": description,
        "status": "to do",
        "priority": 3,
    }
    headers = {
        "Authorization": CLICKUP_API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    logger.info("Created ClickUp task: %s", title)
    return response.json()


def morning_standup(context_notes: Optional[str] = None) -> str:
    prompt = (
        "Create a concise morning standup summary for the day ahead. "
        "Include priorities, blockers, and a quick status update."
    )
    if context_notes:
        prompt += f"\nContext notes: {context_notes}"

    return ask_honeybadger(prompt, model="fast")

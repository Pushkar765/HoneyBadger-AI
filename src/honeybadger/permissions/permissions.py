import logging
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[2] / "permissions.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _log(action: str, description: str, risk_level: str, approved: bool, note: str = "") -> None:
    logger.info(
        "permission=%s description=%s risk_level=%s approved=%s note=%s",
        action,
        description,
        risk_level,
        approved,
        note,
    )


def request_permission(action: str, description: str, risk_level: str = "low") -> bool:
    prompt = (
        f"Permission requested: {action}\n"
        f"Description: {description}\n"
        f"Risk level: {risk_level}\n"
        "Approve this action? (yes/no): "
    )
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"yes", "y"}:
            _log(action, description, risk_level, True)
            return True
        if answer in {"no", "n"}:
            _log(action, description, risk_level, False)
            return False
        print("Please respond with 'yes' or 'no'.")


def nuclear_permission(action: str) -> bool:
    prompt = (
        f"NUCLEAR PERMISSION REQUIRED for: {action}\n"
        "Type CONFIRM exactly to proceed: "
    )
    answer = input(prompt).strip()
    approved = answer == "CONFIRM"
    note = "CONFIRM entered" if approved else f"entered '{answer}'"
    _log(action, "Nuclear permission", "critical", approved, note)
    return approved

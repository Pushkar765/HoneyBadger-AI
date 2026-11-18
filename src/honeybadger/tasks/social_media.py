"""
Social media app launcher for HoneyBadger.

Provides a lookup table of known social media apps and their Windows
launch commands (URI schemes or shell protocol paths). When a user asks
HoneyBadger to open a social media app, these commands will open the
*installed* app instead of a browser tab.

Windows URI scheme behaviour:
  - If the app is installed and registered the URI scheme, Windows
    launches the app directly.
  - If the app is NOT installed, Windows falls back to the Store or
    the browser — never silently fails.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App registry
# ---------------------------------------------------------------------------
# Keys are normalised lowercase names / aliases.
# Values are PowerShell one-liners that open the installed app.
#
# Priority order for each app:
#   1. Windows URI scheme  (opens installed UWP/app directly)
#   2. explorer shell:AppsFolder  (fallback for sideloaded apps)
#   3. Start-Process <url>  (browser fallback — last resort)
# ---------------------------------------------------------------------------

SOCIAL_MEDIA_APPS: dict[str, str] = {
    # ── Instagram ──────────────────────────────────────────────────────────
    "instagram": "try { Start-Process 'instagram:' -ErrorAction Stop } catch { Start-Process 'https://instagram.com' }",
    "ig":        "try { Start-Process 'instagram:' -ErrorAction Stop } catch { Start-Process 'https://instagram.com' }",
    "insta":     "try { Start-Process 'instagram:' -ErrorAction Stop } catch { Start-Process 'https://instagram.com' }",

    # ── Facebook ───────────────────────────────────────────────────────────
    "facebook":  "try { Start-Process 'fb:' -ErrorAction Stop } catch { Start-Process 'https://facebook.com' }",
    "fb":        "try { Start-Process 'fb:' -ErrorAction Stop } catch { Start-Process 'https://facebook.com' }",

    # ── X / Twitter ────────────────────────────────────────────────────────
    "twitter":   "try { Start-Process 'twitter:' -ErrorAction Stop } catch { Start-Process 'https://x.com' }",
    "x":         "try { Start-Process 'twitter:' -ErrorAction Stop } catch { Start-Process 'https://x.com' }",
    "tweet":     "try { Start-Process 'twitter:' -ErrorAction Stop } catch { Start-Process 'https://x.com' }",

    # ── TikTok ─────────────────────────────────────────────────────────────
    "tiktok":    "try { Start-Process 'tiktok:' -ErrorAction Stop } catch { Start-Process 'https://tiktok.com' }",
    "tik tok":   "try { Start-Process 'tiktok:' -ErrorAction Stop } catch { Start-Process 'https://tiktok.com' }",

    # ── Snapchat ───────────────────────────────────────────────────────────
    "snapchat":  "try { Start-Process 'snapchat:' -ErrorAction Stop } catch { Start-Process 'https://snapchat.com' }",
    "snap":      "try { Start-Process 'snapchat:' -ErrorAction Stop } catch { Start-Process 'https://snapchat.com' }",

    # ── YouTube ────────────────────────────────────────────────────────────
    "youtube":   "try { Start-Process 'vnd.youtube:' -ErrorAction Stop } catch { Start-Process 'https://youtube.com' }",
    "yt":        "try { Start-Process 'vnd.youtube:' -ErrorAction Stop } catch { Start-Process 'https://youtube.com' }",

    # ── WhatsApp ───────────────────────────────────────────────────────────
    "whatsapp":  "try { Start-Process 'whatsapp:' -ErrorAction Stop } catch { Start-Process 'https://web.whatsapp.com' }",
    "wa":        "try { Start-Process 'whatsapp:' -ErrorAction Stop } catch { Start-Process 'https://web.whatsapp.com' }",

    # ── Telegram ───────────────────────────────────────────────────────────
    "telegram":  "try { Start-Process 'tg:' -ErrorAction Stop } catch { Start-Process 'https://web.telegram.org' }",
    "tg":        "try { Start-Process 'tg:' -ErrorAction Stop } catch { Start-Process 'https://web.telegram.org' }",

    # ── Discord ────────────────────────────────────────────────────────────
    "discord":   "try { Start-Process 'discord:' -ErrorAction Stop } catch { Start-Process 'https://discord.com' }",

    # ── LinkedIn ───────────────────────────────────────────────────────────
    "linkedin":  "try { Start-Process 'linkedin:' -ErrorAction Stop } catch { Start-Process 'https://linkedin.com' }",

    # ── Reddit ─────────────────────────────────────────────────────────────
    "reddit":    "try { Start-Process 'reddit:' -ErrorAction Stop } catch { Start-Process 'https://reddit.com' }",

    # ── Pinterest ──────────────────────────────────────────────────────────
    "pinterest": "try { Start-Process 'pinterestsearch:' -ErrorAction Stop } catch { Start-Process 'https://pinterest.com' }",
    "pins":      "try { Start-Process 'pinterestsearch:' -ErrorAction Stop } catch { Start-Process 'https://pinterest.com' }",

    # ── Threads ────────────────────────────────────────────────────────────
    "threads":   "Start-Process 'https://www.threads.net/'",

    # ── BeReal ─────────────────────────────────────────────────────────────
    "bereal":    "try { Start-Process 'bereal:' -ErrorAction Stop } catch { Start-Process 'https://bereal.com' }",

    # ── Twitch ─────────────────────────────────────────────────────────────
    "twitch":    "try { Start-Process 'twitch:' -ErrorAction Stop } catch { Start-Process 'https://twitch.tv' }",

    # ── Mastodon ───────────────────────────────────────────────────────────
    "mastodon":  "Start-Process 'https://mastodon.social/'",

    # ── Signal ─────────────────────────────────────────────────────────────
    "signal":    "try { Start-Process 'sgnl:' -ErrorAction Stop } catch { Start-Process 'https://signal.org' }",
}

# Human-readable names for the confirmation message
APP_DISPLAY_NAMES: dict[str, str] = {
    "instagram": "Instagram",
    "ig":        "Instagram",
    "insta":     "Instagram",
    "facebook":  "Facebook",
    "fb":        "Facebook",
    "twitter":   "X (Twitter)",
    "x":         "X (Twitter)",
    "tweet":     "X (Twitter)",
    "tiktok":    "TikTok",
    "tik tok":   "TikTok",
    "snapchat":  "Snapchat",
    "snap":      "Snapchat",
    "youtube":   "YouTube",
    "yt":        "YouTube",
    "whatsapp":  "WhatsApp",
    "wa":        "WhatsApp",
    "telegram":  "Telegram",
    "tg":        "Telegram",
    "discord":   "Discord",
    "linkedin":  "LinkedIn",
    "reddit":    "Reddit",
    "pinterest": "Pinterest",
    "pins":      "Pinterest",
    "threads":   "Threads",
    "bereal":    "BeReal",
    "twitch":    "Twitch",
    "mastodon":  "Mastodon",
    "signal":    "Signal",
}


def resolve_social_app(name: str) -> Optional[tuple[str, str]]:
    """
    Look up a social media app by (possibly informal) name.

    Returns ``(display_name, powershell_command)`` if found, else ``None``.
    """
    key = name.strip().lower()
    command = SOCIAL_MEDIA_APPS.get(key)
    if command is None:
        return None
    display = APP_DISPLAY_NAMES.get(key, name.title())
    return display, command


def launch_social_app(name: str) -> str:
    """
    Directly launch a social media app by name.

    Returns a short status string describing what happened.
    """
    result = resolve_social_app(name)
    if result is None:
        return f"Unknown social media app: '{name}'. Check SOCIAL_MEDIA_APPS in social_media.py."

    display_name, command = result
    logger.info("Launching social media app '%s' with: %s", display_name, command)
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        return f"Opened {display_name}."
    except Exception as exc:
        logger.error("Failed to launch %s: %s", display_name, exc)
        return f"Failed to open {display_name}: {exc}"


def get_supported_apps() -> list[str]:
    """Return a sorted list of unique supported social media display names."""
    seen: set[str] = set()
    names: list[str] = []
    for display in APP_DISPLAY_NAMES.values():
        if display not in seen:
            seen.add(display)
            names.append(display)
    return sorted(names)

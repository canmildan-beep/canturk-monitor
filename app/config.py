import os


def _get(name, default=""):
    return os.environ.get(name, default)


API_ID = int(_get("API_ID", "0") or "0")
API_HASH = _get("API_HASH")
BOT_TOKEN = _get("BOT_TOKEN")
NOTIFY_CHAT_ID = _get("NOTIFY_CHAT_ID")

POSTGRES_HOST = _get("POSTGRES_HOST", "db")
POSTGRES_PORT = _get("POSTGRES_PORT", "5432")
POSTGRES_DB = _get("POSTGRES_DB", "canturk")
POSTGRES_USER = _get("POSTGRES_USER", "canturk")
POSTGRES_PASSWORD = _get("POSTGRES_PASSWORD")

PANEL_USER = _get("PANEL_USER", "admin")
PANEL_PASSWORD = _get("PANEL_PASSWORD")

DEDUP_DAYS = int(_get("DEDUP_DAYS", "7") or "7")
RETENTION_DAYS = int(_get("RETENTION_DAYS", "90") or "90")

SESSION_DIR = _get("SESSION_DIR", "/session")
SESSION_NAME = _get("SESSION_NAME", "canturk")

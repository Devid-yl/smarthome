import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure BASE_DIR points to the project root (same as Django's BASE_DIR)
# __file__ = .../smarthome/smarthome/tornado_app/config.py
# parents[2] = .../smarthome (project root with .env, static, media)
BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BASE_DIR / "smarthome"  # folder containing settings.py and tornado_app

# Load the same .env used by Django
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


def get_settings():
    return {
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        "cookie_secret": os.getenv("COOKIE_SECRET", "CHANGE_ME"),
        # Templates live under smarthome/smarthome/tornado_app/templates
        "template_path": str(PROJECT_DIR / "tornado_app" / "templates"),
        # Static and media live at project root, same as Django
        "static_path": str(BASE_DIR / "static"),
        "media_path": str(BASE_DIR / "media"),
        "xsrf_cookies": True,
    }


def get_database_url():
    # Reuse the same env variables as Django settings
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"

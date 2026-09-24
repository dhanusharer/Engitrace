import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current directory, parent directory, and project root
base_dir = Path(__file__).resolve().parent.parent
root_dir = base_dir.parent
load_dotenv(root_dir / ".env")
load_dotenv(base_dir / ".env")

POSTGRES_USER = os.getenv("POSTGRES_USER", "engitrace_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "engitrace_dev_password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "engitrace_db")

DEFAULT_DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
APP_ENV = os.getenv("APP_ENV", "development")

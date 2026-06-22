from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def load_dotenv_file(dotenv_path: Path) -> None:
	if not dotenv_path.exists():
		return

	for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue

		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if key and key not in os.environ:
			os.environ[key] = value


load_dotenv_file(BASE_DIR / ".env")

RAW_PDFS_DIR = BASE_DIR / "data" / "raw" / "pdfs"
RAW_ARTICLES_DIR = BASE_DIR / "data" / "raw" / "articles"
RAW_DATASETS_DIR = BASE_DIR / "data" / "raw" / "datasets"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FAISS_DIR = BASE_DIR / "storage" / "faiss_index"
FAISS_VERSIONS_DIR = FAISS_DIR / "versions"
FAISS_CURRENT_FILE = FAISS_DIR / "current.json"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_TIMEOUT_SECONDS = int(os.getenv("GROQ_TIMEOUT_SECONDS", "60"))


# API integration/auth settings
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "")
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "30"))

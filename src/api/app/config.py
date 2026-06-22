from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


_CONFIG_FILE = Path(__file__).resolve()
_DEFAULT_ROOT = _CONFIG_FILE.parents[3] if len(_CONFIG_FILE.parents) > 3 else _CONFIG_FILE.parents[1]
ROOT_DIR = Path(os.getenv("RESEARCHPILOT_ROOT_DIR", _DEFAULT_ROOT))


def _load_dotenv_files() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        return

    load_dotenv(ROOT_DIR / ".env", override=False)
    load_dotenv(_CONFIG_FILE.parents[1] / ".env", override=False)


_load_dotenv_files()


@dataclass(frozen=True)
class Settings:
    app_name: str
    data_dir: Path
    database_path: Path
    reports_dir: Path
    cache_dir: Path
    chroma_dir: Path
    llm_provider: str
    deepseek_api_key: str | None
    deepseek_base_url: str
    deepseek_model: str
    openai_compatible_api_key: str | None
    openai_compatible_base_url: str
    openai_compatible_model: str
    llm_timeout: float
    llm_temperature: float
    llm_max_retries: int
    openalex_base_url: str
    arxiv_base_url: str
    cors_origins: list[str]


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _path_from_env(name: str, default: Path) -> Path:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    path = Path(raw_value)
    if path.is_absolute():
        return path
    return ROOT_DIR / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    data_dir = _path_from_env("RESEARCHPILOT_DATA_DIR", ROOT_DIR / "data")
    reports_dir = _path_from_env("RESEARCHPILOT_REPORTS_DIR", data_dir / "reports")
    cache_dir = _path_from_env("RESEARCHPILOT_CACHE_DIR", data_dir / "cache")
    chroma_dir = _path_from_env("RESEARCHPILOT_CHROMA_DIR", data_dir / "chroma")
    database_path = _path_from_env("RESEARCHPILOT_DB_PATH", data_dir / "researchpilot.db")

    for path in (data_dir, reports_dir, cache_dir, chroma_dir):
        path.mkdir(parents=True, exist_ok=True)

    return Settings(
        app_name=os.getenv("RESEARCHPILOT_APP_NAME", "ResearchPilot API"),
        data_dir=data_dir,
        database_path=database_path,
        reports_dir=reports_dir,
        cache_dir=cache_dir,
        chroma_dir=chroma_dir,
        llm_provider=os.getenv("LLM_PROVIDER", "openai_compatible").lower(),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        openai_compatible_api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY"),
        openai_compatible_base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL", ""),
        openai_compatible_model=os.getenv("OPENAI_COMPATIBLE_MODEL", ""),
        llm_timeout=float(os.getenv("LLM_TIMEOUT", "45")),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
        openalex_base_url=os.getenv("OPENALEX_BASE_URL", "https://api.openalex.org"),
        arxiv_base_url=os.getenv("ARXIV_BASE_URL", "https://export.arxiv.org/api/query"),
        cors_origins=_split_csv(os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")),
    )


settings = get_settings()

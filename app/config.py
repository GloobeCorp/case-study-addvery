from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_SEARCH_MODEL = "gpt-5.5"


def load_environment() -> None:
    load_dotenv(ENV_PATH)


def has_openai_api_key() -> bool:
    load_environment()
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def get_openai_api_key() -> str:
    load_environment()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Chybí OPENAI_API_KEY. Vložte OpenAI API key ve webovém UI, ne Claude/Anthropic API key.")
    return api_key


def get_model_name() -> str:
    load_environment()
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def get_search_model_name() -> str:
    load_environment()
    return os.getenv("OPENAI_SEARCH_MODEL", DEFAULT_SEARCH_MODEL).strip() or DEFAULT_SEARCH_MODEL


def save_openai_api_key(api_key: str) -> None:
    value = api_key.strip()
    if not value:
        raise ValueError("OpenAI API key nemůže být prázdný.")
    if not value.startswith("sk-") or len(value) < 20:
        raise ValueError("Tento klíč nevypadá jako OpenAI API key. Nepoužívejte Claude/Anthropic API key.")

    data = _read_env_values()
    data["OPENAI_API_KEY"] = value
    data.setdefault("OPENAI_MODEL", DEFAULT_MODEL)
    data.setdefault("OPENAI_SEARCH_MODEL", DEFAULT_SEARCH_MODEL)
    _write_env_values(data)
    os.environ["OPENAI_API_KEY"] = value


def _read_env_values() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}

    values: dict[str, str] = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _write_env_values(values: dict[str, str]) -> None:
    ordered_keys = ["OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_SEARCH_MODEL"]
    lines: list[str] = []
    for key in ordered_keys:
        if key in values:
            lines.append(f"{key}={values[key]}")
    for key in sorted(values):
        if key not in ordered_keys:
            lines.append(f"{key}={values[key]}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

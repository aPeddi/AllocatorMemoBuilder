"""Runtime configuration, loaded from environment / .env.

Local-first defaults so `./amb` works with zero setup beyond an API key.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # env_file is resolved relative to the process CWD (the repo root, where
    # ./amb runs). extra="ignore" so unrelated env vars never break startup.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = Field("local", alias="AMB_ENV")
    log_level: str = Field("info", alias="AMB_LOG_LEVEL")

    # LLM (Anthropic direct — see ADR-0008)
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    fast_model: str = Field("claude-haiku-4-5-20251001", alias="AMB_MODEL_FAST")
    strong_model: str = Field("claude-sonnet-4-6", alias="AMB_MODEL_STRONG")

    # Storage
    database_url: str = Field("sqlite:///./data/local/amb.sqlite", alias="AMB_DATABASE_URL")

    # Benchmarks / risk-free
    benchmark_mode: str = Field("snapshot", alias="AMB_BENCHMARK_MODE")
    risk_free_annual: float = Field(0.02, alias="AMB_RISK_FREE_ANNUAL")
    # FRED market-data API key. Read server-side only; NEVER sent to the browser.
    # The `./amb serve` proxy uses it so a page can fetch live data without ever
    # exposing the secret client-side.
    fred_api_key: str = Field("", alias="FRED_API_KEY")

    # Local API server (./amb serve)
    serve_host: str = Field("127.0.0.1", alias="AMB_SERVE_HOST")
    serve_port: int = Field(8000, alias="AMB_SERVE_PORT")

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key.strip())

    @property
    def has_fred_key(self) -> bool:
        return bool(self.fred_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""
Pipeline Configuration
========================
Centralised config using Pydantic v2 for strong type validation.
All env vars are loaded from .env (local dev) or GitHub Actions Secrets.
"""
import os
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
load_dotenv()
class PipelineConfig(BaseModel):
    """
    Single source of truth for pipeline settings.
    Extend this class to add new config keys — no changes needed elsewhere.
    """
    # ── Sport selection ──────────────────────────────────────
    sport: str = Field(
        default=os.getenv("SPORT", "football"),
        description="Sport to fetch: 'football' or 'cricket'",
    )
    # ── API settings ─────────────────────────────────────────
    api_base_url: str = Field(
        default=os.getenv(
            "API_BASE_URL", "https://api.football-data.org/v4"
        )
    )
    api_key: str = Field(
        default=os.getenv("FOOTBALL_API_KEY", ""),
        description="API key from environment / GitHub Secret",
    )
    api_timeout_seconds: int = Field(default=30)
    api_max_retries: int = Field(default=3)
    # ── Competition IDs ───────────────────────────────────────
    # PL = Premier League, BL1 = Bundesliga, PD = La Liga
    competition_code: str = Field(
        default=os.getenv("COMPETITION_CODE", "PL"),
    )
    # ── Filesystem paths ──────────────────────────────────────
    base_dir: Path = Field(default=Path(__file__).resolve().parents[1])
    data_dir: Path = Field(default=Path("data"))
    raw_dir: Path = Field(default=Path("data/raw"))
    processed_dir: Path = Field(default=Path("data/processed"))
    reports_dir: Path = Field(default=Path("reports"))
    logs_dir: Path = Field(default=Path("logs"))
    # ── Processing flags ──────────────────────────────────────
    enable_parquet: bool = Field(default=True)
    enable_csv: bool = Field(default=True)
    enable_html_report: bool = Field(default=True)
    # ── [FUTURE] ML flags — set to True to activate ML module ──
    enable_ml_predictions: bool = Field(
        default=os.getenv("ENABLE_ML", "false").lower() == "true"
    )
    enable_nn_features: bool = Field(
        default=os.getenv("ENABLE_NN", "false").lower() == "true"
    )
    @field_validator("sport")
    @classmethod
    def validate_sport(cls, v: str) -> str:
        allowed = {"football", "cricket"}
        if v.lower() not in allowed:
            raise ValueError(f"sport must be one of {allowed}, got '{v}'")
        return v.lower()
    def ensure_dirs(self) -> None:
        """Create all output directories if they don't exist."""
        for d in [
            self.raw_dir,
            self.processed_dir,
            self.reports_dir,
            self.logs_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)
    model_config = {"arbitrary_types_allowed": True}
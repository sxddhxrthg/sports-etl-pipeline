"""
Data Processor Module
========================
Cleans, validates, and engineers features from raw sports data.
Design principle: Every transformation is a pure function
so it can be individually unit-tested and replaced.
Modular hooks are pre-built for:
  - ML feature engineering (Layer 1)
  - Neural network embedding preparation (Layer 2)
"""
import logging
from datetime import datetime
from typing import Tuple
import numpy as np
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema, Check
from rich.console import Console
from rich.table import Table
from pipeline.config import PipelineConfig
logger = logging.getLogger(__name__)
console = Console()
# ──────────────────────────────────────────────────────────────
# Pandera Schemas — Data Quality Contracts
# ──────────────────────────────────────────────────────────────
FOOTBALL_SCHEMA = DataFrameSchema(
    {
        "position": Column(int, Check.greater_than(0), nullable=False),
        "team_name": Column(str, nullable=False),
        "played_games": Column(int, Check.greater_than_or_equal_to(0)),
        "points": Column(int, Check.greater_than_or_equal_to(0)),
        "goals_for": Column(int, Check.greater_than_or_equal_to(0)),
        "goals_against": Column(int, Check.greater_than_or_equal_to(0)),
    },
    coerce=True,
    strict=False,  # allow extra columns
)
CRICKET_SCHEMA = DataFrameSchema(
    {
        "match_id": Column(str, nullable=False),
        "name": Column(str, nullable=False),
        "status": Column(str, nullable=True),
    },
    coerce=True,
    strict=False,
)
class DataProcessor:
    """
    Transforms raw API data into analytics-ready DataFrames.
    Pipeline stages:
        1. Schema coercion & type enforcement
        2. Null/duplicate handling
        3. Derived KPI feature engineering
        4. Statistical normalisation
        5. [HOOK] ML feature preparation
        6. [HOOK] Neural network embedding prep
    """
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
    # ──────────────────────────────────────────────────────────
    # Public entry point
    # ──────────────────────────────────────────────────────────
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full processing pipeline. Returns cleaned, feature-rich DataFrame."""
        sport = self.config.sport
        if sport == "football":
            df = self._process_football(df)
        elif sport == "cricket":
            df = self._process_cricket(df)
        # Universal final steps
        df = self._add_pipeline_metadata(df)
        if self.config.enable_ml_predictions:
            df = self._prepare_ml_features(df)
        if self.config.enable_nn_features:
            df = self._prepare_nn_embeddings(df)
        self._log_summary(df)
        return df
    # ──────────────────────────────────────────────────────────
    # Football processing
    # ──────────────────────────────────────────────────────────
    def _process_football(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Processing football data")
        # ── 1. Clean column types ──────────────────────────────
        numeric_cols = [
            "position", "played_games", "won", "draw", "lost",
            "points", "goals_for", "goals_against", "goal_difference",
            "top_scorer_goals", "top_scorer_assists", "top_scorer_penalties",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # ── 2. Remove duplicates ───────────────────────────────
        before = len(df)
        df = df.drop_duplicates(subset=["team_name"])
        logger.info("Duplicates removed: %d → %d rows", before, len(df))
        # ── 3. Validate schema ─────────────────────────────────
        try:
            df = FOOTBALL_SCHEMA.validate(df, lazy=True)
            logger.info("Schema validation passed")
        except pa.errors.SchemaErrors as err:
            logger.warning("Schema validation issues:\n%s", err.failure_cases)
            # Coerce anyway — don't abort pipeline for minor issues
        # ── 4. Derived KPI features ────────────────────────────
        df = self._engineer_football_features(df)
        return df.sort_values("position").reset_index(drop=True)
    def _engineer_football_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineers domain-specific football KPIs.
        Each feature is independently useful for ML models later.
        """
        eps = 1e-9  # avoid divide-by-zero
        # Win rate
        df["win_rate"] = df["won"] / (df["played_games"] + eps)
        # Points per game
        df["points_per_game"] = df["points"] / (df["played_games"] + eps)
        # Attack vs Defence efficiency
        df["attack_efficiency"] = df["goals_for"] / (df["played_games"] + eps)
        df["defence_efficiency"] = df["goals_against"] / (df["played_games"] + eps)
        # Pythagorean expectation (borrowed from baseball analytics)
        # Predicts true win% from goals scored/conceded
        gf = df["goals_for"].astype(float)
        ga = df["goals_against"].astype(float)
        df["pythagorean_expectation"] = gf**2 / (gf**2 + ga**2 + eps)
        # Form score: W=3, D=1, L=0 from last 5 games
        df["form_score"] = df["form"].apply(self._parse_form_string)
        # Normalise points (z-score) for ML readiness
        df["points_zscore"] = (
            (df["points"] - df["points"].mean()) / (df["points"].std() + eps)
        ).round(4)
        # Performance vs expected (over/underperformance)
        expected_points = df["pythagorean_expectation"] * df["played_games"] * 3
        df["points_vs_expected"] = (df["points"] - expected_points).round(2)
        # Rank within competition (redundant with position but useful for merges)
        df["performance_rank"] = df["points"].rank(ascending=False, method="min")
        logger.info("Engineered %d features", len(df.columns))
        return df
    @staticmethod
    def _parse_form_string(form: str) -> float:
        """
        Converts a form string like 'W,D,L,W,W' into a numeric score.
        Returns NaN if form data is unavailable.
        """
        if not isinstance(form, str) or not form.strip():
            return np.nan
        score_map = {"W": 3.0, "D": 1.0, "L": 0.0}
        results = form.replace(" ", "").split(",")
        scores = [score_map.get(r.upper(), 0.0) for r in results if r]
        return round(np.mean(scores), 2) if scores else np.nan
    # ──────────────────────────────────────────────────────────
    # Cricket processing
    # ──────────────────────────────────────────────────────────
    def _process_cricket(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Processing cricket data")
        # Schema validation
        try:
            df = CRICKET_SCHEMA.validate(df, lazy=True)
        except pa.errors.SchemaErrors as err:
            logger.warning("Cricket schema issues:\n%s", err.failure_cases)
        # Normalise status field
        df["status_category"] = df["status"].apply(self._categorise_match_status)
        # Parse date
        if "date" in df.columns:
            df["match_date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
            df["days_since_match"] = (
                pd.Timestamp.utcnow() - df["match_date"]
            ).dt.days
        df = df.drop_duplicates(subset=["match_id"]).reset_index(drop=True)
        return df
    @staticmethod
    def _categorise_match_status(status: str) -> str:
        if not isinstance(status, str):
            return "unknown"
        s = status.lower()
        if "won" in s or "beat" in s:
            return "completed"
        if "rain" in s or "abandon" in s:
            return "abandoned"
        if "live" in s or "progress" in s:
            return "live"
        return "upcoming"
    # ──────────────────────────────────────────────────────────
    # Universal metadata
    # ──────────────────────────────────────────────────────────
    @staticmethod
    def _add_pipeline_metadata(df: pd.DataFrame) -> pd.DataFrame:
        """Adds lineage columns for debugging and auditing."""
        df["pipeline_run_at"] = datetime.utcnow().isoformat()
        df["pipeline_version"] = "1.0.0"
        return df
    # ──────────────────────────────────────────────────────────
    # [FUTURE HOOK] Machine Learning Feature Layer
    # ──────────────────────────────────────────────────────────
    def _prepare_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        FUTURE LAYER 1: Classical ML Feature Preparation
        ===================================================
        Prepares feature matrix X and target vector y for scikit-learn.
        Planned models:
            - XGBoost match outcome predictor
            - LightGBM title probability estimator
            - Isolation Forest anomaly detector (flag outlier performances)
        To activate:
            1. Set ENABLE_ML=true in GitHub Secrets or .env
            2. Uncomment scikit-learn/xgboost in requirements.txt
            3. Implement pipeline/ml/predictor.py
        Data contract expected here:
            X_features = [
                'win_rate', 'attack_efficiency', 'defence_efficiency',
                'pythagorean_expectation', 'form_score', 'points_zscore'
            ]
            y_target = 'position'  # or 'winner' for match predictions
        """
        logger.info("[HOOK] ML feature preparation — not yet implemented")
        # Placeholder: mark rows as ML-ready
        df["ml_feature_ready"] = True
        return df
    # ──────────────────────────────────────────────────────────
    # [FUTURE HOOK] Neural Network Embedding Layer
    # ──────────────────────────────────────────────────────────
    def _prepare_nn_embeddings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        FUTURE LAYER 2: Neural Network / Deep Learning Prep
        ======================================================
        Prepares time-series sequences and categorical embeddings
        for deep learning models.
        Planned architectures:
            - LSTM for time-series form prediction
            - Transformer for multi-team match outcome modelling
            - Graph Neural Network for league-wide dependency modelling
        To activate:
            1. Set ENABLE_NN=true in GitHub Secrets or .env
            2. Uncomment torch in requirements.txt
            3. Implement pipeline/nn/embedder.py
        Data contract expected here:
            - Sequence length: last N game-weeks
            - Feature tensor shape: (batch, seq_len, n_features)
            - Categorical: team_id → learnable embedding vector
        """
        logger.info("[HOOK] NN embedding preparation — not yet implemented")
        df["nn_embedding_ready"] = True
        return df
    # ──────────────────────────────────────────────────────────
    # Rich terminal summary
    # ──────────────────────────────────────────────────────────
    def _log_summary(self, df: pd.DataFrame) -> None:
        table = Table(
            title="[bold cyan]Processed Data Summary[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")
        table.add_row("Total Rows", str(len(df)))
        table.add_row("Total Columns", str(len(df.columns)))
        table.add_row("Null Cells", str(df.isnull().sum().sum()))
        table.add_row("Duplicate Rows", str(df.duplicated().sum()))
        table.add_row("Pipeline Version", df.get("pipeline_version", pd.Series(["N/A"]))[0])
        console.print(table)

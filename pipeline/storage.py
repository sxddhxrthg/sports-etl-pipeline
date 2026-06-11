"""
Data Storage Module
=====================
Persists processed data in multiple formats:
  - CSV (human-readable, Git-diffable)
  - Parquet (columnar, compressed — production grade)
  - Versioned archive with date-stamped filenames
"""
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from pipeline.config import PipelineConfig
logger = logging.getLogger(__name__)
class DataStorage:
    """
    Saves data to disk in CSV and Parquet formats.
    File naming convention:
        data/processed/football_standings_latest.csv
        data/processed/football_standings_2024-01-15.csv   ← versioned archive
        data/processed/football_standings_latest.parquet
    """
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
    def save(self, df: pd.DataFrame) -> None:
        """Persists DataFrame to all configured formats."""
        sport = self.config.sport
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if self.config.enable_csv:
            self._save_csv(df, sport, today)
        if self.config.enable_parquet:
            self._save_parquet(df, sport, today)
    # ──────────────────────────────────────────────────────────
    # CSV
    # ──────────────────────────────────────────────────────────
    def _save_csv(self, df: pd.DataFrame, sport: str, today: str) -> None:
        out_dir = self.config.processed_dir
        # Latest (always overwritten — tracked by Git diff)
        latest_path = out_dir / f"{sport}_data_latest.csv"
        df.to_csv(latest_path, index=False)
        logger.info("CSV (latest) saved: %s", latest_path)
        # Versioned archive (date-stamped, never overwritten)
        archive_path = out_dir / f"{sport}_data_{today}.csv"
        if not archive_path.exists():
            df.to_csv(archive_path, index=False)
            logger.info("CSV (archive) saved: %s", archive_path)
        else:
            logger.info("Archive for today already exists, skipping: %s", archive_path)
    # ──────────────────────────────────────────────────────────
    # Parquet
    # ──────────────────────────────────────────────────────────
    def _save_parquet(self, df: pd.DataFrame, sport: str, today: str) -> None:
        out_dir = self.config.processed_dir
        # Coerce object columns that Parquet might reject
        df_parquet = df.copy()
        for col in df_parquet.select_dtypes(include=["object"]).columns:
            df_parquet[col] = df_parquet[col].astype(str)
        try:
            latest_path = out_dir / f"{sport}_data_latest.parquet"
            df_parquet.to_parquet(latest_path, index=False, compression="snappy")
            logger.info("Parquet (latest) saved: %s", latest_path)
            archive_path = out_dir / f"{sport}_data_{today}.parquet"
            if not archive_path.exists():
                df_parquet.to_parquet(archive_path, index=False, compression="snappy")
                logger.info("Parquet (archive) saved: %s", archive_path)
        except ImportError:
            logger.warning(
                "Parquet engine (pyarrow/fastparquet) not installed — skipping Parquet output. "
                "Install pyarrow to enable: pip install pyarrow"
            )

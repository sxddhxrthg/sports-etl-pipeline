"""
Automated Sports Data Pipeline
================================
Fetches, cleans, and structures sports data daily via GitHub Actions.
Architecture is modular to support future additions:
  - ML prediction layer (scikit-learn)
  - Neural network integration (PyTorch/TensorFlow)
  - Time-series forecasting
  - Anomaly detection
Author: Siddharth Ganesh
"""
import logging
import sys
from pathlib import Path
from pipeline.config import PipelineConfig
from pipeline.fetcher import DataFetcher
from pipeline.processor import DataProcessor
from pipeline.storage import DataStorage
from pipeline.reporter import PipelineReporter
# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────
# Ensure logs directory exists before FileHandler tries to open it
Path("logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/pipeline.log", mode="a"),
    ],
)
logger = logging.getLogger("main")
def run_pipeline() -> None:
    """
    Orchestrates the full ETL pipeline.
    Steps:
        1. Load configuration
        2. Fetch raw data from API
        3. Clean & transform data
        4. Persist processed data
        5. Generate summary report
    """
    logger.info("=" * 60)
    logger.info("  SPORTS DATA PIPELINE — STARTING RUN")
    logger.info("=" * 60)
    # 1. Configuration
    config = PipelineConfig()
    logger.info("Configuration loaded: sport=%s", config.sport)
    # 2. Fetch
    fetcher = DataFetcher(config)
    raw_data = fetcher.fetch_all()
    if raw_data is None or raw_data.empty:
        logger.error("No data fetched. Aborting pipeline.")
        sys.exit(1)
    logger.info("Raw data fetched: %d rows", len(raw_data))
    # 3. Process
    processor = DataProcessor(config)
    processed_data = processor.run(raw_data)
    logger.info("Data processed: %d rows, %d features", *processed_data.shape)
    # 4. Store
    storage = DataStorage(config)
    storage.save(processed_data)
    # 5. Report
    reporter = PipelineReporter(config)
    reporter.generate(processed_data)
    logger.info("=" * 60)
    logger.info("  PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
if __name__ == "__main__":
    run_pipeline()

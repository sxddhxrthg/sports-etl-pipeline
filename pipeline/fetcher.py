"""
Data Fetcher Module
======================
Handles HTTP requests to sports APIs with:
  - Tenacity-based retry logic (exponential backoff)
  - Request caching to avoid redundant calls during dev
  - Timeout enforcement
  - Graceful fallback to cached data on failure
"""
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
import requests
import requests_cache
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    RetryError,
)
from pipeline.config import PipelineConfig
logger = logging.getLogger(__name__)
# Install a filesystem cache for dev — GitHub Actions gets a fresh cache per run
requests_cache.install_cache(
    cache_name="data/.api_cache",
    backend="filesystem",
    expire_after=3600,  # 1 hour
)
class DataFetcher:
    """
    Fetches raw sports data from a public API.
    Supports:
        - football-data.org  (Premier League, Bundesliga, etc.)
        - cricapi.com        (IPL, international cricket)
    The class is easily extendable: add a new `_fetch_<sport>` method
    and register it in `SPORT_HANDLERS`.
    """
    FOOTBALL_HEADERS = {
        "X-Auth-Token": "",  # filled from config
        "Accept": "application/json",
    }
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        config.ensure_dirs()
        self.session = self._build_session()
        # Sport → fetch method registry (open/closed principle)
        self.SPORT_HANDLERS = {
            "football": self._fetch_football,
            "cricket": self._fetch_cricket,
        }
    # ──────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────
    def fetch_all(self) -> Optional[pd.DataFrame]:
        """
        Entry point. Dispatches to the correct sport handler.
        Returns a raw DataFrame or None on unrecoverable error.
        """
        handler = self.SPORT_HANDLERS.get(self.config.sport)
        if handler is None:
            logger.error("No handler for sport: %s", self.config.sport)
            return None
        try:
            return handler()
        except RetryError as exc:
            logger.critical("All retries exhausted: %s", exc)
            return self._load_fallback_cache()
        except Exception as exc:  # noqa: BLE001
            logger.critical("Unexpected fetcher error: %s", exc, exc_info=True)
            return self._load_fallback_cache()
    # ──────────────────────────────────────────────────────────
    # Football (football-data.org — free tier)
    # ──────────────────────────────────────────────────────────
    def _fetch_football(self) -> pd.DataFrame:
        """Fetches Premier League matches for the current season."""
        logger.info(
            "Fetching football data: competition=%s", self.config.competition_code
        )
        # ── Standings ───────────────────────────────────────
        standings_url = (
            f"{self.config.api_base_url}/competitions/"
            f"{self.config.competition_code}/standings"
        )
        standings_resp = self._get(standings_url)
        standings_df = self._parse_football_standings(standings_resp)
        # ── Scorers ─────────────────────────────────────────
        scorers_url = (
            f"{self.config.api_base_url}/competitions/"
            f"{self.config.competition_code}/scorers?limit=20"
        )
        scorers_resp = self._get(scorers_url)
        scorers_df = self._parse_football_scorers(scorers_resp)
        # ── Merge into unified frame ─────────────────────────
        df = standings_df.merge(
            scorers_df, left_on="team_name", right_on="team_name", how="left"
        )
        df["fetched_at"] = datetime.utcnow().isoformat()
        df["source"] = "football-data.org"
        # Save raw snapshot
        raw_path = self.config.raw_dir / f"football_raw_{self._today()}.json"
        raw_path.write_text(
            standings_resp.text + "\n---SCORERS---\n" + scorers_resp.text
        )
        logger.info("Raw snapshot saved to %s", raw_path)
        return df
    def _parse_football_standings(self, response: requests.Response) -> pd.DataFrame:
        data = response.json()
        rows = []
        # football-data.org returns a list of standing types; 'TOTAL' is the main one
        for standing_type in data.get("standings", []):
            if standing_type.get("type") != "TOTAL":
                continue
            for entry in standing_type.get("table", []):
                team = entry.get("team", {})
                rows.append(
                    {
                        "position": entry.get("position"),
                        "team_name": team.get("name"),
                        "team_id": team.get("id"),
                        "played_games": entry.get("playedGames"),
                        "won": entry.get("won"),
                        "draw": entry.get("draw"),
                        "lost": entry.get("lost"),
                        "points": entry.get("points"),
                        "goals_for": entry.get("goalsFor"),
                        "goals_against": entry.get("goalsAgainst"),
                        "goal_difference": entry.get("goalDifference"),
                        "form": entry.get("form", ""),
                    }
                )
        return pd.DataFrame(rows)
    def _parse_football_scorers(self, response: requests.Response) -> pd.DataFrame:
        data = response.json()
        rows = []
        for scorer in data.get("scorers", []):
            player = scorer.get("player", {})
            team = scorer.get("team", {})
            rows.append(
                {
                    "team_name": team.get("name"),
                    "top_scorer": player.get("name"),
                    "top_scorer_goals": scorer.get("goals"),
                    "top_scorer_assists": scorer.get("assists"),
                    "top_scorer_penalties": scorer.get("penalties"),
                }
            )
        return pd.DataFrame(rows)
    # ──────────────────────────────────────────────────────────
    # Cricket (cricapi.com — free tier, 100 calls/day)
    # ──────────────────────────────────────────────────────────
    def _fetch_cricket(self) -> pd.DataFrame:
        """Fetches current series and match data from CricAPI."""
        logger.info("Fetching cricket data from CricAPI")
        url = "https://api.cricapi.com/v1/currentMatches"
        params = {
            "apikey": self.config.api_key or "demo",
            "offset": 0,
        }
        resp = self._get(url, params=params)
        data = resp.json()
        rows = []
        for match in data.get("data", []):
            rows.append(
                {
                    "match_id": match.get("id"),
                    "name": match.get("name"),
                    "status": match.get("status"),
                    "venue": match.get("venue"),
                    "date": match.get("date"),
                    "team1": match.get("teams", [None, None])[0],
                    "team2": match.get("teams", [None, None])[1],
                    "winner": match.get("matchWinner"),
                    "score": str(match.get("score", [])),
                    "fetched_at": datetime.utcnow().isoformat(),
                    "source": "cricapi.com",
                }
            )
        if not rows:
            logger.warning("No cricket matches returned from API")
        return pd.DataFrame(rows)
    # ──────────────────────────────────────────────────────────
    # HTTP utilities
    # ──────────────────────────────────────────────────────────
    @retry(
        retry=retry_if_exception_type(
            (requests.Timeout, requests.ConnectionError, requests.HTTPError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=False,
    )
    def _get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        """
        Makes a GET request with automatic retry and timeout enforcement.
        Raises HTTPError for 4xx/5xx so tenacity can retry.
        """
        logger.debug("GET %s", url)
        response = self.session.get(
            url,
            params=params,
            timeout=self.config.api_timeout_seconds,
        )
        # 429 = rate limited — wait and retry
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning("Rate limited. Waiting %ds before retry.", retry_after)
            time.sleep(retry_after)
        response.raise_for_status()
        return response
    def _build_session(self) -> requests.Session:
        session = requests.Session()
        if self.config.sport == "football":
            session.headers.update(
                {"X-Auth-Token": self.config.api_key}
            )
        session.headers.update({"User-Agent": "sports-data-pipeline/1.0"})
        return session
    def _load_fallback_cache(self) -> Optional[pd.DataFrame]:
        """
        Falls back to the most recently saved processed CSV if API fails.
        This prevents the pipeline from breaking on transient network issues.
        """
        processed_dir = self.config.processed_dir
        csv_files = sorted(processed_dir.glob("*.csv"), reverse=True)
        if csv_files:
            logger.warning(
                "API failed — loading fallback data: %s", csv_files[0]
            )
            return pd.read_csv(csv_files[0])
        logger.error("No fallback cache found. Pipeline cannot proceed.")
        return None
    @staticmethod
    def _today() -> str:
        return datetime.utcnow().strftime("%Y-%m-%d")
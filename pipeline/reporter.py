"""
Pipeline Reporter Module
==========================
Generates human-readable reports after each pipeline run:
  - Terminal table via Rich
  - Matplotlib charts committed to the repo
  - HTML report via Jinja2 (viewable in GitHub Pages)
"""
import logging
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for CI
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from jinja2 import Template
from pipeline.config import PipelineConfig
logger = logging.getLogger(__name__)
# ──────────────────────────────────────────────────────────────
# HTML Template
# ──────────────────────────────────────────────────────────────
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sports Data Pipeline Report — {{ run_date }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; margin: 0; padding: 2rem; }
        h1   { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem; }
        h2   { color: #79c0ff; margin-top: 2rem; }
        table{ width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th   { background: #161b22; color: #58a6ff; padding: 10px; text-align: left; border: 1px solid #30363d; }
        td   { padding: 8px 10px; border: 1px solid #21262d; }
        tr:nth-child(even) { background: #161b22; }
        .badge { background: #238636; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }
        .meta  { color: #8b949e; font-size: 0.9em; margin-bottom: 1rem; }
        img    { max-width: 100%; border-radius: 8px; margin-top: 1rem; }
    </style>
</head>
<body>
    <h1>⚽ Sports Data Pipeline — Automated Report</h1>
    <p class="meta">Generated: {{ run_date }} UTC &nbsp;|&nbsp; Sport: <strong>{{ sport }}</strong> &nbsp;|&nbsp; Rows: <strong>{{ row_count }}</strong></p>
    <span class="badge">Pipeline v{{ pipeline_version }}</span>
    <h2>📊 Data Table</h2>
    {{ table_html }}
    <h2>📈 Visualisations</h2>
    {% for chart in charts %}
    <img src="{{ chart }}" alt="Pipeline Chart">
    {% endfor %}
    <h2>🔧 Pipeline Health</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        {% for k, v in stats.items() %}
        <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
        {% endfor %}
    </table>
</body>
</html>
"""
class PipelineReporter:
    """Generates charts and HTML reports from processed data."""
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
    def generate(self, df: pd.DataFrame) -> None:
        """Generates all reports. Called after processing."""
        charts = []
        if self.config.sport == "football":
            charts = self._generate_football_charts(df)
        if self.config.enable_html_report:
            self._generate_html_report(df, charts)
    # ──────────────────────────────────────────────────────────
    # Football Charts
    # ──────────────────────────────────────────────────────────
    def _generate_football_charts(self, df: pd.DataFrame) -> list[str]:
        charts = []
        # Set global style
        plt.style.use("dark_background")
        colors = plt.cm.plasma(np.linspace(0.3, 0.9, len(df)))  # noqa
        # ── Chart 1: Points Table ──────────────────────────────
        if "team_name" in df.columns and "points" in df.columns:
            chart_path = self._plot_points_table(df, colors)
            charts.append(chart_path)
        # ── Chart 2: Attack vs Defence ─────────────────────────
        if "attack_efficiency" in df.columns:
            chart_path = self._plot_attack_defence(df)
            charts.append(chart_path)
        # ── Chart 3: Pythagorean vs Actual Points ──────────────
        if "pythagorean_expectation" in df.columns:
            chart_path = self._plot_pythagorean(df)
            charts.append(chart_path)
        return charts
    def _plot_points_table(self, df: pd.DataFrame, colors) -> str:
        top_n = df.nlargest(10, "points")
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.barh(top_n["team_name"], top_n["points"], color=colors[:len(top_n)])
        ax.set_xlabel("Points", color="#8b949e")
        ax.set_title("Premier League — Top 10 Teams by Points", color="#58a6ff", fontsize=14, pad=15)
        ax.invert_yaxis()
        ax.tick_params(colors="#e6edf3")
        ax.spines[["top", "right"]].set_visible(False)
        for bar, val in zip(bars, top_n["points"]):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{int(val)}", va="center", color="#e6edf3", fontsize=9)
        plt.tight_layout()
        path = str(self.config.reports_dir / "chart_points_table.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#0d1117")
        plt.close(fig)
        logger.info("Chart saved: %s", path)
        return Path(path).name  # relative path for HTML
    def _plot_attack_defence(self, df: pd.DataFrame) -> str:
        fig, ax = plt.subplots(figsize=(10, 8))
        scatter = ax.scatter(
            df["attack_efficiency"],
            df["defence_efficiency"],
            c=df["points"],
            cmap="plasma",
            s=100,
            alpha=0.8,
            edgecolors="#30363d",
        )
        for _, row in df.iterrows():
            ax.annotate(
                row["team_name"].split()[-1],  # last word of team name
                (row["attack_efficiency"], row["defence_efficiency"]),
                fontsize=7,
                color="#8b949e",
                xytext=(3, 3),
                textcoords="offset points",
            )
        plt.colorbar(scatter, ax=ax, label="Points")
        ax.set_xlabel("Attack Efficiency (Goals/Game)", color="#8b949e")
        ax.set_ylabel("Goals Conceded/Game (lower=better)", color="#8b949e")
        ax.set_title("Attack vs Defence Efficiency Map", color="#58a6ff", fontsize=14, pad=15)
        ax.tick_params(colors="#e6edf3")
        ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        path = str(self.config.reports_dir / "chart_attack_defence.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#0d1117")
        plt.close(fig)
        logger.info("Chart saved: %s", path)
        return Path(path).name
    def _plot_pythagorean(self, df: pd.DataFrame) -> str:
        fig, ax = plt.subplots(figsize=(10, 6))
        if "points_vs_expected" in df.columns:
            sorted_df = df.sort_values("points_vs_expected")
            colors = ["#f85149" if x < 0 else "#3fb950" for x in sorted_df["points_vs_expected"]]
            ax.barh(sorted_df["team_name"], sorted_df["points_vs_expected"], color=colors)
            ax.axvline(0, color="#8b949e", linewidth=0.8, linestyle="--")
            ax.set_xlabel("Points vs Pythagorean Expected", color="#8b949e")
            ax.set_title("Over/Underperformance vs Expected Points", color="#58a6ff", fontsize=14, pad=15)
            ax.tick_params(colors="#e6edf3")
            ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        path = str(self.config.reports_dir / "chart_pythagorean.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#0d1117")
        plt.close(fig)
        logger.info("Chart saved: %s", path)
        return Path(path).name
    # ──────────────────────────────────────────────────────────
    # HTML Report
    # ──────────────────────────────────────────────────────────
    def _generate_html_report(self, df: pd.DataFrame, charts: list[str]) -> None:
        display_cols = [
            c for c in [
                "position", "team_name", "played_games", "points",
                "won", "draw", "lost", "goals_for", "goals_against",
                "win_rate", "points_per_game", "pythagorean_expectation", "form_score",
            ]
            if c in df.columns
        ]
        table_html = df[display_cols].head(20).to_html(
            index=False,
            classes="data-table",
            border=0,
            float_format=lambda x: f"{x:.3f}",
        )
        stats = {
            "Total Teams": len(df),
            "Total Columns": len(df.columns),
            "Null Values": int(df.isnull().sum().sum()),
            "Run Timestamp (UTC)": datetime.utcnow().isoformat(),
            "ML Features Ready": str(df.get("ml_feature_ready", pd.Series([False]))[0]),
            "NN Embeddings Ready": str(df.get("nn_embedding_ready", pd.Series([False]))[0]),
        }
        template = Template(HTML_TEMPLATE)
        html = template.render(
            run_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            sport=self.config.sport,
            row_count=len(df),
            pipeline_version=df.get("pipeline_version", pd.Series(["1.0.0"]))[0],
            table_html=table_html,
            charts=charts,
            stats=stats,
        )
        report_path = self.config.reports_dir / "pipeline_report.html"
        report_path.write_text(html, encoding="utf-8")
        logger.info("HTML report saved: %s", report_path)
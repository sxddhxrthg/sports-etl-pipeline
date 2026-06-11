# Automated Sports Data Pipeline 🏆
[![Pipeline Status](https://github.com/YOUR_GITHUB_USERNAME/sports-data-pipeline/actions/workflows/data_pipeline.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/sports-data-pipeline/actions)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![pandas](https://img.shields.io/badge/pandas-2.2-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
> An end-to-end, fully automated **Data Engineering** pipeline that fetches, cleans, and structures live sports data daily via GitHub Actions. Built with enterprise-grade modularity to support future ML/NN layers.
---
## 📐 System Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                        GitHub Actions (Cron)                        │
│                     Triggers daily at 00:00 UTC                     │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          main.py (Orchestrator)                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐    │
│  │  Config  │──▶│ Fetcher  │──▶│Processor │──▶│   Storage    │    │
│  │(Pydantic)│   │(Tenacity)│   │(Pandera) │   │(CSV+Parquet) │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────────┘    │
│                                      │                              │
│                               ┌──────────────┐                     │
│                               │   Reporter   │                     │
│                               │  (Matplotlib │                     │
│                               │  + Jinja2)   │                     │
│                               └──────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │   Git Commit & Push     │
         │  (auto-updates repo     │
         │   + contribution graph) │
         └─────────────────────────┘
```
---
## ✨ Features
|
 Feature 
|
 Status 
|
|
---
|
---
|
|
 Daily automated data fetch (Premier League) 
|
 ✅ Active 
|
|
 Exponential backoff retry (3 attempts) 
|
 ✅ Active 
|
|
 Response caching (avoids redundant API hits) 
|
 ✅ Active 
|
|
 Schema validation (Pandera) 
|
 ✅ Active 
|
|
 Feature engineering (8 KPIs) 
|
 ✅ Active 
|
|
 Dual output: CSV + Parquet 
|
 ✅ Active 
|
|
 Dark-themed Matplotlib charts 
|
 ✅ Active 
|
|
 HTML pipeline report 
|
 ✅ Active 
|
|
 Graceful fallback to cached data 
|
 ✅ Active 
|
|
 Classical ML predictions (XGBoost) 
|
 🔜 Layer 1 
|
|
 Neural network forecasting (PyTorch LSTM) 
|
 🔜 Layer 2 
|
---
## 🗂️ Project Structure
```
sports-data-pipeline/
├── main.py                          # Orchestrator — runs the full ETL
├── requirements.txt                 # All Python dependencies (pinned)
├── .env.example                     # Environment variables template
│
├── pipeline/                        # Core modular ETL package
│   ├── __init__.py
│   ├── config.py                    # Pydantic v2 config (type-safe)
│   ├── fetcher.py                   # HTTP client + retry logic
│   ├── processor.py                 # Clean, validate, engineer features
│   ├── storage.py                   # Persist CSV / Parquet
│   └── reporter.py                  # Charts + HTML report
│
├── data/
│   ├── raw/                         # Raw API snapshots (date-stamped)
│   └── processed/
│       ├── football_data_latest.csv     # ← tracked in Git
│       └── football_data_2024-01-15.csv # ← versioned archive
│
├── reports/
│   ├── pipeline_report.html         # Self-contained HTML report
│   ├── chart_points_table.png
│   ├── chart_attack_defence.png
│   └── chart_pythagorean.png
│
├── logs/
│   └── pipeline.log                 # Rotating run log
│
└── .github/
    └── workflows/
        └── data_pipeline.yml        # GitHub Actions CI/CD
```
---
## 🚀 Quick Start
### 1. Get a Free API Key
Register at [football-data.org](https://www.football-data.org/client/register) — it's free, takes 30 seconds, and gives you access to Premier League, Bundesliga, La Liga, and more.
### 2. Clone & Configure
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/sports-data-pipeline.git
cd sports-data-pipeline
# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
# Set up environment variables
cp .env.example .env
# Edit .env and add your FOOTBALL_API_KEY
```
### 3. Run Locally
```bash
python main.py
```
Output:
```
2024-01-15 00:00:01 | INFO     | main | Configuration loaded: sport=football
2024-01-15 00:00:01 | INFO     | fetcher | Fetching football data: competition=PL
2024-01-15 00:00:03 | INFO     | fetcher | Raw snapshot saved to data/raw/football_raw_2024-01-15.json
2024-01-15 00:00:03 | INFO     | processor | Schema validation passed
2024-01-15 00:00:03 | INFO     | processor | Engineered 20 features
2024-01-15 00:00:03 | INFO     | storage | CSV (latest) saved: data/processed/football_data_latest.csv
2024-01-15 00:00:04 | INFO     | reporter | HTML report saved: reports/pipeline_report.html
2024-01-15 00:00:04 | INFO     | main | PIPELINE COMPLETED SUCCESSFULLY
```
---
## ⚙️ GitHub Actions Setup
### Step 1: Add your API key as a GitHub Secret
```
GitHub Repository → Settings → Secrets and variables → Actions → New repository secret
```
|
 Secret Name 
|
 Value 
|
|
---
|
---
|
|
`FOOTBALL_API_KEY`
|
 Your football-data.org API key 
|
### Step 2: Configure Your Git Identity
Open [`.github/workflows/data_pipeline.yml`](.github/workflows/data_pipeline.yml) and replace the placeholders:
```yaml
- name: Commit and push data
  run: |
    git config --global user.name "YOUR_GITHUB_USERNAME"      # ← your username
    git config --global user.email "YOUR_EMAIL@example.com"   # ← your GitHub email
    git add .
    git commit -m "Automated daily data pipeline update [skip ci]" || exit 0
    git push
```
> **Important**: Your email must match the one on your GitHub account (`github.com/settings/emails`) for commits to appear on your contribution graph.
### Step 3: Push to GitHub
```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/sports-data-pipeline.git
git add .
git commit -m "Initial commit: automated sports data pipeline"
git push -u origin main
```
The pipeline will automatically run at **00:00 UTC daily**, or you can trigger it manually from the **Actions** tab.
---
## 📊 Engineered Features
The processor engineers the following KPIs from raw standings data:
|
 Feature 
|
 Formula 
|
 Purpose 
|
|
---
|
---
|
---
|
|
`win_rate`
|
 wins / games_played 
|
 Team consistency 
|
|
`points_per_game`
|
 points / games_played 
|
 Form normalisation 
|
|
`attack_efficiency`
|
 goals_for / games_played 
|
 Scoring threat 
|
|
`defence_efficiency`
|
 goals_against / games_played 
|
 Defensive solidity 
|
|
`pythagorean_expectation`
|
 GF² / (GF² + GA²) 
|
 True performance indicator 
|
|
`form_score`
|
 Avg of last 5 results (W=3, D=1, L=0) 
|
 Recent momentum 
|
|
`points_zscore`
|
 (points - mean) / std 
|
 ML normalisation 
|
|
`points_vs_expected`
|
 actual - pythagorean expected 
|
 Over/underperformance 
|
---
## 🔮 Enterprise Upgrade Roadmap
### Layer 1: Classical ML Predictions (scikit-learn / XGBoost)
**What**: Train an XGBoost classifier on historical standings data to predict:
- **Match outcomes** (home win / draw / away win) with ~70% accuracy
- **Final league positions** at mid-season (regression)
- **Anomaly detection** — flag statistical outliers with Isolation Forest
**Implementation plan**:
```python
# pipeline/ml/predictor.py (planned)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
ml_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', XGBClassifier(n_estimators=100, max_depth=4))
])
```
**To activate**: Set `ENABLE_ML=true` in GitHub Secrets + uncomment scikit-learn in `requirements.txt`.
---
### Layer 2: Neural Network Forecasting (PyTorch LSTM)
**What**: A sequence model that treats each game-week as a time-step and learns temporal patterns:
- **LSTM encoder** ingests the last N game-weeks of team stats
- **Attention mechanism** weights more recent matches higher
- **Output**: probability distribution over next-match outcomes
- **Team embeddings**: learnable vectors per team (like word2vec for teams)
**Architecture sketch**:
```
Input: (batch, seq_len=5, n_features=8)
    → LSTM(hidden=64) → Attention → Dropout(0.3)
    → Linear(64 → 3) → Softmax
Output: [P(Home Win), P(Draw), P(Away Win)]
```
**To activate**: Set `ENABLE_NN=true` in GitHub Secrets + uncomment torch in `requirements.txt`.
> The current data structure is **already shaped** for both of these layers. The `ml_feature_ready` and `nn_embedding_ready` columns in the output data confirm readiness.
---
## 🛡️ Error Handling
|
 Scenario 
|
 Behaviour 
|
|
---
|
---
|
|
 API timeout (>30s) 
|
 Retry up to 3x with exponential backoff 
|
|
 429 Rate Limited 
|
 Honour 
`Retry-After`
 header, then retry 
|
|
 Network failure 
|
 Fall back to most recent processed CSV 
|
|
 Bad/null data 
|
 Log warning, coerce types, continue pipeline 
|
|
 Schema violation 
|
 Log warning (non-fatal), pipeline continues 
|
|
 Full pipeline crash 
|
 GitHub Actions marks run as failed, logs preserved for 30 days 
|
---
## 🛠️ Tech Stack
|
 Layer 
|
 Technology 
|
 Role 
|
|
---
|
---
|
---
|
|
 Language 
|
 Python 3.11 
|
 Pipeline logic 
|
|
 HTTP 
|
`requests`
 + 
`tenacity`
|
 Fault-tolerant API calls 
|
|
 Data 
|
`pandas`
 + 
`numpy`
|
 Transform & engineer features 
|
|
 Validation 
|
`pandera`
 + 
`pydantic`
|
 Data contracts & config 
|
|
 Storage 
|
`pyarrow`
 (Parquet) 
|
 Columnar compressed output 
|
|
 Reporting 
|
`matplotlib`
 + 
`jinja2`
|
 Charts & HTML reports 
|
|
 CI/CD 
|
 GitHub Actions 
|
 Daily scheduling & automation 
|
|
 Config 
|
`python-dotenv`
|
 Secrets management 
|
---
## 📄 License
MIT — free to use, modify, and distribute.
---
*Built as a placement-ready Data Engineering portfolio project. Demonstrates CI/CD automation, ETL design patterns, data quality validation, and a clear upgrade path to production-grade ML systems.*

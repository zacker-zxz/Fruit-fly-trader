# FRUIT-FLY TRADER

A research simulation of a connectome-inspired trading brain. Market data enters
as sensory signals, propagates through a subset of the publicly released
Drosophila connectome topology, and produces BUY / HOLD / SELL decisions. A
risk-adjusted reward signal modulates synaptic plasticity; inactive or
unhelpful neurons and synapses are pruned. Every structural change is logged.

This is a research instrument, not a trading product. It executes nothing and
connects to no broker.

## Structure

```
backend/
  engine/        connectome parsing, neurons, synapses, plasticity, pruning
  market/        CSV ingestion, features, replay environment
  trading/       portfolio, execution, metrics
  experiments/   config-driven runs, baselines, manifests
  api/           FastAPI server, SSE event stream
  tests/
frontend/        React + Vite dashboard with 2D neural canvas
data/
  raw/           drop OHLCV CSVs here (see schema below)
  processed/
  connectome/    downloaded connectome edge lists
```

## Data schema

CSV files in `data/raw/` must have columns:

```
timestamp,open,high,low,close,volume
```

Timestamps are ISO 8601 or epoch seconds. No API keys are used or required.

## Setup

```
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m engine.connectome_download   # fetches public connectome edge lists
python -m uvicorn api.server:app --reload
```

Frontend:

```
cd frontend
npm install
npm run dev
```

## Reproducibility

Every run records a manifest: dataset file and hash, symbol, period, seed,
brain configuration, learning and pruning parameters, and full results.
Given the same seed and inputs, the run is deterministic.

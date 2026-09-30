# 🪰 FRUIT-FLY TRADER

> **A Bio-Computational Connectome Trading Research Simulation**  
> Simulating high-frequency financial decision-making over authentic *Drosophila melanogaster* connectome subgraphs with neuromodulatory feedback, Hebbian synaptic plasticity, and an ultra-low-latency cyber-tech trading desk.

---

## ⚡ Overview

**Fruit-Fly Trader** is an experimental research instrument that maps financial market tick streams into the anatomical compartments of a biological fruit fly brain (*Drosophila melanogaster*). 

Unlike black-box statistical models or brute-force deep learning, this system grounds trading actions in:
- **Sensory Transduction**: Real market features (volatility, momentum, RSI, patterns, turbulence) transduce directly into the **Optic Lobe** (compound eyes) and **Antennal Lobe** (antennae).
- **Steering & Memory**: Synaptic activations propagate across the **Central Complex** (heading steering) and **Mushroom Body Kenyon Cells** (associative learning & memory bias).
- **Neuromodulatory Feedback**: Trade outcomes trigger surges in **Dopamine** (reward/profit), **Cortisol** (stress/drawdown defense), **Octopamine** (market turbulence arousal), and **Serotonin** (impulse control).
- **Dynamic Plasticity & Pruning**: Synapses undergo three-factor Hebbian plasticity, and inactive neural pathways are structurally pruned.
- **Micro-Leverage Execution**: Executes directional micro-trades with variable stochastic hold durations, bracket profit-taking, and dual **INR (₹) / USD ($)** margin accounting.

> **Disclaimer**: This software is purely a bio-computational research instrument and simulation engine. It connects to no real-money broker and does not provide financial or investment advice.

---

## 🏛️ System Architecture

```text
               ┌────────────────────────────────────────────────────────┐
               │              REAL MARKET DATA / REPLAY FEED            │
               │   (Crypto: BTC/ETH/SOL | Equity: NIFTY/RELIANCE | MCX) │
               └───────────────────────────┬────────────────────────────┘
                                           │
                        1. SENSORY TRANSDUCTION (OHLCV + Features)
                                           ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                     DROSOPHILA CONNECTOME BRAIN ENGINE                            │
│                                                                                   │
│   ┌────────────────────────┐                   ┌──────────────────────────────┐   │
│   │  OPTIC LOBE (Eyes)     │                   │  ANTENNAL LOBE (Antennae)    │   │
│   │  Price action, Trend,  │                   │  Volatility, Volume surges,  │   │
│   │  RSI, Reversal bands   │                   │  Breakout turbulence         │   │
│   └───────────┬────────────┘                   └──────────────┬───────────────┘   │
│               │                                               │                   │
│               ▼                                               ▼                   │
│   ┌───────────────────────────────────────────────────────────────────────────┐   │
│   │                       CENTRAL COMPLEX & MUSHROOM BODY                     │   │
│   │  - Kenyon cell associative memory bias                                    │   │
│   │  - Heading direction steering (UP / DOWN / HOLD)                          │   │
│   │  - Biological stochastic noise & threshold jitter                         │   │
│   └─────────────────────────────────────┬─────────────────────────────────────┘   │
│                                         │                                         │
│                                         ▼                                         │
│   ┌───────────────────────────────────────────────────────────────────────────┐   │
│   │                     DESCENDING MOTOR NEURONS                              │   │
│   │  Motor Commands:  ▲ BUY (UP)   |   ⏸ HOLD   |   ▼ SELL (DOWN)            │   │
│   └─────────────────────────────────────┬─────────────────────────────────────┘   │
│                                         │                                         │
│                                         ▼                                         │
│   ┌───────────────────────────────────────────────────────────────────────────┐   │
│   │                       NEUROMODULATION & PLASTICITY                        │   │
│   │  - Dopamine (Profit boost)       - Cortisol (Drawdown risk defense)       │   │
│   │  - Octopamine (Arousal/Turbulence)- Serotonin (Impulse control)           │   │
│   │  - Three-factor Hebbian trace updates & Structural Synaptic Pruning       │   │
│   └───────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                        2. MICRO-TRADING ENGINE (Dual INR/USD)
                                          │
                     ┌────────────────────┴────────────────────┐
                     ▼                                         ▼
        FastAPI SSE Event Stream                  React 18 + Vite Cyber-Tech UI
        - /api/events (SSE)                       - 60 FPS HTML5 Canvas Charts
        - Non-blocking async loop                 - 3D Connectome Soma Visualizer
        - Zero thread contention                  - Real-time PnL & Order Book
```

---

## ✨ Key Features

### 1. Authentic Drosophila Connectome
- Connects to public, open-access *Drosophila* synapse datasets (Zheng et al. / FlyConnectome).
- Automatically downloads or creates a clustered small-world scaffold fallback if offline.
- Simulates hundreds of biologically clustered neurons with Leaky Integrate-and-Fire (LIF) dynamics, refractory periods, and membrane noise.

### 2. Live Neuromodulation Telemetry
- **Dopamine ($DA$)**: Rises on successful take-profits, increasing subsequent risk appetite.
- **Cortisol**: Spikes during adverse trade moves, triggering defensive exit reflex (`CORTISOL_DEFENSE`).
- **Octopamine ($OA$)**: Scales with market turbulence, sharpening optical perception gain.
- **Serotonin ($5\text{-}HT$)**: Governs impulse control, preventing over-trading and rapid flipping.

### 3. High-Frequency Micro-Trading Desk & Autonomous Exits
- **Dual Currency Accounting**: Primary INR (₹) wallet with live USD ($) conversion.
- **Configurable Multiplier Leverage**: 1x, 2x, 5x, 10x, 20x, 50x.
- **Multi-Position Tracking**: Supports multiple concurrent active trades, each with independent entry price, margin stake, and stochastic hold duration (5s to 60s).
- **Autonomous Biological Exits (Default)**: Instead of rigid static percentages, the fruit fly's neural connectome dynamically decides when to take profit and cut loss based on:
  - **Dopamine Satiation (`DOPAMINE_SATISFACTION`)**: Locks in gains dynamically when reward centers surge (+0.4%~+0.8%).
  - **Cortisol Defense (`CORTISOL_DEFENSE`)**: Stress reflex cuts losses early to protect capital during adverse market shocks.
  - **Trailing Momentum Protection (`TRAILING_PROFIT`)**: Locks in gains if price retraces >30% from peak return.
  - **Optic Sensory Reversal (`AUTO_PROFIT_BOOKED`)**: Compound eyes detect oscillator divergence (RSI) and counter-momentum.
  - **Central Complex Motor Reversal (`BRAIN_REVERSAL`)**: Steering neurons actively flip direction against the active trade.
- **Manual Bracket Mode Option**: If desired, users can toggle **Manual TP/SL Brackets** in Settings to enforce fixed percentage take-profit and stop-loss targets.

### 4. Interactive Cyber-Tech UI
- **Trading Desk Canvas**: Native HTML5 Canvas rendering high-density candlestick bars, volume histogram, moving averages, and live execution arrows (`▲ UP`, `▼ DN`).
- **3D Connectome Visualizer**: Renders active somatic clusters across Optic, Antennal, Mushroom Body, and Central Complex networks.
- **Full Simulation Controls**:
  - `▶ START`: Initiates the simulation on demand (does not auto-start unexpectedly).
  - `⏹ STOP`: Pauses the active run in place preserving all candlestick chart history, PnL, and active trades.
  - `▶ RESUME`: Seamlessly continues execution from the exact stopped tick.
  - `🔄 RESET`: Complete reset flushes all open orders, charts, and neural weights back to baseline.
  - `Close`: Instant manual market-order liquidation of active positions.
  - Biological Speed pills: `1x`, `5x`, `10x`, `20x`.

### 5. Multi-Market Slicing
Pre-packaged with realistic geometric Brownian motion and regime-switching market datasets:
- **Commodities**: MCX Gold (`GOLD/INR`)
- **Forex**: US Dollar to Indian Rupee (`USD/INR`)
- **Indian Equities & Indices**: `NIFTY50`, `BANKNIFTY`, `RELIANCE`
- **Crypto Perpetuals**: `BTC/USDT`, `ETH/USDT`, `SOL/USDT`

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python**: 3.10, 3.11, or 3.12
- **Node.js**: 18.x or 20.x+
- **Git**

---

### Step 1: Clone Repository
```bash
git clone https://github.com/Zacker/Fruit-fly-trader.git
cd Fruit-fly-trader
```

---

### Step 2: Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI Server
python -m uvicorn api.server:app --port 8000 --host 127.0.0.1
```
*The backend API will start on `http://127.0.0.1:8000`.*

---

### Step 3: Frontend Setup
Open a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite Development Server
npm run dev
```
*The web interface will launch at `http://localhost:5173`.*

---

## 🕹️ Using the Interface

1. **Launch**: Open `http://localhost:5173` in your browser. The dashboard starts in **`STANDBY`** mode.
2. **Select Asset**: Use the asset dropdown in the top-left to select your target market (e.g. `GOLD/INR`, `USD/INR`, `NIFTY 50`, `BTC/USDT`).
3. **Start Simulation**: Click **`▶ START`** in the top navigation bar.
4. **Adjust Speed**: Switch between `1x` (1 second per tick/candle), `5x`, `10x`, or `20x`.
5. **Adjust Multiplier**: Open the **`💼 WALLET`** drawer to tune leverage (e.g., 5x, 10x, 25x).
6. **Inspect Decisions**: Observe how the fruit fly's dopamine surges on profitable runs, and cortisol induces hesitation during choppy periods.
7. **Stop and Resume**: Click **`⏹ STOP`** to halt ticks in place without wiping the chart or metrics, and **`▶ RESUME`** to seamlessly continue. Use **`🔄 RESET`** whenever you want a completely fresh run.

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/datasets/info` | List all available market datasets with volatility, tick size, and asset metadata. |
| `GET` | `/api/simulation/status` | Current status (`idle`, `running`, `paused`), active speed, and multiplier. |
| `POST`| `/api/simulation/start` | Start simulation with dataset, speed, multiplier, exit mode, and biological seed. |
| `POST`| `/api/simulation/pause` | Toggle simulation pause / resume. |
| `POST`| `/api/simulation/stop` | Stop simulation runner in place preserving chart and trade state. |
| `POST`| `/api/simulation/resume` | Resume simulation runner from stopped state. |
| `POST`| `/api/simulation/reset` | Terminate runner, flush buffers, and reset state. |
| `POST`| `/api/simulation/settings` | Dynamically update exit mode (Auto vs. Manual TP/SL), risk rules, and multiplier. |
| `POST`| `/api/simulation/speed` | Dynamically update simulation speed multiplier (`1` to `100`). |
| `POST`| `/api/simulation/multiplier` | Dynamically update trading leverage multiplier (`1` to `50`). |
| `POST`| `/api/simulation/manual_close`| Manually liquidate all open trades at current mark price. |
| `GET` | `/api/events` | High-frequency Server-Sent Events (SSE) streaming live candles, trades, wallet, and neural telemetry. |

---

## 🧪 Running Tests

A comprehensive unit test suite covering connectome dynamics, micro-trading calculations, security constraints (path traversal prevention, CORS compliance, input bounds), and market feature extraction is included.

Run backend tests:
```bash
cd backend
pytest
```
*Expect all 31 tests to pass in < 1 second.*

---

## 📁 Repository Structure

```text
Fruit-fly-trader/
├── backend/
│   ├── api/
│   │   └── server.py              # FastAPI server, lifespan handler, SSE event broadcaster
│   ├── engine/
│   │   ├── activity.py            # LIF Brain propagation, biological compartments & neuromodulators
│   │   ├── connectome.py          # Drosophila subgraph sampling & topology processor
│   │   ├── connectome_download.py # Downloader & scaffold fallback generator
│   │   ├── neuron.py              # Leaky integrate-and-fire model with stochastic noise
│   │   ├── plasticity.py          # Three-factor Hebbian learning engine
│   │   ├── pruning.py             # Structural synaptic pruning engine
│   │   └── synapse.py             # Synapse connection representations
│   ├── experiments/
│   │   └── runner.py              # Asynchronous simulation loop and biological pacing
│   ├── market/
│   │   ├── data_loader.py         # CSV Candle parser and validation
│   │   ├── dataset_manager.py     # Synthetic data generator & secure dataset loader
│   │   └── features.py            # Technical indicator & feature transduction engine
│   ├── tests/
│   │   ├── test_engine.py         # Connectome graph & neuron tests
│   │   ├── test_market.py         # Data loading & feature calculation tests
│   │   ├── test_micro_trading.py  # Margin, leverage, and PnL accounting tests
│   │   └── test_security.py       # Path traversal, CORS, and parameter bound tests
│   ├── trading/
│   │   └── micro_trading.py       # High-frequency trading engine with INR wallet
│   └── requirements.txt           # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/            # UI components (Trading Desk, 3D Brain, Order Book, Ledger, etc.)
│   │   ├── App.jsx                # Main Workbench layout and state management
│   │   ├── styles.css             # High-contrast cyber-tech styling
│   │   └── useEventStream.js      # Robust SSE stream listener and local buffer manager
│   ├── package.json               # Node frontend dependencies
│   └── vite.config.js             # Vite configuration with API proxy
├── data/
│   ├── raw/                       # Drop custom OHLCV CSVs here
│   └── connectome/                # Local connectome edge lists cache
├── .gitignore                     # Production Git ignore rules
└── README.md                      # Comprehensive project documentation
```

---

## 🔒 Security & Data Integrity

- **Path Traversal Protection**: All dataset endpoints strictly resolve paths using `os.path.realpath`, validating that requested files are strictly contained within `data/raw` and rejecting any path separators or `..` attempts.
- **Strict Input Validation**: Pydantic models enforce hard mathematical and bounds constraints on initial capital, multipliers, speeds, hold ticks, and threshold parameters.
- **Thread-Safe Architecture**: The simulation runner uses cooperative async execution (`asyncio.sleep`) directly within the ASGI event loop, guaranteeing zero queue race conditions or event loop lockups.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

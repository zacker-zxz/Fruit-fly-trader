"""FastAPI server with SSE event streaming, interactive simulation controls, and INR wallet API."""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sse_starlette.sse import EventSourceResponse

from experiments.runner import SimulationRunner
from market.dataset_manager import get_available_datasets_info, ensure_datasets_exist, validate_dataset_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_datasets_exist()
    yield


# Configure secure server logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fruit_fly_trader")

app = FastAPI(title="Fruit-Fly Trader Connectome API", version="2.0.0", lifespan=lifespan)

# Security Fix: Explicit CORS configuration preventing credential leakage
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
if allowed_origins_env.strip():
    allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

# If wildcard is specified, credentials MUST be False per CORS spec
allow_creds = False if "*" in allowed_origins else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_creds,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

subscribers: set[asyncio.Queue] = set()
active_runner: Optional[SimulationRunner] = None
runner_task: Optional[asyncio.Task] = None


# Strict Pydantic Models for Input Validation & DoS Prevention
class SimulationStartRequest(BaseModel):
    dataset: str = Field(..., min_length=1, max_length=150)
    start_time: Optional[float] = Field(default=None, ge=0.0)
    seed: Optional[int] = Field(default=None, ge=0, le=2147483647)
    max_neurons: int = Field(default=750, ge=50, le=5000)
    action_threshold: float = Field(default=0.04, ge=0.001, le=0.5)
    multiplier: int = Field(default=10, ge=1, le=50)
    speed: int = Field(default=1, ge=1, le=100)
    take_profit_pct: float = Field(default=0.015, ge=0.001, le=0.5)
    stop_loss_pct: float = Field(default=0.010, ge=0.001, le=0.5)
    max_hold_ticks: int = Field(default=8, ge=1, le=200)
    initial_capital_inr: float = Field(default=500000.0, ge=1000.0, le=100000000.0)
    currency: str = Field(default="INR", max_length=10)
    stake_pct: float = Field(default=0.05, ge=0.001, le=0.5)
    brain_threshold: float = Field(default=0.8, ge=0.1, le=5.0)
    learning_rate: float = Field(default=0.01, ge=0.0001, le=1.0)
    usd_inr_rate: float = Field(default=83.75, ge=1.0, le=500.0)

    @field_validator("dataset")
    @classmethod
    def validate_dataset_name(cls, v: str) -> str:
        v = v.strip()
        if ".." in v or "/" in v or "\\" in v or ":" in v:
            raise ValueError("Path traversal attempt detected in dataset parameter.")
        if not v.lower().endswith(".csv"):
            raise ValueError("Dataset file must end with .csv")
        return v


class SpeedUpdateRequest(BaseModel):
    speed: int = Field(default=5, ge=1, le=100)


class MultiplierUpdateRequest(BaseModel):
    multiplier: int = Field(default=10, ge=1, le=50)


class PauseRequest(BaseModel):
    paused: Optional[bool] = None


def _on_event(e: dict) -> None:
    dead = []
    for q in list(subscribers):
        try:
            q.put_nowait(e)
        except asyncio.QueueFull:
            pass
        except Exception:
            dead.append(q)
    for q in dead:
        subscribers.discard(q)



@app.get("/api/datasets")
def datasets() -> dict:
    ensure_datasets_exist()
    raw = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
    files = [
        f for f in sorted(os.listdir(raw))
        if f.lower().endswith(".csv") and not any(sep in f for sep in ("/", "\\", ".."))
    ] if os.path.isdir(raw) else []
    return {"datasets": files}


@app.get("/api/datasets/info")
def datasets_info() -> dict:
    return {"markets": get_available_datasets_info()}


@app.get("/api/simulation/status")
def simulation_status() -> dict:
    global active_runner
    if active_runner is None:
        return {"status": "idle", "speed": 5, "multiplier": 10}
    return {
        "status": "paused" if active_runner.is_paused else ("running" if active_runner.is_running else "idle"),
        "speed": active_runner.speed_multiplier,
        "multiplier": active_runner.multiplier,
        "dataset": active_runner.dataset_name,
    }


@app.post("/api/simulation/start")
async def start_simulation(payload: SimulationStartRequest) -> dict:
    global active_runner, runner_task

    # Validate dataset path against traversal
    try:
        validate_dataset_path(payload.dataset)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))

    # Stop any currently active runner
    if active_runner:
        active_runner.stop()
    if runner_task and not runner_task.done():
        runner_task.cancel()

    # Build validated config
    cfg = {
        "seed": payload.seed,
        "max_neurons": payload.max_neurons,
        "action_threshold": payload.action_threshold,
        "multiplier": payload.multiplier,
        "speed_multiplier": payload.speed,
        "take_profit_pct": payload.take_profit_pct,
        "stop_loss_pct": payload.stop_loss_pct,
        "max_hold_ticks": payload.max_hold_ticks,
        "usd_inr_rate": payload.usd_inr_rate,
        "wallet": {
            "initial_capital_inr": payload.initial_capital_inr,
            "currency": payload.currency,
            "stake_pct": payload.stake_pct,
            "usd_inr_rate": payload.usd_inr_rate,
        },
        "brain": {"threshold": payload.brain_threshold},
        "plasticity": {
            "learning_rate": payload.learning_rate,
            "trace_decay": 0.9,
            "hebbian_rate": 0.002,
        },
        "pruning": {
            "enabled": True,
            "min_activity": 0.01,
            "min_strength": 0.02,
            "patience": 150,
        },
    }

    runner = SimulationRunner(
        config=cfg,
        dataset_name=payload.dataset,
        start_time=payload.start_time,
        on_event=_on_event,
    )
    active_runner = runner

    async def _async_run():
        try:
            manifest = await runner.run_async()
            _on_event({"type": "done", "manifest": manifest})
        except asyncio.CancelledError:
            logger.info("Simulation runner cancelled.")
            _on_event({"type": "cancelled"})
        except ValueError as exc:
            # Client input validation error (safe to emit without file paths)
            logger.warning("Simulation validation error: %s", exc)
            _on_event({"type": "error", "message": str(exc)})
        except Exception as exc:
            # Internal error: log full stack trace server-side, send generic message to client
            logger.exception("Internal error in simulation runner: %s", exc)
            _on_event({"type": "error", "message": "Simulation encountered an internal error. Please check server logs."})

    runner_task = asyncio.create_task(_async_run())
    return {"status": "started", "dataset": payload.dataset, "speed": runner.speed_multiplier, "multiplier": runner.multiplier}


@app.post("/api/simulation/speed")
def update_speed(payload: SpeedUpdateRequest) -> dict:
    global active_runner
    speed = payload.speed
    if active_runner:
        active_runner.set_speed(speed)
        _on_event({"type": "speed_changed", "speed": active_runner.speed_multiplier})
        return {"status": "ok", "speed": active_runner.speed_multiplier}
    return {"status": "no_active_runner", "speed": speed}


@app.post("/api/simulation/multiplier")
def update_multiplier(payload: MultiplierUpdateRequest) -> dict:
    global active_runner
    mult = payload.multiplier
    if active_runner:
        active_runner.set_multiplier(mult)
        _on_event({"type": "multiplier_changed", "multiplier": active_runner.multiplier})
        return {"status": "ok", "multiplier": active_runner.multiplier}
    return {"status": "no_active_runner", "multiplier": mult}


@app.post("/api/simulation/pause")
def toggle_pause(payload: PauseRequest = Body(default=PauseRequest())) -> dict:
    global active_runner
    if active_runner:
        desired = payload.paused
        if desired is not None:
            active_runner.is_paused = bool(desired)
        else:
            active_runner.pause()
        is_paused = active_runner.is_paused
        _on_event({"type": "pause_toggled", "paused": is_paused})
        return {"status": "ok", "paused": is_paused}
    return {"status": "no_active_runner"}


@app.post("/api/simulation/reset")
def reset_simulation() -> dict:
    """Instantly and cleanly terminates simulation, flushes event buffers, and resets state."""
    global active_runner, runner_task
    if active_runner:
        active_runner.stop()
    if runner_task and not runner_task.done():
        runner_task.cancel()
    
    active_runner = None
    runner_task = None

    _on_event({"type": "reset", "message": "Simulation cleanly reset."})
    return {"status": "reset_complete"}


@app.post("/api/simulation/stop")
def stop_simulation() -> dict:
    """Stops/pauses the active simulation runner without resetting chart or trade data."""
    global active_runner
    if active_runner:
        active_runner.is_paused = True
        _on_event({"type": "pause_toggled", "paused": True})
        return {"status": "stopped", "paused": True}
    return {"status": "no_active_runner"}


@app.post("/api/simulation/resume")
def resume_simulation() -> dict:
    """Resumes the active simulation runner from the stopped point."""
    global active_runner
    if active_runner:
        active_runner.is_paused = False
        _on_event({"type": "pause_toggled", "paused": False})
        return {"status": "resumed", "paused": False}
    return {"status": "no_active_runner"}


@app.post("/api/simulation/manual_close")
def manual_close() -> dict:
    """Manually book all open positions at market price."""
    global active_runner
    if active_runner:
        active_runner.request_manual_close()
        return {"status": "close_requested"}
    return {"status": "no_active_runner"}


# Legacy compatibility endpoint
@app.post("/api/start/{dataset}")
async def start_legacy(dataset: str) -> dict:
    try:
        req = SimulationStartRequest(dataset=dataset, speed=5, multiplier=10)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return await start_simulation(req)


@app.get("/api/events")
async def events():
    q: asyncio.Queue = asyncio.Queue(maxsize=1000)
    subscribers.add(q)

    # Immediately seed new subscriber if a simulation is currently active
    if active_runner and active_runner.is_running and hasattr(active_runner, "recent_candles") and active_runner.recent_candles:
        try:
            # 1. Send recent candles history
            q.put_nowait({
                "type": "init_history",
                "dataset": active_runner.dataset_name,
                "candles": list(active_runner.recent_candles),
            })
            # 2. Send current wallet summary & latest tick
            if hasattr(active_runner, "trade_engine"):
                latest_px = active_runner.recent_candles[-1]["close"] if active_runner.recent_candles else 0.0
                wallet_summary = active_runner.trade_engine.get_wallet_summary(latest_px)
                q.put_nowait({
                    "type": "tick",
                    "tick": getattr(active_runner, "current_tick", 0),
                    "ts": active_runner.recent_candles[-1]["ts"],
                    "candle": active_runner.recent_candles[-1],
                    "decision": getattr(active_runner, "latest_decision", "HOLD"),
                    "confidence": getattr(active_runner, "latest_confidence", {"BUY": 0.33, "HOLD": 0.34, "SELL": 0.33}),
                    "active_neurons": getattr(active_runner, "latest_active_count", 150),
                    "fired_ids": getattr(active_runner, "latest_fired_ids", []),
                    "total_spikes": getattr(active_runner, "total_spikes", 0),
                    "total_neurons": 750,
                    "clusters": getattr(active_runner, "latest_clusters", {}),
                    "neurotransmitters": getattr(active_runner, "latest_neurotransmitters", {}),
                    "bio_latency_ms": getattr(active_runner, "latest_bio_latency", 25.0),
                    "inference_ms": getattr(active_runner, "latest_inference_ms", 1.0),
                    "firing_rate_hz": getattr(active_runner, "latest_firing_hz", 120.0),
                    "mushroom_body_active": getattr(active_runner, "latest_mb_active", 0),
                    "memory_strength": getattr(active_runner, "latest_memory_strength", 0.0),
                    "speed": active_runner.speed_multiplier,
                    "wallet": wallet_summary,
                    "market_features": getattr(active_runner, "latest_market_features", {}),
                })
                # 3. Send any currently open positions
                for ot in active_runner.trade_engine.open_trades:
                    q.put_nowait({
                        "type": "trade_opened",
                        "trade": {
                            "id": ot.trade_id,
                            "side": ot.side,
                            "multiplier": ot.multiplier,
                            "entry_price": ot.entry_price,
                            "stake_inr": ot.stake_inr,
                            "entry_ts": ot.entry_ts,
                            "entry_tick": ot.entry_tick,
                            "max_hold_ticks": ot.max_hold_ticks,
                        },
                        "wallet": wallet_summary,
                    })
        except Exception as seed_err:
            logger.warning("Could not seed subscriber: %s", seed_err)

    async def gen():
        try:
            while True:
                try:
                    e = await asyncio.wait_for(q.get(), timeout=12)
                    yield {"event": e.get("type", "tick"), "data": json.dumps(e)}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        except asyncio.CancelledError:
            pass
        finally:
            subscribers.discard(q)

    return EventSourceResponse(gen())


# Mount frontend dist static files if built
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.isdir(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

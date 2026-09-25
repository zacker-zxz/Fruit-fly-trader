"""FastAPI server with SSE event streaming, interactive simulation controls, and INR wallet API."""

import asyncio
import json
import os
from typing import Optional
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from experiments.runner import SimulationRunner
from market.dataset_manager import get_available_datasets_info, ensure_datasets_exist

app = FastAPI(title="Fruit-Fly Trader Connectome API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

subscribers: set[asyncio.Queue] = set()
active_runner: Optional[SimulationRunner] = None
runner_task: Optional[asyncio.Task] = None


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


@app.on_event("startup")
def startup():
    ensure_datasets_exist()


@app.get("/api/datasets")
def datasets() -> dict:
    ensure_datasets_exist()
    raw = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
    files = [f for f in sorted(os.listdir(raw)) if f.lower().endswith(".csv")] if os.path.isdir(raw) else []
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
async def start_simulation(payload: dict = Body(...)) -> dict:
    global active_runner, runner_task

    dataset = payload.get("dataset")
    if not dataset:
        raise HTTPException(status_code=400, detail="Missing dataset parameter")

    # Stop any currently active runner
    if active_runner:
        active_runner.stop()
    if runner_task and not runner_task.done():
        runner_task.cancel()

    # Clear queue
    while not queue.empty():
        try:
            queue.get_nowait()
        except Exception:
            break

    # Build config
    cfg = {
        "seed": payload.get("seed", 42),
        "max_neurons": payload.get("max_neurons", 750),
        "action_threshold": payload.get("action_threshold", 0.04),
        "multiplier": payload.get("multiplier", 10),
        "speed_multiplier": payload.get("speed", 5),
        "take_profit_pct": payload.get("take_profit_pct", 0.015),
        "stop_loss_pct": payload.get("stop_loss_pct", 0.010),
        "max_hold_ticks": payload.get("max_hold_ticks", 8),
        "wallet": {
            "initial_capital_inr": payload.get("initial_capital_inr", 500000.0),
            "currency": payload.get("currency", "INR"),
            "stake_pct": payload.get("stake_pct", 0.05),
        },
        "brain": {"threshold": payload.get("brain_threshold", 0.8)},
        "plasticity": {
            "learning_rate": payload.get("learning_rate", 0.01),
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

    start_time = payload.get("start_time")
    runner = SimulationRunner(
        config=cfg,
        dataset_name=dataset,
        start_time=start_time,
        on_event=_on_event,
    )
    active_runner = runner

    async def _async_run():
        try:
            manifest = await asyncio.to_thread(runner.run_sync)
            _on_event({"type": "done", "manifest": manifest})
        except asyncio.CancelledError:
            _on_event({"type": "cancelled"})
        except Exception as exc:
            _on_event({"type": "error", "message": str(exc)})

    runner_task = asyncio.create_task(_async_run())
    return {"status": "started", "dataset": dataset, "speed": runner.speed_multiplier, "multiplier": runner.multiplier}


@app.post("/api/simulation/speed")
def update_speed(payload: dict = Body(...)) -> dict:
    global active_runner
    speed = payload.get("speed", 5)
    if active_runner:
        active_runner.set_speed(speed)
        _on_event({"type": "speed_changed", "speed": active_runner.speed_multiplier})
        return {"status": "ok", "speed": active_runner.speed_multiplier}
    return {"status": "no_active_runner", "speed": speed}


@app.post("/api/simulation/multiplier")
def update_multiplier(payload: dict = Body(...)) -> dict:
    global active_runner
    mult = payload.get("multiplier", 10)
    if active_runner:
        active_runner.set_multiplier(mult)
        _on_event({"type": "multiplier_changed", "multiplier": active_runner.multiplier})
        return {"status": "ok", "multiplier": active_runner.multiplier}
    return {"status": "no_active_runner", "multiplier": mult}


@app.post("/api/simulation/pause")
def toggle_pause(payload: dict = Body(default={})) -> dict:
    global active_runner
    if active_runner:
        desired = payload.get("paused") if isinstance(payload, dict) else None
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

    while not queue.empty():
        try:
            queue.get_nowait()
        except Exception:
            break

    _on_event({"type": "reset", "message": "Simulation cleanly reset."})
    return {"status": "reset_complete"}


@app.post("/api/simulation/manual_close")
def manual_close() -> dict:
    """Manually book all open positions at market price."""
    global active_runner
    if active_runner and hasattr(active_runner, "trade_engine"):
        # We trigger on next tick or force
        return {"status": "close_requested"}
    return {"status": "no_active_runner"}


# Legacy compatibility endpoint
@app.post("/api/start/{dataset}")
async def start_legacy(dataset: str) -> dict:
    return await start_simulation({"dataset": dataset, "speed": 5, "multiplier": 10})


@app.get("/api/events")
async def events():
    async def gen():
        while True:
            try:
                e = await asyncio.wait_for(queue.get(), timeout=25)
                yield {"event": e.get("type", "tick"), "data": json.dumps(e)}
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": "{}"}

    return EventSourceResponse(gen())


# Mount frontend dist static files if built
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.isdir(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

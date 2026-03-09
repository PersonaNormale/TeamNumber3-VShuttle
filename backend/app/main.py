import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    DatasetLoadRequest,
    DatasetLoadResponse,
    DecisionOutput,
    HumanDecisionRequest,
    HumanDecisionResponse,
    ScenarioInput,
    SimulationStartRequest,
    SimulationStartResponse,
    SimulationState,
    CurrentScenario,
)
from app.pipeline import evaluate_scenario

app = FastAPI(title="V-Shuttle Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # intentional for hackathon demo — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

# datasets[datasetId] = list[ScenarioInput]
datasets: dict[str, list[ScenarioInput]] = {}
_dataset_counter = 0

# simulations[simulationId] = {
#   "items": list[tuple[int, DecisionOutput]],   # (id_scenario, result)
#   "current_index": int,
#   "status": str,
#   "last_advance_time": float,
#   "waiting_human_since": float | None,
# }
simulations: dict[str, dict] = {}
_simulation_counter = 0

AUTO_ADVANCE_MS = 4000
HUMAN_TIMEOUT_MS = 2000

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _confidence_level(confidence: float) -> str:
    if confidence >= 0.80:
        return "high"
    if confidence >= 0.50:
        return "medium"
    return "low"


def _action_color(action: str) -> str:
    if action == "GO":
        return "green"
    if action == "STOP":
        return "red"
    return "yellow"


def _set_status_for_current(sim: dict, now: float) -> None:
    """Update sim status based on the action of the current scenario."""
    items = sim["items"]
    idx = sim["current_index"]
    if idx >= len(items):
        sim["status"] = "COMPLETED"
        sim["waiting_human_since"] = None
        return
    _, dec = items[idx]
    if dec.action == "HUMAN_REVIEW":
        sim["status"] = "WAITING_HUMAN"
        sim["waiting_human_since"] = now
    else:
        sim["status"] = "RUNNING"
        sim["waiting_human_since"] = None


def _try_advance(sim: dict, now: float) -> None:
    """Advance current_index by one and update status accordingly."""
    sim["current_index"] += 1
    sim["last_advance_time"] = now
    _set_status_for_current(sim, now)


def _build_state(sim_id: str, sim: dict) -> SimulationState:
    items = sim["items"]
    total = len(items)
    idx = sim["current_index"]
    status = sim["status"]

    current_scenario: CurrentScenario | None = None
    if idx < total:
        scenario_id, dec = items[idx]
        countdown: int | None = None
        if status == "WAITING_HUMAN" and sim["waiting_human_since"] is not None:
            elapsed_ms = (time.time() - sim["waiting_human_since"]) * 1000
            countdown = max(0, int(HUMAN_TIMEOUT_MS - elapsed_ms))

        current_scenario = CurrentScenario(
            scenarioId=scenario_id,
            fusedText=dec.fused_text,
            action=dec.action,
            reason=dec.reason,
            confidence=dec.confidence,
            confidenceLevel=_confidence_level(dec.confidence),
            requiresHumanReview=dec.action == "HUMAN_REVIEW",
            countdownMsRemaining=countdown,
            color=_action_color(dec.action),
        )

    allowed_actions = ["CONFIRM", "OVERRIDE"] if status == "WAITING_HUMAN" else []

    return SimulationState(
        simulationId=sim_id,
        status=status,
        currentIndex=idx,
        totalScenarios=total,
        autoAdvanceMs=AUTO_ADVANCE_MS,
        humanTimeoutMs=HUMAN_TIMEOUT_MS,
        currentScenario=current_scenario,
        allowedActions=allowed_actions,
    )


# ---------------------------------------------------------------------------
# Existing endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/decision/evaluate", response_model=DecisionOutput)
def decision_evaluate(payload: ScenarioInput) -> DecisionOutput:
    return evaluate_scenario(payload)


# ---------------------------------------------------------------------------
# New simulation endpoints
# ---------------------------------------------------------------------------


@app.post("/api/datasets/load", response_model=DatasetLoadResponse)
def datasets_load(body: DatasetLoadRequest) -> DatasetLoadResponse:
    global _dataset_counter
    _dataset_counter += 1
    dataset_id = f"ds_{_dataset_counter:03d}"
    datasets[dataset_id] = body.scenarios
    return DatasetLoadResponse(
        datasetId=dataset_id,
        scenarioCount=len(body.scenarios),
    )


@app.post("/api/simulations/start", response_model=SimulationStartResponse)
def simulations_start(body: SimulationStartRequest) -> SimulationStartResponse:
    global _simulation_counter
    if body.datasetId not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    scenarios = datasets[body.datasetId]
    items = [(sc.id_scenario, evaluate_scenario(sc)) for sc in scenarios]

    _simulation_counter += 1
    sim_id = f"sim_{_simulation_counter:03d}"
    now = time.time()
    sim: dict = {
        "items": items,
        "current_index": 0,
        "status": "RUNNING",
        "last_advance_time": now,
        "waiting_human_since": None,
    }
    _set_status_for_current(sim, now)
    simulations[sim_id] = sim

    return SimulationStartResponse(
        simulationId=sim_id,
        state=_build_state(sim_id, sim),
    )


@app.get("/api/simulations/{simulation_id}/state", response_model=SimulationState)
def simulations_state(simulation_id: str) -> SimulationState:
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim = simulations[simulation_id]
    now = time.time()

    if sim["status"] == "RUNNING":
        elapsed = now - sim["last_advance_time"]
        if elapsed >= AUTO_ADVANCE_MS / 1000:
            _try_advance(sim, now)

    elif sim["status"] == "WAITING_HUMAN":
        elapsed = now - sim["waiting_human_since"]
        if elapsed >= HUMAN_TIMEOUT_MS / 1000:
            # Timeout: apply automatic STOP and advance
            _try_advance(sim, now)

    return _build_state(simulation_id, sim)


@app.post(
    "/api/simulations/{simulation_id}/human-decision",
    response_model=HumanDecisionResponse,
)
def simulations_human_decision(
    simulation_id: str, body: HumanDecisionRequest
) -> HumanDecisionResponse:
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim = simulations[simulation_id]
    if sim["status"] != "WAITING_HUMAN":
        raise HTTPException(
            status_code=409, detail="Simulation is not waiting for human input"
        )

    now = time.time()
    _try_advance(sim, now)

    return HumanDecisionResponse(
        accepted=True,
        state=_build_state(simulation_id, sim),
    )

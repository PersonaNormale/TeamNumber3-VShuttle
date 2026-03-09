from typing import Literal

from pydantic import BaseModel


class SensorReading(BaseModel):
    testo: str | None = None
    confidenza: float | None = None


class Sensors(BaseModel):
    camera_frontale: SensorReading
    camera_laterale: SensorReading
    V2I_receiver: SensorReading


class ScenarioInput(BaseModel):
    id_scenario: int
    sensori: Sensors
    orario_rilevamento: str
    giorno_settimana: str


class DecisionOutput(BaseModel):
    action: Literal["STOP", "GO", "HUMAN_REVIEW"]
    reason: str
    confidence: float
    fused_text: str | None = None


# ---------------------------------------------------------------------------
# Dataset / Simulation request and response models
# ---------------------------------------------------------------------------


class DatasetLoadRequest(BaseModel):
    scenarios: list[ScenarioInput]


class DatasetLoadResponse(BaseModel):
    datasetId: str
    scenarioCount: int


class SimulationStartRequest(BaseModel):
    datasetId: str


class CurrentScenario(BaseModel):
    scenarioId: int
    fusedText: str | None
    action: Literal["GO", "STOP", "HUMAN_REVIEW"]
    reason: str
    confidence: float
    confidenceLevel: Literal["low", "medium", "high"]
    requiresHumanReview: bool
    countdownMsRemaining: int | None
    color: Literal["green", "yellow", "red"]


class SimulationState(BaseModel):
    simulationId: str
    status: Literal["IDLE", "RUNNING", "WAITING_HUMAN", "COMPLETED"]
    currentIndex: int
    totalScenarios: int
    autoAdvanceMs: int
    humanTimeoutMs: int
    currentScenario: CurrentScenario | None
    allowedActions: list[Literal["CONFIRM", "OVERRIDE"]]


class SimulationStartResponse(BaseModel):
    simulationId: str
    state: SimulationState


class HumanDecisionRequest(BaseModel):
    decision: Literal["CONFIRM", "OVERRIDE"]


class HumanDecisionResponse(BaseModel):
    accepted: bool
    state: SimulationState

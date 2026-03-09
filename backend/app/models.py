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

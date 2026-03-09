from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class SensorReading:
    source: str
    testo: str | None
    confidenza: float | None


@dataclass
class Scenario:
    id_scenario: int
    sensori: list[SensorReading]
    orario_rilevamento: str
    giorno_settimana: str


@dataclass
class SignInfo:
    sign_type: str
    raw_text: str
    exceptions: list[str] = field(default_factory=list)
    time_range: tuple | None = None
    days: list[str] = field(default_factory=list)
    varco_attivo: bool | None = None
    is_fine_zona: bool = False
    sub_type: str = ""


@dataclass
class Decision:
    scenario_id: int
    action: str
    confidence: float
    fused_text: str
    sign_type: str
    exceptions: list[str]
    reason: str
    orario_rilevamento: str
    giorno_settimana: str
    sensori_raw: dict

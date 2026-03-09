"""V-Shuttle decision pipeline — public API."""
from __future__ import annotations

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from engine.fusion import fuse_sensors
from engine.sign_parser import parse_sign
from engine.decision import decide, to_legacy_json
from models import Decision


def process_scenario(scenario: dict) -> Decision:
    """Run the full pipeline on a single scenario dict."""
    try:
        sid = scenario["id_scenario"]
        sensori = scenario["sensori"]
        orario = scenario.get("orario_rilevamento", "12:00")
        giorno = scenario.get("giorno_settimana", "Lunedì")

        fused_text, confidence, raw_dict = fuse_sensors(sensori)
        sign_info = parse_sign(fused_text)
        return decide(sign_info, confidence, orario, giorno, sid,
                       fused_text, raw_dict)
    except Exception as exc:
        return Decision(
            scenario_id=scenario.get("id_scenario", -1),
            action="ASK_HUMAN",
            confidence=0.0,
            fused_text=f"ERRORE: {exc}",
            sign_type="ERRORE",
            exceptions=[],
            reason="Errore nel processamento — frenata di sicurezza",
            orario_rilevamento=scenario.get("orario_rilevamento", ""),
            giorno_settimana=scenario.get("giorno_settimana", ""),
            sensori_raw={},
        )


def process_all(scenarios: list[dict]) -> list[dict]:
    """Process every scenario and return a list of Legacy JSON dicts."""
    return [to_legacy_json(process_scenario(sc)) for sc in scenarios]

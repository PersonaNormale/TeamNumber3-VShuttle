import pathlib
import sys

# Ensure the project root is in sys.path so that engine/ and models.py are importable
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engine.decision import decide  # noqa: E402
from engine.fusion import fuse_sensors  # noqa: E402
from engine.sign_parser import parse_sign  # noqa: E402

from app.models import DecisionOutput, ScenarioInput


def evaluate_scenario(scenario: ScenarioInput) -> DecisionOutput:
    """Run the full OCR pipeline for a single scenario.

    Steps:
    1. Convert Pydantic Sensors model to dict for fuse_sensors
    2. Weighted sensor fusion (fuse_sensors)
    3. Sign parsing (parse_sign)
    4. Decision logic (decide)
    5. Map engine action ASK_HUMAN → HUMAN_REVIEW for the frontend contract
    """
    sensori_dict = scenario.sensori.model_dump()

    fused_text, confidence, raw_dict = fuse_sensors(sensori_dict)
    sign_info = parse_sign(fused_text)
    decision = decide(
        sign_info,
        confidence,
        scenario.orario_rilevamento,
        scenario.giorno_settimana,
        scenario.id_scenario,
        fused_text,
        raw_dict,
    )

    action = decision.action
    if action == "ASK_HUMAN":
        action = "HUMAN_REVIEW"

    return DecisionOutput(
        action=action,
        reason=decision.reason,
        confidence=decision.confidence,
        fused_text=decision.fused_text,
    )

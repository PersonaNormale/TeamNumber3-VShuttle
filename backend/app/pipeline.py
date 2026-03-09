from app.models import DecisionOutput, ScenarioInput


def evaluate_scenario(scenario: ScenarioInput) -> DecisionOutput:
    """Stub iniziale della pipeline semantica.

    Step previsti:
    1. normalizzazione OCR
    2. fusione pesata dei sensori
    3. parsing della regola
    4. decisione finale
    """
    return DecisionOutput(
        action="HUMAN_REVIEW",
        reason="pipeline_not_implemented",
        confidence=0.0,
        fused_text=None,
    )

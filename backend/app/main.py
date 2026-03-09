from fastapi import FastAPI

from app.models import DecisionOutput, ScenarioInput
from app.pipeline import evaluate_scenario

app = FastAPI(title="V-Shuttle Backend", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/decision/evaluate", response_model=DecisionOutput)
def decision_evaluate(payload: ScenarioInput) -> DecisionOutput:
    return evaluate_scenario(payload)

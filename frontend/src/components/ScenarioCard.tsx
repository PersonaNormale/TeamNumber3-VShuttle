import type { SimulationState } from "../types";
import { StatusBadge } from "./StatusBadge";

type ScenarioCardProps = {
  state: SimulationState | null;
};

export function ScenarioCard({ state }: ScenarioCardProps) {
  if (!state?.currentScenario) {
    return (
      <section className="panel">
        <h2>Scenario corrente</h2>
        <p>Nessuna simulazione attiva. Carica un dataset e avvia la demo.</p>
      </section>
    );
  }

  const { currentScenario, currentIndex, totalScenarios } = state;
  const confidencePercentage = Math.round(currentScenario.confidence * 100);

  return (
    <section className="panel scenario-card">
      <div className="scenario-header">
        <h2>Scenario #{currentScenario.scenarioId}</h2>
        <StatusBadge action={currentScenario.action} />
      </div>

      <p className="fused-text">{currentScenario.fusedText ?? "N/A"}</p>

      <div className="scenario-grid">
        <div>
          <span className="label">Decisione</span>
          <p className="action-text">{currentScenario.action}</p>
        </div>
        <div>
          <span className="label">Confidenza</span>
          <p>{confidencePercentage}% ({currentScenario.confidenceLevel})</p>
        </div>
      </div>

      <div>
        <span className="label">Motivazione</span>
        <p>{currentScenario.reason}</p>
      </div>

      <p className="progress-text">
        Progresso scenario: {Math.min(currentIndex + 1, totalScenarios)} / {totalScenarios}
      </p>
    </section>
  );
}

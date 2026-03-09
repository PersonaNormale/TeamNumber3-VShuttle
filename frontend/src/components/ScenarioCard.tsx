import type { SimulationState } from "../types";
import { ConfidenceBar } from "./ConfidenceBar";
import { StatusBadge } from "./StatusBadge";

type ScenarioCardProps = {
  state: SimulationState | null;
};

const actionLabel: Record<string, string> = {
  GO: "PROCEDI",
  STOP: "FERMATI",
  HUMAN_REVIEW: "ATTENDI CONFERMA"
};

export function ScenarioCard({ state }: ScenarioCardProps) {
  if (!state?.currentScenario) {
    return (
      <section className="panel scenario-card">
        <h2>Situazione attuale</h2>
        <p>Nessuna simulazione attiva. Carica un dataset e premi START SIMULATION.</p>
      </section>
    );
  }

  const { currentScenario, currentIndex, totalScenarios } = state;

  return (
    <section className={`panel scenario-card tone-${currentScenario.color}`}>
      <div className="scenario-header">
        <h2>Scenario #{currentScenario.scenarioId}</h2>
        <StatusBadge action={currentScenario.action} />
      </div>

      <p className="fused-title">Testo compreso dal sistema</p>
      <p className="fused-text">{currentScenario.fusedText ?? "Segnale non leggibile"}</p>

      <div className="scenario-grid">
        <div>
          <span className="label">Azione</span>
          <p className="action-text">{actionLabel[currentScenario.action]}</p>
        </div>
        <div>
          <span className="label">Affidabilità lettura</span>
          <ConfidenceBar value={currentScenario.confidence} />
        </div>
      </div>

      <div>
        <span className="label">Perché</span>
        <p>{currentScenario.reason}</p>
      </div>

      <p className="progress-text">
        Scenario {Math.min(currentIndex + 1, totalScenarios)} di {totalScenarios}
      </p>
    </section>
  );
}

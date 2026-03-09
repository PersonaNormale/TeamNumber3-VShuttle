import type { HumanDecision, SimulationState } from "../types";

type HumanDecisionPanelProps = {
  state: SimulationState;
  onDecision: (decision: HumanDecision) => Promise<void>;
  loading: boolean;
};

export function HumanDecisionPanel({ state, onDecision, loading }: HumanDecisionPanelProps) {
  if (state.status !== "WAITING_HUMAN" || !state.currentScenario?.requiresHumanReview) {
    return null;
  }

  const countdownMs = state.currentScenario.countdownMsRemaining;

  return (
    <section className="panel human-panel">
      <h2>Intervento umano richiesto</h2>
      <p>
        Countdown backend: <strong>{countdownMs !== null ? `${countdownMs} ms` : "N/A"}</strong>
      </p>
      <div className="human-actions">
        <button
          className="button decision confirm"
          disabled={loading || !state.allowedActions.includes("CONFIRM")}
          onClick={() => {
            void onDecision("CONFIRM");
          }}
        >
          CONFIRM
        </button>
        <button
          className="button decision override"
          disabled={loading || !state.allowedActions.includes("OVERRIDE")}
          onClick={() => {
            void onDecision("OVERRIDE");
          }}
        >
          OVERRIDE
        </button>
      </div>
    </section>
  );
}

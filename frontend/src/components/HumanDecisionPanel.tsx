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
  const secondsLeft = countdownMs !== null ? Math.max(0, countdownMs / 1000).toFixed(1) : "2.0";

  return (
    <section className="panel human-panel">
      <h2>Conferma operatore richiesta</h2>
      <p className="timer-text">
        Tempo rimasto: <strong>{secondsLeft}s</strong>
      </p>
      <div className="human-actions">
        <button
          className="button decision override"
          disabled={loading || !state.allowedActions.includes("OVERRIDE")}
          onClick={() => {
            void onDecision("OVERRIDE");
          }}
        >
          OVERRIDE
        </button>
        <button
          className="button decision confirm"
          disabled={loading || !state.allowedActions.includes("CONFIRM")}
          onClick={() => {
            void onDecision("CONFIRM");
          }}
        >
          CONFERMA
        </button>
      </div>
    </section>
  );
}

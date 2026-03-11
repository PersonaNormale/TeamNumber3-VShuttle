import { useCallback, useMemo, useState } from "react";
import { apiClient, ApiError } from "./api/client";
import { DatasetUploader } from "./components/DatasetUploader";
import { useSimulationPolling } from "./hooks/useSimulationPolling";
import type {
  DatasetLoadRequest,
  HumanDecision,
  SimulationState,
  SimulationStatus
} from "./types";

type DashboardTone = "go" | "stop" | "review" | "safe-stop";

const TONE_META: Record<DashboardTone, { label: string; action: string }> = {
  go: { label: "VIA LIBERA", action: "VAI" },
  stop: { label: "STOP", action: "STOP" },
  review: { label: "CONFERMA RICHIESTA", action: "DECIDI" },
  "safe-stop": { label: "STOP DI SICUREZZA", action: "STOP" }
};

function getTone(state: SimulationState | null): DashboardTone {
  if (!state?.currentScenario) return "safe-stop";
  if (state.status === "WAITING_HUMAN" && state.currentScenario.countdownMsRemaining === 0) {
    return "safe-stop";
  }

  switch (state.currentScenario.action) {
    case "GO":
      return "go";
    case "STOP":
      return "stop";
    case "HUMAN_REVIEW":
      return state.status === "WAITING_HUMAN" ? "review" : "safe-stop";
    default:
      return "safe-stop";
  }
}

function confidenceLabel(value: number): string {
  if (value >= 85) return "Alta";
  if (value >= 65) return "Media";
  if (value > 0) return "Bassa";
  return "Assente";
}

function App() {
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [scenarioCount, setScenarioCount] = useState<number>(0);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const simulationStatus: SimulationStatus | null = simulationState?.status ?? null;
  const tone = useMemo(() => getTone(simulationState), [simulationState]);
  const isWaitingHuman = simulationState?.status === "WAITING_HUMAN";
  const rawConfidence = simulationState?.currentScenario?.confidence ?? 0;
  const progressValue = Math.round(Math.max(0, Math.min(1, rawConfidence)) * 100);

  const parseError = (err: unknown): string => {
    if (err instanceof ApiError) {
      if (err.status === 404) return "Risorsa non trovata. Ricarica il dataset e riprova.";
      if (err.status === 409) return "Azione non disponibile in questo momento.";
      return "Operazione non riuscita. Riprova.";
    }
    return "Qualcosa non ha funzionato. Riprova.";
  };

  const handleDatasetParsed = async (dataset: DatasetLoadRequest) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.loadDataset(dataset);
      setDatasetId(response.datasetId);
      setScenarioCount(response.scenarioCount);
      setSimulationId(null);
      setSimulationState(null);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleStartSimulation = async () => {
    if (!datasetId) {
      setError("Carica prima un dataset valido.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.startSimulation(datasetId);
      setSimulationId(response.simulationId);
      setSimulationState(response.state);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const refreshState = useCallback(async () => {
    if (!simulationId) return;
    try {
      const state = await apiClient.getSimulationState(simulationId);
      setSimulationState(state);
    } catch (err) {
      setError(parseError(err));
    }
  }, [simulationId]);

  const handleHumanDecision = async (decision: HumanDecision) => {
    if (!simulationId) return;

    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.sendHumanDecision(simulationId, decision);
      setSimulationState(response.state);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };


  const handleStopSimulation = async () => {
    if (!simulationId) return;

    setLoading(true);
    setError(null);
    try {
      const state = await apiClient.stopSimulation(simulationId);
      setSimulationState(state);
    } catch (err) {
      setError(parseError(err));
    } finally {
      setLoading(false);
    }
  };

  const pollingEnabled = useMemo(() => {
    return simulationState?.status === "RUNNING" || simulationState?.status === "WAITING_HUMAN";
  }, [simulationState?.status]);

  useSimulationPolling({
    simulationId,
    enabled: pollingEnabled,
    onTick: refreshState,
    state: simulationState
  });

  const timerSeconds = ((simulationState?.currentScenario?.countdownMsRemaining ?? 0) / 1000).toFixed(1);
  const displayedScenarioIndex = simulationState
    ? Math.min(simulationState.currentIndex + 1, simulationState.totalScenarios)
    : "-";

  return (
    <div className={`app-shell tone-${tone}`}>
      <div className="topbar">
        <div>
          <p className="eyebrow">V-Shuttle</p>
          <h1>Decision Dashboard</h1>
        </div>
        <div className="status-wrap">
          <span className="pill">{TONE_META[tone].label}</span>
          <p>
            Scenario {displayedScenarioIndex}/
            {(simulationState?.totalScenarios ?? scenarioCount) || "-"}
          </p>
        </div>
      </div>

      <main className="dashboard-grid">
        <section className="hero-card">
          <div>
            <p className="eyebrow">Azione immediata</p>
            <h2>{TONE_META[tone].action}</h2>
            <p className="message">
              {simulationState?.currentScenario?.reason ?? "Carica un file JSON e avvia la simulazione."}
            </p>
          </div>

          <div className="stats-grid">
            <article>
              <span>Cartello compreso</span>
              <strong>{simulationState?.currentScenario?.fusedText ?? "Nessun dato disponibile"}</strong>
            </article>
            <article>
              <span>Affidabilità</span>
              <strong>{confidenceLabel(progressValue)} ({progressValue}%)</strong>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${progressValue}%` }} />
              </div>
            </article>
            <article>
              <span>Stato simulazione</span>
              <strong>{simulationStatus ?? "IDLE"}</strong>
              <p>Auto-advance backend: {simulationState?.autoAdvanceMs ?? 4000} ms</p>
            </article>
          </div>
        </section>

        <aside className="control-panel">
          <DatasetUploader onDatasetParsed={handleDatasetParsed} loading={loading} />

          <button
            className="cta primary"
            onClick={() => void handleStartSimulation()}
            disabled={loading || !datasetId}
          >
            Start simulation
          </button>
          <button className="cta secondary" onClick={() => void refreshState()} disabled={loading || !simulationId}>
            Aggiorna stato
          </button>
          <button className="cta danger" onClick={() => void handleStopSimulation()} disabled={loading || !simulationId}>
            Stop simulazione
          </button>

          <div className="panel-note">
            <p>Dataset pronto: <strong>{datasetId ? "Sì" : "No"}</strong></p>
            <p>Scenari caricati: <strong>{scenarioCount || "-"}</strong></p>
          </div>

          {error && <p className="error-banner">{error}</p>}
        </aside>
      </main>

      {isWaitingHuman && simulationState?.currentScenario && (
        <div className="review-overlay">
          <div className="review-card">
            <p className="eyebrow">Serve una decisione</p>
            <h3>Decidi adesso</h3>
            <p className="message">{simulationState.currentScenario.reason}</p>
            <div className="timer">Tempo residuo: {timerSeconds}s</div>
            <div className="human-actions">
              <button
                className="cta confirm"
                disabled={loading}
                onClick={() => {
                  void handleHumanDecision("CONFIRM");
                }}
              >
                Procedi
              </button>
              <button
                className="cta override"
                disabled={loading}
                onClick={() => {
                  void handleHumanDecision("OVERRIDE");
                }}
              >
                Fermati
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

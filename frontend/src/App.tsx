import { useCallback, useMemo, useState } from "react";
import { apiClient, ApiError } from "./api/client";
import { DatasetUploader } from "./components/DatasetUploader";
import { Header } from "./components/Header";
import { HumanDecisionPanel } from "./components/HumanDecisionPanel";
import { ScenarioCard } from "./components/ScenarioCard";
import { useSimulationPolling } from "./hooks/useSimulationPolling";
import type {
  DatasetLoadRequest,
  HumanDecision,
  SimulationState,
  SimulationStatus
} from "./types";

function App() {
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [scenarioCount, setScenarioCount] = useState<number>(0);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const simulationStatus: SimulationStatus | null = simulationState?.status ?? null;

  const parseError = (err: unknown): string => {
    if (err instanceof ApiError) {
      if (err.status === 404) {
        return "Risorsa non trovata. Ricarica il dataset e riprova.";
      }
      if (err.status === 409) {
        return "Azione non disponibile in questo momento.";
      }
      return "Operazione non riuscita. Riprova.";
    }
    if (err instanceof Error) {
      return "Qualcosa non ha funzionato. Riprova.";
    }
    return "Operazione non disponibile. Riprova.";
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
    if (!simulationId) {
      return;
    }

    try {
      const state = await apiClient.getSimulationState(simulationId);
      setSimulationState(state);
    } catch (err) {
      setError(parseError(err));
    }
  }, [simulationId]);

  const handleHumanDecision = async (decision: HumanDecision) => {
    if (!simulationId) {
      return;
    }

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

  const pollingEnabled = useMemo(() => {
    return simulationState?.status === "RUNNING" || simulationState?.status === "WAITING_HUMAN";
  }, [simulationState?.status]);

  useSimulationPolling({
    simulationId,
    enabled: pollingEnabled,
    onTick: refreshState,
    state: simulationState
  });

  return (
    <div className="app">
      <Header status={simulationStatus} />

      <main>
        <DatasetUploader onDatasetParsed={handleDatasetParsed} loading={loading} />

        <section className="panel controls">
          <h2>Simulazione live</h2>
          <p>Dataset pronto: <strong>{datasetId ? "Sì" : "No"}</strong></p>
          <p>Scenari caricati: <strong>{scenarioCount || "-"}</strong></p>
          <button className="button start-button" onClick={() => void handleStartSimulation()} disabled={loading || !datasetId}>
            START SIMULATION
          </button>
          <p className="hint">Avanzamento automatico ogni 4 secondi.</p>
        </section>

        {error && <p className="error-banner">{error}</p>}

        <ScenarioCard state={simulationState} />

        {simulationState && (
          <HumanDecisionPanel
            state={simulationState}
            onDecision={handleHumanDecision}
            loading={loading}
          />
        )}
      </main>
    </div>
  );
}

export default App;

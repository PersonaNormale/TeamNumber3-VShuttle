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
      return `Errore API (${err.status ?? "unknown"}): ${err.message}`;
    }
    if (err instanceof Error) {
      return err.message;
    }
    return "Errore non previsto";
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
          <h2>Controlli simulazione</h2>
          <p>Dataset ID: <strong>{datasetId ?? "non caricato"}</strong></p>
          <p>Scenari totali: <strong>{scenarioCount || "-"}</strong></p>
          <button className="button" onClick={() => void handleStartSimulation()} disabled={loading || !datasetId}>
            START SIMULATION
          </button>
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

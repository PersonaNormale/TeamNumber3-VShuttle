import type {
  DatasetLoadRequest,
  DatasetLoadResponse,
  HumanDecision,
  HumanDecisionResponse,
  SimulationState,
  StartSimulationResponse
} from "../types";

const BASE_URL = "/api";

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new ApiError(detail || "Errore nella chiamata API", response.status);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  loadDataset(payload: DatasetLoadRequest): Promise<DatasetLoadResponse> {
    return request<DatasetLoadResponse>("/datasets/load", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },

  startSimulation(datasetId: string): Promise<StartSimulationResponse> {
    return request<StartSimulationResponse>("/simulations/start", {
      method: "POST",
      body: JSON.stringify({ datasetId })
    });
  },

  getSimulationState(simulationId: string): Promise<SimulationState> {
    return request<SimulationState>(`/simulations/${simulationId}/state`);
  },

  stopSimulation(simulationId: string): Promise<SimulationState> {
    return request<SimulationState>(`/simulations/${simulationId}/stop`, {
      method: "POST"
    });
  },

  sendHumanDecision(
    simulationId: string,
    decision: HumanDecision
  ): Promise<HumanDecisionResponse> {
    return request<HumanDecisionResponse>(`/simulations/${simulationId}/human-decision`, {
      method: "POST",
      body: JSON.stringify({ decision })
    });
  }
};

export { ApiError };

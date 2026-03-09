export type SimulationStatus =
  | "IDLE"
  | "RUNNING"
  | "WAITING_HUMAN"
  | "COMPLETED";

export type ScenarioAction =
  | "GO"
  | "STOP"
  | "HUMAN_REVIEW";

export type HumanDecision =
  | "CONFIRM"
  | "OVERRIDE";

export type ConfidenceLevel =
  | "low"
  | "medium"
  | "high";

export type ScenarioColor =
  | "green"
  | "yellow"
  | "red";

export type SimulationState = {
  simulationId: string;
  status: SimulationStatus;
  currentIndex: number;
  totalScenarios: number;
  autoAdvanceMs: number;
  humanTimeoutMs: number;
  currentScenario: {
    scenarioId: number;
    fusedText: string | null;
    action: ScenarioAction;
    reason: string;
    confidence: number;
    confidenceLevel: ConfidenceLevel;
    requiresHumanReview: boolean;
    countdownMsRemaining: number | null;
    color: ScenarioColor;
  } | null;
  allowedActions: HumanDecision[];
};

export type DatasetScenario = {
  id_scenario: number;
  sensori: Record<string, { testo: string; confidenza: number }>;
  orario_rilevamento: string;
  giorno_settimana: string;
};

export type DatasetLoadRequest = {
  scenarios: DatasetScenario[];
};

export type DatasetLoadResponse = {
  datasetId: string;
  scenarioCount: number;
};

export type StartSimulationResponse = {
  simulationId: string;
  state: SimulationState;
};

export type HumanDecisionResponse = {
  accepted: boolean;
  state: SimulationState;
};

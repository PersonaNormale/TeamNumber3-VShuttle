import { useEffect } from "react";
import type { SimulationState } from "../types";

type UseSimulationPollingParams = {
  simulationId: string | null;
  enabled: boolean;
  onTick: () => Promise<void>;
  state: SimulationState | null;
};

export function useSimulationPolling({
  simulationId,
  enabled,
  onTick,
  state
}: UseSimulationPollingParams) {
  useEffect(() => {
    if (!simulationId || !enabled) {
      return;
    }

    if (state?.status === "COMPLETED") {
      return;
    }

    const intervalId = window.setInterval(() => {
      void onTick();
    }, 500);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [simulationId, enabled, onTick, state?.status]);
}

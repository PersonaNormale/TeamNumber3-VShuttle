import type { ScenarioAction } from "../types";

type StatusBadgeProps = {
  action: ScenarioAction;
};

const actionClassMap: Record<ScenarioAction, string> = {
  GO: "badge badge-go",
  STOP: "badge badge-stop",
  HUMAN_REVIEW: "badge badge-human"
};

export function StatusBadge({ action }: StatusBadgeProps) {
  return <span className={actionClassMap[action]}>{action}</span>;
}

import type { ScenarioAction } from "../types";

type StatusBadgeProps = {
  action: ScenarioAction;
};

const actionClassMap: Record<ScenarioAction, string> = {
  GO: "badge badge-go",
  STOP: "badge badge-stop",
  HUMAN_REVIEW: "badge badge-human"
};

const actionLabelMap: Record<ScenarioAction, string> = {
  GO: "PROCEDI",
  STOP: "FERMATI",
  HUMAN_REVIEW: "ATTENZIONE"
};

export function StatusBadge({ action }: StatusBadgeProps) {
  return <span className={actionClassMap[action]}>{actionLabelMap[action]}</span>;
}

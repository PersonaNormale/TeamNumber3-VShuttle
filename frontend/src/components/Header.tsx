import type { SimulationStatus } from "../types";

type HeaderProps = {
  status: SimulationStatus | null;
};

const statusLabel: Record<string, string> = {
  IDLE: "IN ATTESA",
  RUNNING: "IN CORSO",
  WAITING_HUMAN: "RICHIEDE CONFERMA",
  COMPLETED: "COMPLETATA"
};

export function Header({ status }: HeaderProps) {
  const label = status ? statusLabel[status] : statusLabel.IDLE;

  return (
    <header className="header">
      <div>
        <h1>V-Shuttle Dashboard</h1>
        <p>Vista rapida per decisioni immediate a bordo</p>
      </div>
      <div className="header-status">
        <span>Stato</span>
        <strong>{label}</strong>
      </div>
    </header>
  );
}

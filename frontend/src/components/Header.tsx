import type { SimulationStatus } from "../types";

type HeaderProps = {
  status: SimulationStatus | null;
};

export function Header({ status }: HeaderProps) {
  return (
    <header className="header">
      <div>
        <h1>V-Shuttle Dashboard</h1>
        <p>Demo hackathon per simulazione navetta autonoma</p>
      </div>
      <div className="header-status">
        <span>Stato simulazione</span>
        <strong>{status ?? "IDLE"}</strong>
      </div>
    </header>
  );
}

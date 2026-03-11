# V-Shuttle Frontend

Dashboard single-page per la demo hackathon della navetta autonoma **V-Shuttle**.

## Obiettivo

Visualizzare in tempo reale lo stato della simulazione calcolato dal backend:
- scenario corrente,
- cartello fuso,
- decisione (`GO`, `STOP`, `HUMAN_REVIEW`),
- motivazione e confidenza,
- richiesta intervento umano (`WAITING_HUMAN`) con countdown.

## Stack tecnico

- React 18
- TypeScript
- Vite
- Polling HTTP ogni 500ms (no websocket)

## Principi

- Backend come unica source of truth.
- Nessuna logica semantica nel frontend.
- Nessun global state complesso.
- Interfaccia ottimizzata per lettura rapida su tablet.

## Struttura

```text
frontend/
├── index.html
├── package.json
├── vite.config.ts
└── src/
    ├── App.tsx
    ├── styles.css
    ├── types.ts
    ├── api/client.ts
    ├── hooks/useSimulationPolling.ts
    └── components/
        ├── DatasetUploader.tsx
        ├── Header.tsx
        ├── ScenarioCard.tsx
        ├── HumanDecisionPanel.tsx
        ├── ConfidenceBar.tsx
        └── StatusBadge.tsx
```

## Flusso UI

1. Upload dataset JSON (`POST /api/datasets/load`).
2. Start simulazione (`POST /api/simulations/start`).
3. Polling stato (`GET /api/simulations/{id}/state`) ogni 500ms.
4. Se `WAITING_HUMAN`, mostra azioni `CONFIRM` / `OVERRIDE`.
5. Invio decisione operatore (`POST /api/simulations/{id}/human-decision`).
6. Possibilità di terminare la simulazione (`POST /api/simulations/{id}/stop`).
7. Stop polling quando stato `COMPLETED`.

## API usate

Base URL: `/api`

- `POST /datasets/load`
- `POST /simulations/start`
- `GET /simulations/{simulationId}/state`
- `POST /simulations/{simulationId}/human-decision`
- `POST /simulations/{simulationId}/stop`

## Avvio locale

```bash
cd frontend
npm install
npm run dev
```

Default: `http://localhost:5173`

## Build

```bash
npm run build
npm run preview
```

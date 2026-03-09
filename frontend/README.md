# V-Shuttle Frontend (Demo Hackathon)

Dashboard single-page per demo hackathon della navetta autonoma **V-Shuttle**.
Il frontend è volutamente semplice: mostra lo stato che arriva dal backend senza implementare logica decisionale locale.

## Obiettivo della demo

Mostrare in tempo reale:
- scenario corrente della simulazione
- testo fuso ricevuto dal backend
- decisione (`GO`, `STOP`, `HUMAN_REVIEW`)
- motivazione, confidenza e avanzamento
- gestione intervento umano quando lo stato è `WAITING_HUMAN`

## Stack tecnico

- **React 18**
- **TypeScript**
- **Vite**
- **HTTP polling** ogni 500ms (no websocket)

## Principi implementativi

- Backend come **unica source of truth**.
- Nessuna logica di decisione semantica nel frontend.
- Nessun Redux / stato globale complesso.
- Nessuna autenticazione.
- Componenti piccoli e facilmente modificabili.

## Struttura progetto

```text
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── styles.css
    ├── types.ts
    ├── api/
    │   └── client.ts
    ├── hooks/
    │   └── useSimulationPolling.ts
    └── components/
        ├── Header.tsx
        ├── DatasetUploader.tsx
        ├── ScenarioCard.tsx
        ├── HumanDecisionPanel.tsx
        └── StatusBadge.tsx
```

## Flusso funzionale

1. Upload di un file JSON dataset dal client.
2. `POST /api/datasets/load`.
3. Click su **START SIMULATION**.
4. `POST /api/simulations/start`.
5. Polling `GET /api/simulations/{id}/state` ogni 500ms.
6. Rendering stato, scenario, decisione e progresso.
7. Se `WAITING_HUMAN`, mostra countdown backend + bottoni `CONFIRM` / `OVERRIDE`.
8. `POST /api/simulations/{id}/human-decision` e update immediato dello stato UI con la response.
9. Stop polling a stato `COMPLETED`.

## Mappa API usata dal frontend

Base URL: `/api`

- `POST /datasets/load`
- `POST /simulations/start`
- `GET /simulations/{simulationId}/state`
- `POST /simulations/{simulationId}/human-decision`

Le chiamate sono centralizzate in `src/api/client.ts`.

## Tipi principali

Definiti in `src/types.ts`:
- `SimulationStatus`
- `ScenarioAction`
- `HumanDecision`
- `ConfidenceLevel`
- `ScenarioColor`
- `SimulationState`

## Requisiti UI coperti

- Header con titolo progetto e stato simulazione.
- Sezione upload dataset.
- Pulsante **START SIMULATION**.
- Card scenario con:
  - `scenarioId`
  - `fusedText`
  - `action` ben visibile
  - `reason`
  - `confidence` in percentuale
  - badge decisionale
- Progresso scenario (`currentIndex` / `totalScenarios`).
- Pannello `WAITING_HUMAN` con countdown backend e due pulsanti grandi.
- Gestione semplice di loading, errore rete, stato iniziale senza dati.

## Colori decisione

- `GO` → verde
- `STOP` → rosso
- `HUMAN_REVIEW` → giallo

## Avvio locale

```bash
cd frontend
npm install
npm run dev
```

App disponibile di default su: `http://localhost:5173`

## Build produzione

```bash
npm run build
npm run preview
```

## Dataset di esempio

Puoi usare un file JSON con shape:

```json
{
  "scenarios": [
    {
      "id_scenario": 3,
      "sensori": {
        "camera_frontale": { "testo": "ZTL ATTIVA 08:00 - 20:00", "confidenza": 0.95 },
        "camera_laterale": { "testo": "ZTL ATTIVA 8:00 20:00", "confidenza": 0.81 },
        "V2I_receiver": { "testo": "ZTL 08-20", "confidenza": 0.91 }
      },
      "orario_rilevamento": "10:00",
      "giorno_settimana": "Mercoledì"
    }
  ]
}
```

## Limiti noti (hackathon scope)

- Nessun sistema di autenticazione/autorizzazione.
- Nessuna persistenza locale avanzata.
- Nessuna riconnessione sofisticata oltre alla gestione errori base.

## Estensioni future (TODO)

- Sostituire il polling con websocket mantenendo invariata la UI.
- Aggiungere test unitari per componenti e client API.
- Migliorare visualizzazione timeline simulazione.

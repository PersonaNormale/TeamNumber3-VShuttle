# backend integration

## Scopo

Contratto minimo tra backend e frontend per la demo V-Shuttle.
Il frontend non implementa logica decisionale: legge lo stato simulazione e mostra feedback operatore.

## Base URL

`/api`

Esempi:

* `/api/datasets/load`
* `/api/simulations/start`
* `/api/simulations/{simulationId}/state`
* `/api/simulations/{simulationId}/human-decision`
* `/api/simulations/{simulationId}/stop`

## Flusso integrazione

1. Upload dataset.
2. Backend restituisce `datasetId`.
3. Avvio simulazione con `datasetId`.
4. Backend restituisce `simulationId` + stato iniziale.
5. Frontend fa polling periodico dello stato.
6. Se `WAITING_HUMAN`, frontend abilita azioni operatore.
7. Se timeout 2s senza input, backend forza `STOP` e passa allo scenario successivo.

## Endpoint

### `POST /api/datasets/load`
Carica il dataset e restituisce:

```json
{ "datasetId": "ds_001", "scenarioCount": 75 }
```

### `POST /api/simulations/start`
Avvia una simulazione su dataset esistente.

Request:

```json
{ "datasetId": "ds_001" }
```

Response:

```json
{ "simulationId": "sim_001", "state": { "status": "RUNNING" } }
```

### `GET /api/simulations/{simulationId}/state`
Restituisce lo stato corrente completo (`SimulationState`).

### `POST /api/simulations/{simulationId}/human-decision`
Accetta body:

```json
{ "decision": "CONFIRM" }
```

oppure

```json
{ "decision": "OVERRIDE" }
```

> Nota: nella versione attuale backend entrambe le decisioni fanno avanzare la simulazione allo scenario successivo.

### `POST /api/simulations/{simulationId}/stop`
Termina manualmente la simulazione impostando stato `COMPLETED`.

## Enum condivise

```ts
export type SimulationStatus = "IDLE" | "RUNNING" | "WAITING_HUMAN" | "COMPLETED";
export type ScenarioAction = "GO" | "STOP" | "HUMAN_REVIEW";
export type HumanDecision = "CONFIRM" | "OVERRIDE";
export type ConfidenceLevel = "low" | "medium" | "high";
export type ScenarioColor = "green" | "yellow" | "red";
```

## Regole di integrazione

### Frontend

- Non ricalcola fusione, decisione o countdown.
- Mostra esclusivamente i campi ricevuti da `SimulationState`.
- Invia `human-decision` solo in `WAITING_HUMAN`.

### Backend

- Mantiene stato simulazione coerente.
- Espone `allowedActions` solo in `WAITING_HUMAN`.
- Gestisce avanzamento automatico (4s) e timeout umano (2s).

## Polling consigliato

- Intervallo: `500ms`.
- Arresto polling quando `status === "COMPLETED"`.

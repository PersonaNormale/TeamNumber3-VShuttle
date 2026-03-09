# backend integration

## Scopo

Questo documento definisce il contratto minimo tra backend e frontend per la demo V-Shuttle.
Il frontend non implementa logica decisionale. Il frontend legge lo stato della simulazione, mostra il cartello fuso, la decisione corrente e invia eventuale conferma umana.

## Base URL

Assumere come base:

`/api`

Esempi:

* `/api/datasets/load`
* `/api/simulations/start`
* `/api/simulations/{simulationId}/state`
* `/api/simulations/{simulationId}/human-decision`

## Flusso di integrazione

Sequenza prevista:

1. il frontend carica il dataset
2. il backend restituisce `datasetId`
3. il frontend avvia la simulazione usando `datasetId`
4. il backend restituisce `simulationId` e stato iniziale
5. il frontend legge periodicamente lo stato corrente
6. se lo stato è `WAITING_HUMAN`, il frontend mostra i pulsanti operatore
7. se l’operatore sceglie un’azione, il frontend invia la decisione
8. se l’operatore non risponde entro 2 secondi, il backend applica `STOP` automaticamente

## Endpoint minimi

## 1. Caricamento dataset

### `POST /api/datasets/load`

Carica il dataset JSON e restituisce un identificativo riusabile per la simulazione.

### Request

```json
{
  "scenarios": [
    {
      "id_scenario": 3,
      "sensori": {
        "camera_frontale": {
          "testo": "ZTL ATTIVA 08:00 - 20:00",
          "confidenza": 0.95
        },
        "camera_laterale": {
          "testo": "ZTL ATTIVA 8:00 20:00",
          "confidenza": 0.81
        },
        "V2I_receiver": {
          "testo": "ZTL 08-20",
          "confidenza": 0.91
        }
      },
      "orario_rilevamento": "10:00",
      "giorno_settimana": "Mercoledì"
    }
  ]
}
```

### Response

```json
{
  "datasetId": "ds_001",
  "scenarioCount": 75
}
```

### Uso frontend

* chiamata una sola volta all’avvio oppure dopo upload manuale del file
* salvare `datasetId` nello stato applicativo

## 2. Avvio simulazione

### `POST /api/simulations/start`

Avvia la simulazione sul dataset scelto.

### Request

```json
{
  "datasetId": "ds_001"
}
```

### Response

```json
{
  "simulationId": "sim_001",
  "state": {
    "simulationId": "sim_001",
    "status": "RUNNING",
    "currentIndex": 0,
    "totalScenarios": 75,
    "autoAdvanceMs": 4000,
    "humanTimeoutMs": 2000,
    "currentScenario": {
      "scenarioId": 3,
      "fusedText": "ZTL ATTIVA 08:00-20:00",
      "action": "STOP",
      "reason": "ztl attiva nella fascia oraria corrente",
      "confidence": 0.91,
      "confidenceLevel": "high",
      "requiresHumanReview": false,
      "countdownMsRemaining": null,
      "color": "red"
    },
    "allowedActions": []
  }
}
```

### Uso frontend

* chiamata sul click del pulsante `START SIMULATION`
* salvare `simulationId`
* inizializzare la UI con `state`

## 3. Stato simulazione

### `GET /api/simulations/{simulationId}/state`

Restituisce lo stato corrente della simulazione. È l’endpoint principale usato dal frontend.

### Response

```json
{
  "simulationId": "sim_001",
  "status": "WAITING_HUMAN",
  "currentIndex": 12,
  "totalScenarios": 75,
  "autoAdvanceMs": 4000,
  "humanTimeoutMs": 2000,
  "currentScenario": {
    "scenarioId": 99,
    "fusedText": "DIVIETO DI ACCESSO",
    "action": "HUMAN_REVIEW",
    "reason": "lettura incerta tra divieto e possibile eccezione bus",
    "confidence": 0.67,
    "confidenceLevel": "medium",
    "requiresHumanReview": true,
    "countdownMsRemaining": 1340,
    "color": "yellow"
  },
  "allowedActions": ["CONFIRM", "OVERRIDE"]
}
```

### Uso frontend

Campi da visualizzare direttamente:

* `status`
* `currentScenario.fusedText`
* `currentScenario.action`
* `currentScenario.reason`
* `currentScenario.confidence`
* `currentScenario.confidenceLevel`
* `currentScenario.countdownMsRemaining`
* `currentScenario.color`
* `allowedActions`

### Polling consigliato

Polling HTTP ogni `250` o `500 ms`.

Il frontend non deve calcolare localmente il timeout. Deve mostrare il countdown ricevuto dal backend.

## 4. Decisione operatore

### `POST /api/simulations/{simulationId}/human-decision`

Invia la scelta umana quando la simulazione è in stato `WAITING_HUMAN`.

### Request

```json
{
  "decision": "CONFIRM"
}
```

oppure

```json
{
  "decision": "OVERRIDE"
}
```

### Response

```json
{
  "accepted": true,
  "state": {
    "simulationId": "sim_001",
    "status": "RUNNING",
    "currentIndex": 13,
    "totalScenarios": 75,
    "autoAdvanceMs": 4000,
    "humanTimeoutMs": 2000,
    "currentScenario": {
      "scenarioId": 100,
      "fusedText": "LAVORI",
      "action": "GO",
      "reason": "segnale informativo",
      "confidence": 0.96,
      "confidenceLevel": "high",
      "requiresHumanReview": false,
      "countdownMsRemaining": null,
      "color": "green"
    },
    "allowedActions": []
  }
}
```

### Uso frontend

* mostrare i pulsanti solo se `status = WAITING_HUMAN`
* disabilitare i pulsanti dopo il click finché non arriva la response
* aggiornare lo stato locale con `state`

## Contratti dati

## Enum `status`

```ts
export type SimulationStatus =
  | "IDLE"
  | "RUNNING"
  | "WAITING_HUMAN"
  | "COMPLETED";
```

## Enum `action`

```ts
export type ScenarioAction =
  | "GO"
  | "STOP"
  | "HUMAN_REVIEW";
```

## Enum `decision`

```ts
export type HumanDecision =
  | "CONFIRM"
  | "OVERRIDE";
```

## Enum `confidenceLevel`

```ts
export type ConfidenceLevel =
  | "low"
  | "medium"
  | "high";
```

## Enum `color`

```ts
export type ScenarioColor =
  | "green"
  | "yellow"
  | "red";
```

## Tipo principale condiviso

```ts
export type SimulationState = {
  simulationId: string;
  status: "IDLE" | "RUNNING" | "WAITING_HUMAN" | "COMPLETED";
  currentIndex: number;
  totalScenarios: number;
  autoAdvanceMs: number;
  humanTimeoutMs: number;
  currentScenario: {
    scenarioId: number;
    fusedText: string | null;
    action: "GO" | "STOP" | "HUMAN_REVIEW";
    reason: string;
    confidence: number;
    confidenceLevel: "low" | "medium" | "high";
    requiresHumanReview: boolean;
    countdownMsRemaining: number | null;
    color: "green" | "yellow" | "red";
  } | null;
  allowedActions: ("CONFIRM" | "OVERRIDE")[];
};
```

## Regole di integrazione

## Regole lato frontend

Il frontend deve:

* trattare il backend come unica fonte di verità
* non ricostruire il testo fuso
* non ricalcolare decisione, colore o countdown
* limitarsi a leggere `state` e mostrarlo
* inviare `human-decision` solo in stato `WAITING_HUMAN`

## Regole lato backend

Il backend deve:

* restituire sempre uno stato consistente
* valorizzare `allowedActions` in base allo stato
* restituire `countdownMsRemaining` solo in `WAITING_HUMAN`
* applicare `STOP` automatico allo scadere dei 2 secondi
* avanzare automaticamente ogni 4 secondi negli stati automatici

## Mappatura minima UI

## Header simulazione

Usa:

* `currentIndex`
* `totalScenarios`
* `status`

## Card scenario

Usa:

* `fusedText`
* `reason`
* `confidence`
* `color`

## Pannello decisione

Usa:

* `action`
* `requiresHumanReview`
* `countdownMsRemaining`
* `allowedActions`

## Comportamenti da evitare

Non introdurre ora:

* websocket dedicati
* storico eventi complesso
* tick manuale dal frontend
* log tecnici in UI
* mapping colore deciso dal frontend

## Note implementative

Per la demo hackathon la soluzione consigliata è:

* backend con stato simulazione in memoria
* frontend con polling su `/state`
* un solo dataset attivo per sessione demo

Questa soluzione minimizza il codice e riduce il rischio di desincronizzazione tra frontend e backend.

## Checklist integrazione

Il frontend è integrato correttamente se:

* riesce a caricare il dataset
* riesce ad avviare la simulazione
* aggiorna la dashboard leggendo `/state`
* mostra `GO`, `STOP` e `HUMAN_REVIEW`
* mostra il countdown solo quando richiesto
* invia `CONFIRM` e `OVERRIDE`
* non contiene logica decisionale duplicata

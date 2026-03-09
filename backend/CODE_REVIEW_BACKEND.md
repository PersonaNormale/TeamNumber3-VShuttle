# Code Review Backend (FastAPI)

## Ambito
Revisione del backend in `backend/app` con focus su API di simulazione e robustezza runtime.

## Findings

### 1) `human-decision` ignora il payload `decision` (CONFIRM/OVERRIDE)
**Severità:** Alta

L'endpoint `/api/simulations/{simulation_id}/human-decision` accetta `HumanDecisionRequest` con `decision` (`CONFIRM` o `OVERRIDE`), ma il valore non viene mai usato: la funzione avanza sempre alla scena successiva con `_try_advance(sim, now)` senza alcuna differenza di comportamento o tracciamento dell'override.

- Impatto: l'API promette due azioni distinte, ma il backend implementa una sola semantica.
- Rischio: disallineamento contratto FE/BE, impossibilità di audit, override non applicabili.

Riferimenti:
- `HumanDecisionRequest` definisce `decision`.  
- Endpoint usa `_try_advance` senza leggere `body.decision`.

### 2) Commento di timeout incoerente con l'implementazione
**Severità:** Media

Nel branch `WAITING_HUMAN`, il commento dice: `Timeout: apply automatic STOP and advance`, ma la logica reale fa solo `_try_advance(sim, now)` e non modifica la decisione corrente né registra uno `STOP` automatico.

- Impatto: comportamento ambiguo, bug di prodotto/documentazione.
- Rischio: aspettative errate lato client e stakeholder.

Riferimento:
- `simulations_state` ramo timeout umano.

### 3) Stato globale in memoria non protetto (race condition / multi-worker)
**Severità:** Media

`datasets`, `simulations`, `_dataset_counter` e `_simulation_counter` sono globali mutabili in memoria di processo. In esecuzione concorrente (più richieste, più worker Uvicorn/Gunicorn) si possono avere inconsistenze tra processi/thread e perdita dati al riavvio.

- Impatto: ID duplicati o non condivisi tra worker, stato simulazioni non affidabile in produzione.
- Rischio: errori intermittenti difficili da riprodurre.

Riferimenti:
- Store e counter globali in `main.py`.

## Raccomandazioni

1. Rendere `decision` effettiva nel backend:
   - `CONFIRM`: conferma decisione del modello e avanza.
   - `OVERRIDE`: sostituisce action corrente (es. `STOP`/`GO`) con tracciamento.
   - Salvare audit trail (`actor`, `timestamp`, `from_action`, `to_action`, `note`).
2. Allineare commenti e semantica timeout:
   - O implementare davvero `automatic STOP` con persistenza nel risultato,
   - oppure aggiornare commento/API contract per riflettere il semplice skip/advance.
3. Spostare lo stato su storage condiviso (Redis/DB) con locking atomico per contatori e avanzamento simulazione.

## Check eseguiti

- E2E regression: `python3 test_pipeline.py` (75/75 scenari OK).

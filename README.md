# V-Shuttle

Demo full-stack per la simulazione decisionale della navetta autonoma **V-Shuttle**.

Il progetto è composto da:
- **Backend** FastAPI (logica pipeline + API di simulazione)
- **Frontend** React + Vite (dashboard per upload dataset e monitoraggio simulazione)

## Architettura e integrazione frontend/backend

### Porte di default
- Backend: `http://127.0.0.1:8000`
- Frontend (Vite dev server): `http://127.0.0.1:5173`

### Come comunica il frontend con il backend
Il frontend usa base URL relativa `\`/api\`` (`frontend/src/api/client.ts`).
In sviluppo, Vite fa da proxy verso il backend:
- `\`/api\`` → `http://127.0.0.1:8000`
- `\`/health\`` → `http://127.0.0.1:8000`
- `\`/decision\`` → `http://127.0.0.1:8000`

In questo modo non servono URL hardcoded nel codice React e le chiamate restano coerenti con gli endpoint FastAPI.

## Endpoint principali backend

- `GET /health`
- `POST /decision/evaluate`
- `POST /api/datasets/load`
- `POST /api/simulations/start`
- `GET /api/simulations/{simulation_id}/state`
- `POST /api/simulations/{simulation_id}/human-decision`

### Payload `POST /api/datasets/load`

L'endpoint accetta **entrambi** i formati seguenti:

```json
{
  "scenarios": [
    { "id_scenario": 1, "sensori": { "camera_frontale": { "testo": "...", "confidenza": 0.9 }, "camera_laterale": { "testo": "...", "confidenza": 0.8 }, "V2I_receiver": { "testo": "...", "confidenza": 0.85 } }, "orario_rilevamento": "09:15", "giorno_settimana": "Lunedì" }
  ]
}
```

oppure direttamente un array JSON di scenari:

```json
[
  { "id_scenario": 1, "sensori": { "camera_frontale": { "testo": "...", "confidenza": 0.9 }, "camera_laterale": { "testo": "...", "confidenza": 0.8 }, "V2I_receiver": { "testo": "...", "confidenza": 0.85 } }, "orario_rilevamento": "09:15", "giorno_settimana": "Lunedì" }
]
```

## Avvio rapido (consigliato)

Dalla root del repository:

```bash
make run
```

Questo comando esegue `run_fullstack.sh`, che:
1. crea (se manca) il virtualenv backend in `backend/.venv`
2. installa dipendenze backend (`backend/requirements.txt`)
3. installa dipendenze frontend se `node_modules` manca
4. avvia backend con uvicorn
5. verifica `GET /health`
6. avvia frontend Vite
7. gestisce shutdown pulito di entrambi i processi con `Ctrl+C`

## Variabili ambiente utili

Puoi cambiare le porte senza modificare codice:

```bash
BACKEND_PORT=9000 FRONTEND_PORT=5174 make run
```

## Setup manuale (alternativa)

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend (in un altro terminale)
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Altri target Makefile

- `make install-backend` → prepara venv e installa dipendenze Python
- `make install-frontend` → installa dipendenze Node del frontend

## Struttura progetto (sintesi)

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── pipeline.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── run_fullstack.sh
├── Makefile
└── README.md
```

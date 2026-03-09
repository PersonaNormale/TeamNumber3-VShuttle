# V-Shuttle

Backend Python per la logica di fusione dei sensori della navetta autonoma V-Shuttle.

Il problema è fondere tre letture potenzialmente discordanti dello stesso cartello stradale, normalizzare il testo OCR sporco, interpretare eventuali divieti, eccezioni e vincoli temporali, e produrre una decisione deterministica tra `STOP`, `GO` e `HUMAN_REVIEW`. La logica decisionale deve risiedere nel codice applicativo e non può dipendere da modelli esterni in runtime, come richiesto dalla traccia. fileciteturn1file0

## Struttura attuale

```text
.
├── README.md
└── backend
    ├── .gitignore
    ├── requirements.txt
    └── app
        ├── __init__.py
        ├── main.py
        ├── models.py
        └── pipeline.py
```

## Scopo di questo primo step

Questo scaffolding copre solo il backend del primo task:

- caricamento scenari JSON
- modellazione input dei sensori
- punto di ingresso API/backend
- modulo dedicato alla pipeline logica

Il dataset contiene già casi che giustificano questa separazione minima: OCR sporco come `D1V1ET0`, `Z T L` e `R0T4T0R14`, sensori null, conflitti tra divieto ed eccezioni, regole con orari e giorni. fileciteturn1file1

## Avvio

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Passo successivo

Implementare dentro `pipeline.py` quattro funzioni pure:

1. `normalize_text`
2. `fuse_sensor_readings`
3. `parse_sign`
4. `decide_action`

#!/usr/bin/env python3
"""End-to-end test — processes all scenarios and compares with expected decisions."""
from __future__ import annotations

import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine import process_all

# ── Expected action per scenario (hand-verified) ──
EXPECTED: dict[int, str] = {
    70: "STOP",       # ZTL generica
    101: "ASK_HUMAN", # Sensori discordanti (DIVIETO vs ECCETTO NAVETTE)
    57: "STOP",       # ECCETTO SOCCORSO — non siamo soccorso
    91: "GO",         # PIAZZA DEL DUOMO — info
    40: "STOP",       # ECCETTO FORNITORE 08-10 — non siamo fornitori
    3: "STOP",        # ZTL 08-20, ore 10:00 — dentro orario
    10: "GO",         # DIVIETO ECCETTO BUS
    49: "GO",         # DIVIETO ECCETTO NAVETTE L4
    31: "GO",         # DIVIETO DI SOSTA — non riguarda transito
    61: "STOP",       # MERCATO VEN 06-14, ore 10:30 Ven
    93: "STOP",       # ZTL 0-24 SEMPRE
    69: "GO",         # ECCETTO VEICOLI ELETTRICI
    62: "GO",         # MERCATO VEN 06-14, ore 15:00 — fuori orario
    33: "GO",         # OBBLIGO SVOLTA DESTRA
    25: "GO",         # DIVIETO MEZZI PESANTI
    50: "STOP",       # DIVIETO generico
    13: "GO",         # ATTENZIONE PEDONI
    46: "GO",         # ZTL DALLE 20, ore 14:40
    30: "STOP",       # DIVIETO DI TRANSITO (spaced text)
    22: "GO",         # ZTL NOTTURNA 23-05, ore 16:00
    99: "ASK_HUMAN",  # front=DIVIETO ACCESSO vs side=DIVIETO ECCETTO BUS
    16: "GO",         # VARCO NON ATTIVO
    44: "ASK_HUMAN",  # MEZZI NON AUTORIZZATI
    79: "STOP",       # OCR D1V1ET0 → DIVIETO DI ACCESSO
    17: "STOP",       # ECCETTO RESIDENTI
    48: "GO",         # R0T4T0R14 → ROTATORIA
    42: "GO",         # LAVORI IN CORSO
    28: "GO",         # DOSSO ARTIFICIALE
    55: "STOP",       # DIVIETO LUN-VEN, giorno=Lunedì
    83: "GO",         # PARCHEGGIO
    71: "STOP",       # Z T L → ZTL
    2: "GO",          # DIVIETO ECCETTO BUS
    59: "GO",         # S3NS0 UN1C0 → SENSO UNICO ALTERNATO
    26: "GO",         # PASSAGGIO A LIVELLO
    68: "GO",         # ACCESSO CONSENTITO VEICOLI ELETTRICI
    38: "GO",         # Z0N4 30 → ZONA 30
    39: "GO",         # DIVIETO DI FERMATA
    82: "GO",         # 5T4Z10N3 → STAZIONE FERROVIARIA
    100: "GO",        # LAVORI
    85: "GO",         # CENTRO STORICO
    32: "GO",         # ATTENZIONE BAMBINI
    54: "GO",         # ZTL VARCO NON ATTIVO
    5: "GO",          # LAVORI IN CORSO
    24: "STOP",       # 4R3A P3D0NAL3 → AREA PEDONALE
    96: "STOP",       # ZTL SPERIMENTALE
    97: "STOP",       # ZTL 18-24, ore 19:30
    103: "GO",        # ZTL ECCETTO NAVETTE L4
    90: "GO",         # TUTTE LE DIREZIONI
    45: "STOP",       # ZTL DALLE 20, ore 21:05
    53: "STOP",       # ZTL VARCO ATTIVO
    78: "GO",         # ZTL 22-06, ore 10:00
    76: "GO",         # DIVIETO VEICOLI A MOTORE — navetta elettrica
    4: "GO",          # ZTL 08-20, ore 21:30
    88: "STOP",       # ZTL FESTIVI, Domenica
    89: "GO",         # ZTL FESTIVI, Martedì
    66: "GO",         # FINE ZTL
    104: "GO",        # NAVETTE L4 NOTTE — info
    81: "GO",         # STAZIONE FERROVIARIA
    18: "GO",         # LIMITE 30 KM/H
    58: "GO",         # SENSO UNICO ALTERNATO
    84: "GO",         # DIVIETO DI AFFISSIONE
    23: "STOP",       # AREA PEDONALE
    11: "STOP",       # SENSO VIETATO
    1: "STOP",        # DIVIETO DI ACCESSO
    14: "GO",         # STRADA SENZA USCITA
    94: "STOP",       # "D I V E T O D I A C C S S O" → DIVIETO
    29: "GO",         # RALLENTARE
    72: "GO",         # DIVIETO DI SCARICO RIFIUTI
    63: "GO",         # MERCATO VEN, giorno=Martedì
    95: "GO",         # STRADA DISSESTATA
    37: "GO",         # ZONA 30
    105: "ASK_HUMAN", # tutti sensori null
    41: "STOP",       # ECCETTO FORNITORE ore 14:00
    9: "ASK_HUMAN",   # ECCETTO AUTORIZZATI
    73: "GO",         # DIVIETO ECCETTO BUS E TAXI
}


def main() -> None:
    input_path = ROOT / "VShuttle-input.json"
    scenarios = json.loads(input_path.read_text(encoding="utf-8"))

    results = process_all(scenarios)

    passed = failed = 0
    header = f"{'ID':>4} {'ACTION':>10} {'EXPECTED':>10} {'OK':>4} {'CONF':>6}  {'FUSED TEXT':35s}  REASON"
    print(header)
    print("-" * len(header) + "-" * 40)

    for r in results:
        sid = r["id_scenario"]
        action = r["action"]
        expected = EXPECTED.get(sid, "?")
        ok = "✅" if action == expected else "❌"
        if action == expected:
            passed += 1
        else:
            failed += 1
        print(
            f"{sid:>4} {action:>10} {expected:>10} {ok:>4} "
            f"{r['confidence']:>6.3f}  {r['fused_text'][:35]:35s}  {r['reason'][:55]}"
        )

    print("-" * 120)
    print(f"RESULT: {passed} ✅  /  {failed} ❌  out of {len(results)} scenarios")

    # Save legacy JSON output
    out_path = ROOT / "output" / "results.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nLegacy JSON saved → {out_path}")


if __name__ == "__main__":
    main()

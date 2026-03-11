"""OCR correction module — cleans up noisy sensor text readings."""
from __future__ import annotations

import re

# Digit → letter mapping for common OCR errors
DIGIT_TO_LETTER = {
    "0": "O",
    "1": "I",
    "3": "E",
    "4": "A",
    "5": "S",
    "7": "T",
    "8": "B",
}



DIZIONARIO = {
    # --- Divieti, Accessi e ZTL ---
    "DIVIETO", "TRANSITO", "ACCESSO", "SOSTA", "FERMATA", "CIRCOLAZIONE",
    "INGRESSO", "AFFISSIONE", "SCARICO", "RIFIUTI", "ZTL", "ZONA", 
    "TRAFFICO", "LIMITATO", "LIMITATA", "VARCO", "ATTIVO", "ATTIVA", 
    "INATTIVO", "SPERIMENTALE", "NOTTURNA", "AREA", "PEDONALE", "SENSO", 
    "VIETATO", "UNICO", "ALTERNATO", "RIMOZIONE", "FORZATA",

    # --- Veicoli e Utenti ---
    "BUS", "TAXI", "NAVETTE", "NAVETTA", "RESIDENTI", "AUTORIZZATI", 
    "FORNITORE", "FORNITORI", "SOCCORSO", "ELETTRICI", "ELETTRICO", 
    "PUBBLICI", "MEZZI", "PESANTI", "MOTORE", "VEICOLI", "MOTO", 
    "MOTOCICLI", "CICLOMOTORI", "AUTOCARRI", "AUTOTRENI", "RIMORCHI", 
    "CARAVAN", "CAMPER", "BICICLETTE", "VELOCIPEDI", "MACCHINE", 
    "AGRICOLE", "DISABILI", "INVALIDI", "DONNE", "GRAVIDANZA", "INCINTA",
    "FORZE", "ORDINE", "ECCETTO",

    # --- Obblighi, Azioni e Direzioni ---
    "OBBLIGO", "SVOLTA", "DESTRA", "SINISTRA", "ROTATORIA", "PRECEDENZA", 
    "STOP", "DARE", "FERMARSI", "ARRESTO", "SPEGNERE", "FINE", "TUTTE", 
    "DIREZIONI", "CONSENTITO", "NORD", "SUD", "EST", "OVEST",

    # --- Infrastrutture e Servizi ---
    "STAZIONE", "FERROVIARIA", "MERCATO", "RIONALE", "SCUOLA", "STRADA", 
    "USCITA", "CENTRO", "STORICO", "PIAZZA", "DEL", "DUOMO", "AUTOSTRADA", 
    "TANGENZIALE", "STATALE", "PROVINCIALE", "GALLERIA", "PONTE", 
    "SOTTOPASSAGGIO", "CAVALCAVIA", "CORSIA", "EMERGENZA", "OSPEDALE", 
    "PRONTO", "CARABINIERI", "POLIZIA", "MUNICIPALE", "LOCALE", 
    "AEROPORTO", "PORTO", "DOGANA", "INFO",

    # --- Pericoli, Meteo e Condizioni Stradali ---
    "LAVORI", "CORSO", "DOSSO", "ARTIFICIALE", "RALLENTARE", "ATTENZIONE", 
    "PEDONI", "BAMBINI", "PASSAGGIO", "LIVELLO", "DISSESTATA", "NEBBIA", 
    "NEVE", "GHIACCIO", "PIOGGIA", "CATENE", "GOMME", "TERMICHE", 
    "ALLAGAMENTO", "PERICOLO", "CADUTA", "MASSI", "ANIMALI", "SELVATICI", 
    "VAGANTI", "BANCHINA", "CEDEVOLE", "CURVA", "PERICOLOSA", "INCIDENTE", 
    "CODE", "NEVISCHIO", "INCROCIO", "SEMAFORO", "DEVIAZIONE", 
    "RESTRINGIMENTO", "CARREGGIATA",

    # --- Misure, Limiti, Tempi e Pagamenti ---
    "LIMITE", "MASSIMO", "PARCHEGGIO", "PAGAMENTO", "ORE", "DALLE", "ALLE", 
    "SOLO", "GIORNI", "FESTIVI", "FERIALI", "NOTTE", "SERA", "SEMPRE", 
    "KM", "KM/H", "MAX", "MT", "M", "T", "L4", "PEDAGGIO", "TELEPASS", 
    "CARTE", "CONTANTI", "MONETE", "CASSA", "DISCO", "ORARIO", "TARIFFA", 
    "ABBONAMENTO", "ABBONAMENTI", "GRATUITO",

    # --- Preposizioni, Avverbi e Giorni ---
    "PER", "NON", "DI", "IN", "AI", "AL", "LE", "A", "DAL", "OK", "NO",
    "LUNEDI", "MARTEDI", "MERCOLEDI", "GIOVEDI", "VENERDI", "SABATO", "DOMENICA",
    "LUNEDÌ", "MARTEDÌ", "MERCOLEDÌ", "GIOVEDÌ", "VENERDÌ"
}


def _collapse_spaced_letters(text: str) -> str:
    """'D I V I E T O' → 'DIVIETO', 'Z T L' → 'ZTL'."""

    def _replacer(m: re.Match) -> str:
        return m.group(0).replace(" ", "")

    # Sequences of single chars separated by single spaces (min 2 chars)
    return re.sub(r"(?<!\S)([A-Z0-9] ){2,}[A-Z0-9](?!\S)", _replacer, text)


def _remove_dots_between_letters(text: str) -> str:
    """'V.A.R.C.O.' → 'VARCO'."""
    return re.sub(
        r"\b([A-Z])(?:\.[A-Z]){2,}\.?",
        lambda m: m.group(0).replace(".", ""),
        text,
    )


def _replace_digits(text: str) -> tuple[str, int]:
    """Replace digits that look like OCR-mangled letters.

    Strategy: split into alphanumeric tokens.  Pure-digit tokens (e.g. '30',
    '08') are real numbers and kept.  Mixed letter+digit tokens longer than 2
    chars get digit→letter replacement (e.g. 'ROTATOR14' → 'ROTATORIA').
    Short mixed tokens (≤2 chars, e.g. 'L4') are kept as-is.
    """
    parts = re.split(r"([^A-Za-z0-9]+)", text)
    n_subs = 0
    out: list[str] = []
    for part in parts:
        has_digit = any(ch.isdigit() for ch in part)
        has_alpha = any(ch.isalpha() for ch in part)
        if has_digit and has_alpha and len(part) > 2:
            # Mixed token — replace digits
            new = []
            for ch in part:
                if ch in DIGIT_TO_LETTER:
                    new.append(DIGIT_TO_LETTER[ch])
                    n_subs += 1
                else:
                    new.append(ch)
            out.append("".join(new))
        else:
            out.append(part)
    return "".join(out), n_subs


def _merge_fragments(text: str) -> tuple[str, int]:
    """Merge adjacent short word fragments that combine into a known word."""
    from difflib import SequenceMatcher
    tokens = text.split()
    count = 0
    changed = True
    while changed:
        changed = False
        new_tokens: list[str] = []
        i = 0
        while i < len(tokens):
            if i + 1 < len(tokens) and len(tokens[i]) <= 6 and len(tokens[i + 1]) <= 6:
                combined = tokens[i] + tokens[i + 1]
                if combined in DIZIONARIO:
                    new_tokens.append(combined)
                    count += 1
                    i += 2
                    changed = True
                    continue
                if len(combined) >= 5:
                    best = max(
                        DIZIONARIO,
                        key=lambda w, c=combined: SequenceMatcher(None, c, w).ratio(),
                    )
                    if SequenceMatcher(None, combined, best).ratio() >= 0.85:
                        new_tokens.append(best)
                        count += 1
                        i += 2
                        changed = True
                        continue
            new_tokens.append(tokens[i])
            i += 1
        tokens = new_tokens
    return " ".join(tokens), count


def _fuzzy_correct_words(text: str) -> tuple[str, int]:
    """Fix single misspelled words by matching against DIZIONARIO."""
    from difflib import SequenceMatcher
    tokens = text.split()
    count = 0
    for idx, token in enumerate(tokens):
        if token in DIZIONARIO or len(token) < 4:
            continue
        best = max(
            DIZIONARIO,
            key=lambda w, t=token: SequenceMatcher(None, t, w).ratio(),
        )
        if SequenceMatcher(None, token, best).ratio() >= 0.85:
            tokens[idx] = best
            count += 1
    return " ".join(tokens), count


def correct_ocr(raw_text: str | None) -> tuple[str, float]:
    """Clean an OCR sensor reading.

    Returns
    -------
    (corrected_text, ocr_confidence)
        ocr_confidence is 1.0 when no correction was needed and decreases
        with the number of substitutions applied.
    """
    if raw_text is None or raw_text.strip() == "":
        return "", 0.0

    text = raw_text.upper().strip()

    # Step 1 – collapse spaced single letters
    text = _collapse_spaced_letters(text)

    # Step 2 – remove dots between single letters
    text = _remove_dots_between_letters(text)

    # Step 3 – normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Step 4 – replace digit→letter OCR artefacts
    text, n_subs = _replace_digits(text)

    # Step 5 – merge adjacent fragments into known words
    text, n_merge = _merge_fragments(text)
    n_subs += n_merge

    # Step 6 – fuzzy-correct remaining misspelled words
    text, n_fuzzy = _fuzzy_correct_words(text)
    n_subs += n_fuzzy

    # Step 7 – confidence penalty per substitution

    '''
    Baseline: 1.0 (lettura zero-mutation).

    Decadimento: -0.15 per ogni mutazione
                 (proxy dell'edit distance: digit->letter, merge, fuzzy-match).

    Lower bound: 0.0. Garantisce il collasso deterministico della confidenza per
                      input ad alta entropia, forzando il fallback logico di sicurezza a valle.
    '''
    ocr_confidence = max(0.0, 1.0 - (n_subs * 0.15))

    return text, ocr_confidence


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cases = [
        "D1V1ET0 D1 ACCE550",
        "4R3A P3D0NAL3",
        "R0T4T0R14",
        "S3NS0 UN1C0 4LT3RN4T0",
        "5T4Z10N3 F3RR0V14R14",
        "Z0N4 30",
        "D I V I E T O   D I   T R A N S I T O",
        "Z T L",
        "ZTL V.A.R.C.O. NON ATTIVO",
        "D I V  E T O  D I  A C C S S O",
        "ZTL ATTIVA 08:00 - 20:00",
        "DIVIETO DI TRANSITO ECCETTO BUS",
        None,
    ]
    for raw in cases:
        corrected, conf = correct_ocr(raw)
        print(f"  {str(raw):45s} → {corrected:40s} (conf={conf:.2f})")

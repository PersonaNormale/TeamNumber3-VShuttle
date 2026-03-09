"""Decision engine — maps parsed sign info to STOP / GO / ASK_HUMAN."""
from __future__ import annotations

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from models import SignInfo, Decision

# Exceptions that apply to the V-Shuttle
# The shuttle counts as: BUS, NAVETTA L4, electric vehicle, public transport
NAVETTA_EXCEPTIONS = {
    "BUS", "NAVETTE_L4", "ELETTRICI", "MEZZI_PUBBLICI",
    "TAXI", "ACCESSO_CONSENTITO",
}

# Prohibitions that do NOT concern vehicle transit
DIVIETI_NON_TRANSITO = {"SOSTA", "FERMATA", "AFFISSIONE", "SCARICO"}

GIORNI_FERIALI = {"Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"}


def _is_festivo(giorno: str) -> bool:
    return giorno in {"Sabato", "Domenica"}


def _is_in_time_range(orario: str, time_range: tuple) -> bool:
    """Check whether *orario* (HH:MM) falls inside *time_range*.

    Handles cross-midnight ranges like 23:00→05:00.
    """
    try:
        h, m = (int(x) for x in orario.split(":"))
        cur = h * 60 + m
        (sh, sm), (eh, em) = time_range
        start = sh * 60 + sm
        end = eh * 60 + em
        if end == 0:
            end = 24 * 60
        if start <= end:
            return start <= cur < end
        else:
            return cur >= start or cur < end
    except (ValueError, TypeError):
        return True  # assume inside (safety)


def _is_in_day_range(giorno: str, days: list[str]) -> bool:
    if not days:
        return True
    for d in days:
        if d == "FESTIVI" and _is_festivo(giorno):
            return True
        if d == "FERIALI" and giorno in GIORNI_FERIALI:
            return True
        if d == "LUN-VEN" and giorno in GIORNI_FERIALI:
            return True
        # Specific day match (VENERDI ↔ Venerdì)
        if giorno.upper().startswith(d[:5]):
            return True
    return False


def _fmt_time(tr: tuple) -> str:
    (sh, sm), (eh, em) = tr
    return f"{sh:02d}:{sm:02d}-{eh:02d}:{em:02d}"


def decide(
    sign_info: SignInfo,
    fusion_confidence: float,
    orario: str,
    giorno: str,
    scenario_id: int,
    fused_text: str,
    sensori_raw: dict,
) -> Decision:
    """Core decision logic."""

    def _mk(action: str, confidence: float, reason: str) -> Decision:
        return Decision(
            scenario_id=scenario_id,
            action=action,
            confidence=round(min(max(confidence, 0.0), 1.0), 3),
            fused_text=fused_text,
            sign_type=sign_info.sign_type,
            exceptions=sign_info.exceptions,
            reason=reason,
            orario_rilevamento=orario,
            giorno_settimana=giorno,
            sensori_raw=sensori_raw,
        )

    st = sign_info.sign_type
    sub = sign_info.sub_type
    exc = set(sign_info.exceptions)

    # 0 — no data at all
    if fusion_confidence == 0.0 or (st == "SCONOSCIUTO" and not sign_info.raw_text):
        return _mk("ASK_HUMAN", 0.0,
                    "Nessun sensore disponibile — richiesta conferma operatore")

    # 1 — FINE ZTL
    if st == "ZTL" and sign_info.is_fine_zona:
        return _mk("GO", fusion_confidence, "Fine zona ZTL — proseguire")

    # 2 — VARCO NON ATTIVO
    if st == "ZTL" and sign_info.varco_attivo is False:
        return _mk("GO", fusion_confidence,
                    "Varco ZTL non attivo — transito consentito")

    # 3 — VARCO ATTIVO
    if st == "ZTL" and sign_info.varco_attivo is True:
        if exc & NAVETTA_EXCEPTIONS:
            return _mk("GO", fusion_confidence,
                        f"Varco ZTL attivo con eccezione {', '.join(exc & NAVETTA_EXCEPTIONS)}")
        return _mk("STOP", fusion_confidence,
                    "Varco ZTL attivo — fermata obbligatoria")

    # 4 — explicit access granted
    if st == "ACCESSO_CONSENTITO":
        return _mk("GO", fusion_confidence,
                    "Accesso esplicitamente consentito")

    # 5 — shuttle service info
    if st == "INFO_NAVETTE":
        return _mk("GO", fusion_confidence,
                    "Informazione servizio navette — proseguire")

    # 6 — informational sign
    if st == "INFO":
        return _mk("GO", fusion_confidence,
                    "Segnale informativo — nessun divieto di transito")

    # 6b — very low confidence (before content-based rules)
    if fusion_confidence < 0.31:
        return _mk("ASK_HUMAN", fusion_confidence,
                    "Lettura poco affidabile — conferma operatore necessaria")

    # 7 — OBBLIGO
    if st == "OBBLIGO":
        return _mk("GO", fusion_confidence,
                    "Obbligo di navigazione — seguire indicazione")

    # 8 — SENSO UNICO
    if st == "SENSO_UNICO":
        return _mk("GO", fusion_confidence,
                    "Senso unico — proseguire nella direzione consentita")

    # 9 — non-transit prohibitions
    if st == "DIVIETO" and sub in DIVIETI_NON_TRANSITO:
        return _mk("GO", fusion_confidence,
                    f"Divieto di {sub.lower()} — non riguarda il transito")

    # 10 — heavy vehicles
    if st == "DIVIETO" and sub == "MEZZI_PESANTI":
        return _mk("GO", fusion_confidence,
                    "Divieto per mezzi pesanti — la navetta non è un mezzo pesante")

    # 11 — combustion vehicles
    if st == "DIVIETO" and sub == "VEICOLI_MOTORE":
        return _mk("GO", fusion_confidence,
                    "Divieto per veicoli a motore — la navetta è elettrica")

    # 12 — applicable shuttle exception (BUS / L4 / electric / …)
    applicable = exc & NAVETTA_EXCEPTIONS
    if applicable and st in ("DIVIETO", "ZTL", "AREA_PEDONALE"):
        return _mk("GO", fusion_confidence,
                    f"Eccezione per {', '.join(applicable)} — la navetta può transitare")

    # 13 — ECCETTO standalone
    if st == "ECCETTO_STANDALONE":
        if "ELETTRICI" in exc:
            return _mk("GO", fusion_confidence,
                        "Eccezione per veicoli elettrici — la navetta può transitare")
        if exc - NAVETTA_EXCEPTIONS:
            return _mk("STOP", fusion_confidence,
                        "Divieto con eccezione non applicabile alla navetta")
        return _mk("STOP", fusion_confidence,
                    "Divieto con eccezione non applicabile alla navetta")

    # 14 — unauthorised vehicles
    if st == "DIVIETO" and sub == "ACCESSO_NON_AUTORIZZATI":
        return _mk("ASK_HUMAN", fusion_confidence * 0.6,
                    "Divieto per mezzi non autorizzati — verifica autorizzazione")

    # 15 — "ECCETTO AUTORIZZATI"
    if "AUTORIZZATI" in exc:
        return _mk("ASK_HUMAN", fusion_confidence * 0.6,
                    "Eccezione per autorizzati — verifica se la navetta è autorizzata")

    # 16 — MERCATO (day + time gated)
    if st == "MERCATO":
        if not _is_in_day_range(giorno, sign_info.days):
            return _mk("GO", fusion_confidence,
                        f"Mercato non attivo oggi ({giorno})")
        if sign_info.time_range and not _is_in_time_range(orario, sign_info.time_range):
            return _mk("GO", fusion_confidence,
                        f"Mercato fuori orario (attivo {_fmt_time(sign_info.time_range)})")
        return _mk("STOP", fusion_confidence,
                    "Mercato rionale attivo — strada bloccata")

    # 17 — time-gated restriction
    if sign_info.time_range:
        if not _is_in_time_range(orario, sign_info.time_range):
            return _mk("GO", fusion_confidence,
                        f"Fuori dall'orario di validità ({_fmt_time(sign_info.time_range)})")

    # 18 — day-gated restriction
    if sign_info.days:
        if not _is_in_day_range(giorno, sign_info.days):
            return _mk("GO", fusion_confidence,
                        f"Vincolo non attivo oggi ({giorno})")

    # 20 — SENSO VIETATO
    if st == "SENSO_VIETATO":
        return _mk("STOP", fusion_confidence,
                    "Senso vietato — fermata obbligatoria")

    # 21 — AREA PEDONALE
    if st == "AREA_PEDONALE":
        return _mk("STOP", fusion_confidence,
                    "Area pedonale — transito vietato ai veicoli")

    # 22 — ZTL (active, no valid exception)
    if st == "ZTL":
        return _mk("STOP", fusion_confidence,
                    "Zona a Traffico Limitato attiva")

    # 23 — DIVIETO (active, no valid exception)
    if st == "DIVIETO":
        label = f"Divieto di {sub.lower()}" if sub and sub != "GENERICO" else "Divieto"
        return _mk("STOP", fusion_confidence,
                    f"{label} — nessuna eccezione applicabile")

    # 24 — unknown sign
    if fusion_confidence >= 0.70:
        return _mk("GO", fusion_confidence * 0.9,
                    "Cartello non riconosciuto come divieto — proseguire con cautela")
    return _mk("ASK_HUMAN", fusion_confidence,
               "Cartello non riconosciuto — conferma operatore necessaria")


def to_legacy_json(decision: Decision) -> dict:
    """Serialize a Decision to the Legacy JSON format required by the client."""
    return {
        "id_scenario": decision.scenario_id,
        "action": decision.action,
        "confidence": decision.confidence,
        "fused_text": decision.fused_text,
        "sign_type": decision.sign_type,
        "exceptions": decision.exceptions,
        "reason": decision.reason,
        "orario_rilevamento": decision.orario_rilevamento,
        "giorno_settimana": decision.giorno_settimana,
        "sensori_raw": decision.sensori_raw,
    }

"""Semantic sign parser — extracts structured info from fused text."""
from __future__ import annotations

import re
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from models import SignInfo


# ── Time-range extraction ────────────────────────────────────────────────

def _parse_time_range(text: str) -> tuple | None:
    # "SEMPRE" or "0-24"
    if re.search(r"\b0\s*[-–]\s*24\b|SEMPRE", text):
        return ((0, 0), (24, 0))

    # "DALLE 08:00 ALLE 10:00"
    m = re.search(
        r"DALL[EA]?\s*(\d{1,2})[.:](\d{2})\s*ALL[EA]?\s*(\d{1,2})[.:](\d{2})",
        text,
    )
    if m:
        return (
            (int(m.group(1)), int(m.group(2))),
            (int(m.group(3)), int(m.group(4))),
        )

    # "08:00 - 20:00"  /  "08:00-20:00"  /  "8:00 20:00"
    m = re.search(
        r"(\d{1,2})[.:](\d{2})\s*[-–\s]\s*(\d{1,2})[.:](\d{2})", text
    )
    if m:
        return (
            (int(m.group(1)), int(m.group(2))),
            (int(m.group(3)), int(m.group(4))),
        )

    # "DALLE 20" (start only → until midnight)
    m = re.search(r"DALL[EA]?\s*(\d{1,2})[.:]?(\d{2})?(?!\d)", text)
    if m:
        h = int(m.group(1))
        mi = int(m.group(2)) if m.group(2) else 0
        return ((h, mi), (24, 0))

    # "08-20" / "22-06" (short, no minutes)
    m = re.search(r"\b(\d{1,2})\s*[-–]\s*(\d{1,2})\b", text)
    if m:
        h1, h2 = int(m.group(1)), int(m.group(2))
        # Avoid false positives like "ZONA 30", "LIMITE 10" etc.
        if h1 <= 24 and h2 <= 24 and h1 != h2:
            return ((h1, 0), (h2, 0))

    return None


# ── Day extraction ───────────────────────────────────────────────────────

def _parse_days(text: str) -> list[str]:
    days: list[str] = []
    if re.search(r"FESTIV[OI]", text):
        days.append("FESTIVI")
    if re.search(r"FERIAL[EI]", text):
        days.append("FERIALI")
    if re.search(
        r"(DAL\s*)?LUNED[IÌ]\s*(AL\s*)?VENERD[IÌ]|LUN[\s-]*VEN", text
    ):
        days.append("LUN-VEN")
    # Specific day name (e.g. VENERDI in "MERCATO VENERDI 06-14")
    for giorno in [
        "LUNEDI", "MARTEDI", "MERCOLEDI", "GIOVEDI",
        "VENERDI", "SABATO", "DOMENICA",
    ]:
        if re.search(rf"\b{giorno[:6]}", text):
            days.append(giorno)
    return days


# ── Exception extraction ─────────────────────────────────────────────────

def _parse_exceptions(text: str) -> list[str]:
    exc: list[str] = []
    if re.search(r"ECCETTO\s.*?BUS|BUS\s*(E\s*)?TAXI\s*OK|BUS\s*OK|\bBUS\b.*\bOK\b", text):
        exc.append("BUS")
    if re.search(r"ECCETTO\s.*?TAXI|TAXI\s*OK", text):
        exc.append("TAXI")
    if re.search(
        r"NAVETT[EA]?\s*L4\s*(OK|CONSENTIT)?|ECCETTO\s*NAVETT|L4\s*OK",
        text,
    ):
        exc.append("NAVETTE_L4")
    if re.search(
        r"ECCETTO\s.*?(VEICOLI\s*)?ELETTRIC[IO]|ELETTRIC[IO]\s*OK|ACCESSO\s*(VEICOLI\s*)?ELETTRIC", text
    ):
        exc.append("ELETTRICI")
    if re.search(r"ECCETTO\s.*?MEZZI\s*(DI\s*)?SOCCORSO|ECCETTO\s*SOCCORSO", text):
        exc.append("SOCCORSO")
    if re.search(r"ECCETTO\s.*?RESIDENTI", text):
        exc.append("RESIDENTI")
    if re.search(r"ECCETTO\s.*?AUTORIZZATI", text):
        exc.append("AUTORIZZATI")
    if re.search(r"ECCETTO\s.*?FORNITOR[EI]", text):
        exc.append("FORNITORE")
    if re.search(r"ECCETTO\s.*?MEZZI\s*PUBBLIC", text):
        exc.append("MEZZI_PUBBLICI")
    if re.search(r"ACCESSO\s*CONSENTITO", text):
        exc.append("ACCESSO_CONSENTITO")
    return exc


# ── Main parser ──────────────────────────────────────────────────────────

def parse_sign(text: str) -> SignInfo:
    """Analyse the fused sign text and return structured SignInfo."""
    if not text or not text.strip():
        return SignInfo(
            sign_type="SCONOSCIUTO", raw_text="", sub_type="ILLEGGIBILE"
        )

    t = text.upper().strip()
    exceptions = _parse_exceptions(t)
    time_range = _parse_time_range(t)
    days = _parse_days(t)

    # ── FINE ZTL ──
    if re.search(r"FINE\s*Z\.?T\.?L|USCITA\s*Z\.?T\.?L", t):
        return SignInfo("ZTL", t, exceptions, time_range, days,
                        varco_attivo=None, is_fine_zona=True)

    # ── ZTL VARCO ──
    if re.search(r"VARCO", t):
        non_attivo = bool(re.search(r"NON\s*ATTIV|INATTIV", t))
        return SignInfo("ZTL", t, exceptions, time_range, days,
                        varco_attivo=not non_attivo)

    # ── ZTL ──
    if re.search(r"\bZ\.?T\.?L\.?\b|ZONA\s*TRAFFICO\s*LIMITAT", t):
        return SignInfo("ZTL", t, exceptions, time_range, days)

    # ── AREA PEDONALE ──
    if re.search(r"AREA\s*PEDONALE", t):
        return SignInfo("AREA_PEDONALE", t, exceptions, time_range, days)

    # ── SENSO VIETATO ──
    if re.search(r"SENSO\s*VIETATO", t):
        return SignInfo("SENSO_VIETATO", t, exceptions, time_range, days)

    # ── DIVIETO with sub-type ──
    m_div = re.search(
        r"DIVIETO\s*(DI\s*)?"
        r"(TRANSITO|ACCESSO|SOSTA|FERMATA|CIRCOLAZIONE|"
        r"INGRESSO|AFFISSIONE|SCARICO)",
        t,
    )
    if m_div:
        sub = m_div.group(2) or ""
        # Refine sub_type when extra qualifiers follow
        if re.search(r"MEZZI\s*PESANTI", t):
            sub = "MEZZI_PESANTI"
        elif re.search(r"VEICOLI\s*(A\s*)?MOTORE", t):
            sub = "VEICOLI_MOTORE"
        elif re.search(r"MEZZI\s*(NON\s*)?AUTORIZZATI", t):
            sub = "ACCESSO_NON_AUTORIZZATI"
        return SignInfo("DIVIETO", t, exceptions, time_range, days,
                        sub_type=sub)

    # ── DIVIETO generic ──
    if re.search(r"\bDIVIETO\b", t):
        if re.search(r"MEZZI\s*(NON\s*)?AUTORIZZATI", t):
            return SignInfo("DIVIETO", t, exceptions, time_range, days,
                            sub_type="ACCESSO_NON_AUTORIZZATI")
        if re.search(r"MEZZI\s*PESANTI", t):
            return SignInfo("DIVIETO", t, exceptions, time_range, days,
                            sub_type="MEZZI_PESANTI")
        if re.search(r"VEICOLI\s*(A\s*)?MOTORE", t):
            return SignInfo("DIVIETO", t, exceptions, time_range, days,
                            sub_type="VEICOLI_MOTORE")
        return SignInfo("DIVIETO", t, exceptions, time_range, days,
                        sub_type="GENERICO")

    # ── ECCETTO standalone (implies a prohibition) ──
    if re.search(r"^ECCETTO\s", t):
        return SignInfo("ECCETTO_STANDALONE", t, exceptions, time_range, days)

    # ── MERCATO ──
    if re.search(r"MERCATO", t):
        return SignInfo("MERCATO", t, exceptions, time_range, days)

    # ── OBBLIGO ──
    if re.search(r"OBBLIGO", t):
        return SignInfo("OBBLIGO", t, exceptions, time_range, days)

    # ── SENSO UNICO ──
    if re.search(r"SENSO\s*UNICO", t):
        return SignInfo("SENSO_UNICO", t, exceptions, time_range, days)

    # ── ACCESS CONSENTITO (explicit GO) ──
    if re.search(r"ACCESSO\s*(CONSENTITO|ELETTRIC)|OK\s", t):
        return SignInfo("ACCESSO_CONSENTITO", t, exceptions, time_range, days)

    # ── NAVETTE L4 service info ──
    if re.search(r"NAVETT", t):
        return SignInfo("INFO_NAVETTE", t, exceptions, time_range, days)

    # ── Generic informational sign ──
    info_kw = (
        r"LAVORI|DOSSO|RALLENTARE|ATTENZIONE|PASSAGGIO\s*A?\s*LIVELLO|"
        r"LIMITE|ZONA\s*30|PARCHEGGIO|CENTRO\s*STORICO|STAZIONE|PIAZZA|"
        r"TUTTE\s*(LE\s*)?DIREZIONI|STRADA|ROTATORIA|BAMBINI|PEDONI|"
        r"DISSESTATA|KM"
    )
    if re.search(info_kw, t):
        return SignInfo("INFO", t, exceptions, time_range, days)

    # ── Unknown ──
    return SignInfo("SCONOSCIUTO", t, exceptions, time_range, days)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        "ZTL ATTIVA 08:00 - 20:00",
        "DIVIETO DI TRANSITO ECCETTO BUS",
        "ZTL VARCO NON ATTIVO",
        "FINE ZTL",
        "ZTL SOLO GIORNI FESTIVI",
        "MERCATO RIONALE VENERDI 06:00-14:00",
        "DIVIETO DI ACCESSO DAL LUNEDI AL VENERDI",
        "ECCETTO VEICOLI ELETTRICI",
        "AREA PEDONALE",
        "ZTL ATTIVA DALLE 20",
        "ZTL NOTTURNA 23:00-05:00",
        "ECCETTO FORNITORE DALLE 08:00 ALLE 10:00",
        "DIVIETO DI TRANSITO PER VEICOLI A MOTORE",
    ]
    for t in tests:
        info = parse_sign(t)
        print(
            f"  {t:50s} → type={info.sign_type:20s} exc={info.exceptions} "
            f"time={info.time_range} days={info.days} varco={info.varco_attivo} "
            f"fine={info.is_fine_zona} sub={info.sub_type}"
        )

"""Weighted sensor fusion module."""
from __future__ import annotations

from difflib import SequenceMatcher

from engine.ocr_corrector import correct_ocr

# Base reliability weights
WEIGHTS: dict[str, float] = {
    "camera_frontale": 0.50,
    "camera_laterale": 0.30,
    "V2I_receiver": 0.20,
}


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _has_exception_conflict(texts: list[str]) -> bool:
    """True when sensors disagree on whether an exception exists."""
    has_eccetto = [("ECCETTO" in t or "OK" in t) for t in texts]
    if len(texts) >= 2 and any(has_eccetto) and not all(has_eccetto):
        has_divieto = [("DIVIETO" in t or "NO " in t) for t in texts]
        if any(has_divieto):
            return True
    return False


def fuse_sensors(sensori: dict) -> tuple[str, float, dict]:
    """Fuse three sensor readings into a single text + confidence.

    Returns
    -------
    (fused_text, confidence, raw_sensors_dict)
    """
    # ---- 1. Collect active (non-null) readings ----
    readings: list[dict] = []
    raw_dict: dict[str, str | None] = {}

    # ---- 1. Data Ingestion & V2I Bypass ----
    for source, data in sensori.items():
        raw_text = data.get("testo") if isinstance(data, dict) else None
        raw_conf = data.get("confidenza") if isinstance(data, dict) else None
        raw_dict[source] = raw_text

        if raw_text is not None and str(raw_text).strip() != "":
            sensor_c = float(raw_conf) if raw_conf is not None else 0.5

            if source == "V2I_receiver":
                readings.append({
                    "source": source,
                    "raw": raw_text,
                    "corrected": raw_text.upper().strip(),
                    "sensor_conf": sensor_c,
                    "ocr_conf": 1.0,
                    "weight": WEIGHTS.get(source, 0.20),
                })
            else:
                corrected, ocr_conf = correct_ocr(raw_text)
                if corrected:
                    readings.append({
                        "source": source,
                        "raw": raw_text,
                        "corrected": corrected,
                        "sensor_conf": sensor_c,
                        "ocr_conf": ocr_conf,
                        "weight": WEIGHTS.get(source, 0.50),
                    })

    if not readings:
        return "", 0.0, raw_dict

    if len(readings) == 1:
        r = readings[0]
        conf = r["sensor_conf"] * r["ocr_conf"] * 0.80
        return r["corrected"], round(conf, 3), raw_dict

    # ---- 2. Normalisation & Conflict Detection ----
    total_w = sum(r["weight"] for r in readings)
    for r in readings:
        r["norm_weight"] = r["weight"] / total_w

    n = len(readings)
    sim_matrix: dict[tuple[int, int], float] = {}
    for i in range(n):
        for j in range(i + 1, n):
            sim_matrix[(i, j)] = _similarity(readings[i]["corrected"], readings[j]["corrected"])

    corrected_texts = [r["corrected"] for r in readings]
    if _has_exception_conflict(corrected_texts):
        # In caso di conflitto su eccezioni critiche, affidabilità ridotta al minimo
        best = max(readings, key=lambda r: r["norm_weight"] * r["sensor_conf"])
        conf = best["sensor_conf"] * best["ocr_conf"] * 0.25
        return best["corrected"], round(conf, 3), raw_dict

    # ---- 3. Cluster Resolution & Confidence Bounding ----
    SIM_THRESHOLD = 0.60
    best_text: str | None = None
    best_conf = 0.0

    if n >= 3 and all(s >= SIM_THRESHOLD for s in sim_matrix.values()):
        best_r = max(readings, key=lambda r: len(r["corrected"]))
        best_text = best_r["corrected"]
        best_conf = sum(r["norm_weight"] * r["sensor_conf"] * r["ocr_conf"] for r in readings)

    if best_text is None and n >= 2:
        best_pair_sim = 0.0
        best_pair: tuple[int, int] | None = None
        for (i, j), sim in sim_matrix.items():
            if sim >= SIM_THRESHOLD and sim > best_pair_sim:
                best_pair_sim = sim
                best_pair = (i, j)

        if best_pair is not None:
            i, j = best_pair
            pair = [readings[i], readings[j]]
            best_r = max(pair, key=lambda r: len(r["corrected"]))
            best_text = best_r["corrected"]
            # Confidenza limitata esclusivamente al contributo del cluster concordante
            best_conf = sum(r["norm_weight"] * r["sensor_conf"] * r["ocr_conf"] for r in pair)

    if best_text is None:
        best_r = max(readings, key=lambda r: r["norm_weight"] * r["sensor_conf"] * r["ocr_conf"])
        best_text = best_r["corrected"]
        best_conf = best_r["sensor_conf"] * best_r["ocr_conf"] * best_r["norm_weight"]

    return best_text, round(min(best_conf, 1.0), 3), raw_dict

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json, pathlib

    path = pathlib.Path(__file__).resolve().parent.parent / "VShuttle-input.json"
    scenarios = json.loads(path.read_text(encoding="utf-8"))
    for sc in scenarios[:10]:
        fused, conf, _ = fuse_sensors(sc["sensori"])
        print(f"  ID {sc['id_scenario']:3d}: {fused:50s} conf={conf:.3f}")

"""V-Shuttle Live Dashboard — Streamlit app for real-time scenario simulation."""
from __future__ import annotations

import json
import time
import pathlib
import sys

import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine import process_scenario

# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="V-Shuttle Dashboard",
    page_icon="🚐",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .action-go {
        background: #1b5e20; color: white; padding: 30px; border-radius: 16px;
        text-align: center; font-size: 48px; font-weight: bold;
        margin: 8px 0; animation: pulse-green 1.5s infinite;
    }
    .action-stop {
        background: #b71c1c; color: white; padding: 30px; border-radius: 16px;
        text-align: center; font-size: 48px; font-weight: bold;
        margin: 8px 0; animation: pulse-red 1.5s infinite;
    }
    .action-ask {
        background: #e65100; color: white; padding: 30px; border-radius: 16px;
        text-align: center; font-size: 48px; font-weight: bold;
        margin: 8px 0; animation: pulse-orange 1.5s infinite;
    }
    @keyframes pulse-green {
        0%, 100% { box-shadow: 0 0 10px #1b5e20; }
        50% { box-shadow: 0 0 30px #4caf50; }
    }
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 10px #b71c1c; }
        50% { box-shadow: 0 0 30px #f44336; }
    }
    @keyframes pulse-orange {
        0%, 100% { box-shadow: 0 0 10px #e65100; }
        50% { box-shadow: 0 0 30px #ff9800; }
    }
    .sensor-card {
        background: #263238; color: #eceff1; padding: 12px 16px;
        border-radius: 10px; margin: 4px 0; font-size: 14px;
    }
    .confidence-bar {
        height: 10px; border-radius: 5px; margin-top: 4px;
    }
    .big-button button {
        font-size: 24px !important; padding: 14px 32px !important;
        border-radius: 12px !important; font-weight: bold !important;
    }
    .stats-card {
        background: #37474f; color: white; padding: 16px;
        border-radius: 12px; text-align: center;
    }
    .countdown {
        font-size: 60px; font-weight: bold; color: #ff9800; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ── State init ───────────────────────────────────────────────────────────
if "scenarios" not in st.session_state:
    st.session_state.scenarios = []
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "running" not in st.session_state:
    st.session_state.running = False
if "results" not in st.session_state:
    st.session_state.results = []
if "human_responses" not in st.session_state:
    st.session_state.human_responses = {}
if "ask_human_time" not in st.session_state:
    st.session_state.ask_human_time = None
if "paused_for_human" not in st.session_state:
    st.session_state.paused_for_human = False
if "auto_advance_time" not in st.session_state:
    st.session_state.auto_advance_time = None
if "speed" not in st.session_state:
    st.session_state.speed = 4

# ── Load default data ────────────────────────────────────────────────────
def load_default():
    path = ROOT / "VShuttle-input.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []

# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🚐 V-Shuttle Control")
    st.markdown("---")

    uploaded = st.file_uploader("📂 Carica JSON scenari", type=["json"])
    if uploaded:
        st.session_state.scenarios = json.loads(uploaded.read())
        st.session_state.idx = 0
        st.session_state.results = []
        st.session_state.running = False
        st.success(f"Caricati {len(st.session_state.scenarios)} scenari")
    elif not st.session_state.scenarios:
        st.session_state.scenarios = load_default()
        if st.session_state.scenarios:
            st.info(f"Dataset predefinito: {len(st.session_state.scenarios)} scenari")

    st.markdown("---")
    st.session_state.speed = st.slider(
        "⏱️ Velocità (sec/scenario)", 1, 10, st.session_state.speed
    )

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ START", use_container_width=True, type="primary"):
            st.session_state.running = True
            st.session_state.paused_for_human = False
            st.session_state.auto_advance_time = time.time()
    with col2:
        if st.button("⏸️ STOP", use_container_width=True):
            st.session_state.running = False

    if st.button("🔄 RESET", use_container_width=True):
        st.session_state.idx = 0
        st.session_state.results = []
        st.session_state.running = False
        st.session_state.paused_for_human = False
        st.session_state.human_responses = {}

    st.markdown("---")
    # Stats
    total = len(st.session_state.scenarios)
    done = len(st.session_state.results)
    n_go = sum(1 for r in st.session_state.results if r["action"] == "GO")
    n_stop = sum(1 for r in st.session_state.results if r["action"] == "STOP")
    n_ask = sum(1 for r in st.session_state.results if r["action"] == "ASK_HUMAN")

    st.metric("Scenari", f"{done}/{total}")
    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 GO", n_go)
    c2.metric("🔴 STOP", n_stop)
    c3.metric("🟠 ASK", n_ask)

    if done > 0:
        avg_conf = sum(r["confidence"] for r in st.session_state.results) / done
        st.metric("Confidenza media", f"{avg_conf:.1%}")

# ── Process current scenario ─────────────────────────────────────────────
scenarios = st.session_state.scenarios
idx = st.session_state.idx

if not scenarios:
    st.warning("Nessuno scenario caricato. Usa la sidebar per caricare un file JSON.")
    st.stop()

# Auto-advance logic
if (
    st.session_state.running
    and not st.session_state.paused_for_human
    and idx < len(scenarios)
):
    now = time.time()
    if st.session_state.auto_advance_time is None:
        st.session_state.auto_advance_time = now

    elapsed = now - st.session_state.auto_advance_time
    if elapsed >= st.session_state.speed:
        # Process current scenario
        scenario = scenarios[idx]
        result = process_scenario(scenario)

        if result["action"] == "ASK_HUMAN" and scenario["id_scenario"] not in st.session_state.human_responses:
            st.session_state.paused_for_human = True
            st.session_state.ask_human_time = time.time()
        else:
            if scenario["id_scenario"] in st.session_state.human_responses:
                result["action"] = st.session_state.human_responses[scenario["id_scenario"]]
                result["reason"] += " [OPERATORE]"
            st.session_state.results.append(result)
            st.session_state.idx += 1
            st.session_state.auto_advance_time = time.time()
        st.rerun()

# ── Main display ─────────────────────────────────────────────────────────
if idx >= len(scenarios):
    st.title("✅ Simulazione completata!")
    st.balloons()

    # Summary table
    st.subheader("Riepilogo")
    import pandas as pd
    df = pd.DataFrame(st.session_state.results)
    df = df[["id_scenario", "action", "confidence", "fused_text", "sign_type", "reason"]]
    st.dataframe(df, use_container_width=True, height=600)

    # Export
    json_str = json.dumps(st.session_state.results, ensure_ascii=False, indent=2)
    st.download_button(
        "📥 Scarica risultati JSON",
        json_str,
        "vshuttle_results.json",
        "application/json",
    )
    st.stop()

# Current scenario data
scenario = scenarios[idx]
sid = scenario["id_scenario"]
sensori = scenario["sensori"]
orario = scenario["orario_rilevamento"]
giorno = scenario["giorno_settimana"]

# Process for display
result = process_scenario(scenario)
action = result["action"]
confidence = result["confidence"]

# ── Header ───────────────────────────────────────────────────────────────
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title(f"🚐 V-Shuttle — Scenario #{sid}")
with header_col2:
    st.markdown(f"### 🕐 {orario} — {giorno}")
    progress = (idx + 1) / len(scenarios)
    st.progress(progress, text=f"Scenario {idx + 1}/{len(scenarios)}")

st.markdown("---")

# ── Action display ───────────────────────────────────────────────────────
act_col, detail_col = st.columns([1, 2])

with act_col:
    css_class = {"GO": "action-go", "STOP": "action-stop", "ASK_HUMAN": "action-ask"}[action]
    emoji = {"GO": "✅", "STOP": "🛑", "ASK_HUMAN": "⚠️"}[action]
    label = {"GO": "GO", "STOP": "STOP", "ASK_HUMAN": "ASK HUMAN"}[action]
    st.markdown(f'<div class="{css_class}">{emoji} {label}</div>', unsafe_allow_html=True)

    # Confidence gauge
    conf_color = "#4caf50" if confidence > 0.7 else "#ff9800" if confidence > 0.4 else "#f44336"
    st.markdown(
        f'<div style="margin-top:12px;"><b>Confidenza: {confidence:.1%}</b>'
        f'<div class="confidence-bar" style="background:#444;">'
        f'<div style="width:{confidence*100:.0f}%;background:{conf_color};'
        f'height:10px;border-radius:5px;"></div></div></div>',
        unsafe_allow_html=True,
    )

    # ASK_HUMAN interaction
    if action == "ASK_HUMAN" and st.session_state.paused_for_human:
        st.markdown("---")
        st.warning("⏳ In attesa dell'operatore...")

        remaining = max(0, 2.0 - (time.time() - (st.session_state.ask_human_time or time.time())))
        st.markdown(f'<div class="countdown">{remaining:.1f}s</div>', unsafe_allow_html=True)

        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("🟢 CONSENTI (GO)", use_container_width=True, type="primary"):
                st.session_state.human_responses[sid] = "GO"
                result["action"] = "GO"
                result["reason"] += " [OPERATORE: GO]"
                st.session_state.results.append(result)
                st.session_state.idx += 1
                st.session_state.paused_for_human = False
                st.session_state.auto_advance_time = time.time()
                st.rerun()
        with bc2:
            if st.button("🔴 FERMA (STOP)", use_container_width=True):
                st.session_state.human_responses[sid] = "STOP"
                result["action"] = "STOP"
                result["reason"] += " [OPERATORE: STOP]"
                st.session_state.results.append(result)
                st.session_state.idx += 1
                st.session_state.paused_for_human = False
                st.session_state.auto_advance_time = time.time()
                st.rerun()

        # Auto-timeout → STOP after 2 seconds
        if remaining <= 0:
            st.session_state.human_responses[sid] = "STOP"
            result["action"] = "STOP"
            result["reason"] += " [TIMEOUT → STOP]"
            st.session_state.results.append(result)
            st.session_state.idx += 1
            st.session_state.paused_for_human = False
            st.session_state.auto_advance_time = time.time()
            st.rerun()

with detail_col:
    st.subheader("📋 Analisi cartello")
    st.markdown(f"**Testo fuso:** `{result['fused_text']}`")
    st.markdown(f"**Tipo segnale:** `{result['sign_type']}`")
    if result.get("exceptions"):
        st.markdown(f"**Eccezioni:** {', '.join(result['exceptions'])}")
    st.info(f"💡 {result['reason']}")

    # Sensor details
    st.subheader("📡 Dati sensori")
    s1, s2, s3 = st.columns(3)
    sensor_map = {
        "camera_frontale": ("📷 Camera Frontale", s1),
        "camera_laterale": ("📷 Camera Laterale", s2),
        "V2I_receiver": ("📡 V2I Receiver", s3),
    }
    for key, (label, col) in sensor_map.items():
        with col:
            sensor = sensori.get(key, {})
            txt = sensor.get("testo") or "—"
            conf = sensor.get("confidenza")
            conf_str = f"{conf:.0%}" if conf is not None else "N/A"
            conf_val = conf if conf is not None else 0
            bar_color = "#4caf50" if conf_val > 0.7 else "#ff9800" if conf_val > 0.4 else "#f44336"
            st.markdown(
                f'<div class="sensor-card">'
                f'<b>{label}</b><br>'
                f'📝 {txt}<br>'
                f'🎯 {conf_str}'
                f'<div class="confidence-bar" style="background:#555;">'
                f'<div style="width:{conf_val*100:.0f}%;background:{bar_color};'
                f'height:10px;border-radius:5px;"></div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── Recent results ───────────────────────────────────────────────────────
if st.session_state.results:
    st.markdown("---")
    st.subheader("📊 Ultimi risultati")
    recent = st.session_state.results[-10:][::-1]
    cols = st.columns(len(recent))
    for i, r in enumerate(recent):
        with cols[i]:
            color = {"GO": "🟢", "STOP": "🔴", "ASK_HUMAN": "🟠"}[r["action"]]
            st.markdown(
                f"**#{r['id_scenario']}**  \n"
                f"{color} {r['action']}  \n"
                f"_{r['confidence']:.0%}_"
            )

# ── Auto-refresh for running simulation ──────────────────────────────────
if st.session_state.running and not st.session_state.paused_for_human:
    time.sleep(0.5)
    st.rerun()
elif st.session_state.paused_for_human:
    time.sleep(0.3)
    st.rerun()

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from typing import Dict, Any

from aegisrisk.core.models import TradeTicket, MarketState, Side, OrderType, TimeInForce
from aegisrisk.engine.bridge import PrologBridge
from aegisrisk.engine.fuzzifier import fuzzify
from aegisrisk.simulator.generator import generate_snapshot, _SYMBOLS

# Set up the streamlit page (must be first command)
st.set_page_config(
    page_title="AEGIS: CORE SURVEILLANCE",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cool hacker CSS I found / tweaked
st.markdown("""
<style>
    /* Import Premium Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* Varsity Theme Colors */
    :root {
        --terminal-bg: #090b0f;
        --panel-bg: rgba(18, 22, 31, 0.65);
        --panel-border: rgba(45, 55, 72, 0.4);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-accent: #38bdf8;
        --neon-green: #10b981;
        --neon-red: #ef4444;
        --neon-yellow: #f59e0b;
        --glow-green: rgba(16, 185, 129, 0.15);
        --glow-red: rgba(239, 68, 68, 0.15);
    }
    
    /* Document Overrides */
    .stApp {
        background-color: var(--terminal-bg);
        background-image: radial-gradient(circle at 50% 0%, rgba(30, 41, 59, 0.4) 0%, transparent 70%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Default Streamlit Chrome */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1600px;
    }

    /* Top Nav */
    .nav-ribbon {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--panel-border);
        margin-bottom: 2rem;
        border-radius: 8px;
    }
    .nav-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .nav-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: var(--neon-green);
        box-shadow: 0 0 10px var(--neon-green);
        animation: pulse 2s infinite;
    }
    .nav-stats {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: var(--text-secondary);
        display: flex;
        gap: 2rem;
    }

    /* Panels */
    .glass-panel {
        background: var(--panel-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--panel-border);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem;
    }
    .glass-panel h3, .stMarkdown h3 {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-accent);
        border-bottom: 1px solid var(--panel-border);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        margin-top: 0;
    }

    /* High-Density Grid (Data Readout) */
    .data-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
    }
    .data-item {
        display: flex;
        flex-direction: column;
    }
    .data-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        color: var(--text-secondary);
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .data-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    .data-value.up { color: var(--neon-green); }
    .data-value.down { color: var(--neon-red); }

    /* The big status box */
    .intercept-core {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 3rem 1rem;
        border-radius: 12px;
        border: 1px solid var(--panel-border);
        background: radial-gradient(circle at 50% 50%, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
    }
    .intercept-approved {
        border-color: rgba(16, 185, 129, 0.4);
        box-shadow: inset 0 0 40px var(--glow-green);
    }
    .intercept-rejected {
        border-color: rgba(239, 68, 68, 0.4);
        box-shadow: inset 0 0 40px var(--glow-red);
    }
    .intercept-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px currentColor; /* Softer glow */
    }
    .status-approve { color: var(--neon-green); }
    .status-reject { color: var(--neon-red); }
    .intercept-reason {
        font-family: 'Inter', sans-serif;
        font-size: 1.15rem;
        font-weight: 400;
        color: var(--text-primary);
        max-width: 80%;
        background: rgba(0,0,0,0.4);
        padding: 1rem 2rem;
        border-radius: 8px;
        border: 1px dashed var(--panel-border);
    }

    /* Fuzzifier tags */
    .atom-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 0.5rem;
    }
    .atom-tag {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 1rem;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid var(--panel-border);
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-primary);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .atom-tag span {
        margin-right: 0.5rem;
        color: var(--text-secondary);
    }
    
    /* Coloring the semantic states */
    .atom-safe { border-left: 3px solid var(--neon-green); }
    .atom-warn { border-left: 3px solid var(--neon-yellow); }
    .atom-danger { border-left: 3px solid var(--neon-red); }
    .atom-info { border-left: 3px solid var(--text-accent); }

    /* Form Styling via Streamlit CSS wrappers */
    [data-testid="stForm"] {
        background: var(--panel-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--panel-border);
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    /* Audit Table Rendering */
    .audit-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        text-align: left;
    }
    .audit-table th {
        color: var(--text-secondary);
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        text-transform: uppercase;
        border-bottom: 1px solid var(--panel-border);
        padding: 0.75rem 0.5rem;
    }
    .audit-table td {
        padding: 0.75rem 0.5rem;
        border-bottom: 1px solid rgba(45, 55, 72, 0.2);
        color: var(--text-primary);
    }
    .audit-table tr:hover td {
        background: rgba(255, 255, 255, 0.02);
    }
    .stat-approve {
        color: var(--neon-green);
        font-weight: 700;
        background-color: rgba(16, 185, 129, 0.1);
    }
    .stat-reject {
        color: var(--neon-red);
        font-weight: 700;
        background-color: rgba(239, 68, 68, 0.1);
    }

    /* Animations */
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    .flash-update {
        animation: flashBg 0.5s ease-out;
    }
    @keyframes flashBg {
        0% { background: rgba(255, 255, 255, 0.1); }
        100% { background: transparent; }
    }

    /* Streamlit specific overrides */
    div[data-baseweb="input"], div[data-baseweb="select"] { 
        background-color: rgba(0,0,0,0.5) !important; 
        border-color: var(--panel-border) !important; 
    }
    /* Buttons (spent way too long on this gradient/hover) */
    .stButton>button {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(56, 189, 248, 0.5) !important;
        color: var(--text-accent) !important;
        font-family: 'JetBrains Mono', monospace !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    }
    .stButton>button:hover {
        background: rgba(56, 189, 248, 0.15) !important;
        border-color: var(--text-accent) !important;
        color: #fff !important;
    }
    .stButton>button:active {
        background: rgba(56, 189, 248, 0.25) !important;
    }
</style>
""", unsafe_allow_html=True)

# init engine and session state
if "engine" not in st.session_state:
    st.session_state.engine = PrologBridge()
if "sim_running" not in st.session_state:
    st.session_state.sim_running = False
if "sim_counter" not in st.session_state:
    st.session_state.sim_counter = 1
if "history" not in st.session_state:
    st.session_state.history = []

# ui helpers
def get_atom_class(level_str: str) -> str:
    level = level_str.lower()
    if level in ["low", "normal", "tight", "positive", "neutral"]: return "atom-safe"
    if level in ["medium", "elevated"]: return "atom-warn"
    if level in ["high", "extreme", "wide", "critical", "negative"]: return "atom-danger"
    return "atom-info"

def render_top_nav():
    current_time = datetime.now().strftime("%H:%M:%S UTC")
    init_status = "ONLINE" if st.session_state.engine._initialized else "OFFLINE"
    status_color = "var(--neon-green)" if st.session_state.engine._initialized else "var(--neon-red)"
    
    st.markdown(f"""
    <div class="nav-ribbon">
        <div class="nav-title">
            <div class="nav-indicator" style="background-color: {status_color}; box-shadow: 0 0 10px {status_color};"></div>
            AEGISRISK // CORE SURVEILLANCE
        </div>
        <div class="nav-stats">
            <div><strong>TIME:</strong> {current_time}</div>
            <div><strong>KB STATUS:</strong> <span style="color: {status_color}">{init_status}</span></div>
            <div><strong>ACTIVE RULES:</strong> 25</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_top_nav()

live_tab, manual_tab = st.tabs(["[ LIVE SURVEILLANCE ]", "[ MANUAL ORDER TERMINAL ]"])

# tab 1: surveillance mode
with live_tab:
    
    # control buttons
    approve_col, reject_col, clear_col, _ = st.columns([2.5, 2.5, 2, 5])
    with approve_col:
        if st.button("GENERATE APPROVED TRADE", use_container_width=True):
            st.session_state.sim_running = True
            st.session_state.force_status = "approve"
    with reject_col:
        if st.button("GENERATE REJECTED TRADE", use_container_width=True):
            st.session_state.sim_running = True
            st.session_state.force_status = "reject"
    with clear_col:
        if st.button("PURGE AUDIT LOG", use_container_width=True):
            st.session_state.history = []
            st.session_state.sim_running = False
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state.sim_running:
        # continuously generate trades until we hit the requested outcome (with safety limit)
        max_attempts = 100
        target_status = st.session_state.get("force_status")
        
        for _ in range(max_attempts):
            snapshot = generate_snapshot(st.session_state.sim_counter)
            st.session_state.sim_counter += 1
            
            # Fuzzify
            fuzzy = fuzzify(snapshot.ticket, snapshot.market, snapshot.session)
            
            # Evaluate via Prolog
            start_time = time.perf_counter()
            decision = st.session_state.engine.evaluate(
                snapshot.ticket,
                snapshot.market,
                fuzzy.as_dict(),
                account_tier=snapshot.account_tier,
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            if not target_status or decision.status == target_status:
                break
        
        # Log to audit history
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        st.session_state.history.insert(0, {
            "TS": current_time,
            "TID": f"{snapshot.ticket.ticket_id:06d}",
            "SYM": snapshot.ticket.symbol.upper(),
            "DIR": snapshot.ticket.side.value.upper(),
            "SZ": f"{snapshot.ticket.lots:.2f}",
            "PX": f"{snapshot.ticket.price:.5f}",
            "STAT": decision.status.upper(),
            "RSN": decision.reason,
            "LAT": f"{latency_ms:.2f}ms"
        })
        if len(st.session_state.history) > 15:
            st.session_state.history.pop()

        left_panel, right_panel = st.columns([1, 1.2])
        
        # left side: intercept core & atoms
        with left_panel:
            box_class = "intercept-approved" if decision.status == "approve" else "intercept-rejected"
            txt_class = "status-approve" if decision.status == "approve" else "status-reject"
            lbl = "EXECUTION CLEARED" if decision.status == "approve" else "INTERCEPT DETECTED"
            
            # Sub-panel for Semantic Atoms
            atoms_html = f"""
            <div class="glass-panel" style="padding: 0;">
                <div class="intercept-core {box_class} flash-update">
                    <div style="font-family: 'Inter'; font-size: 1rem; color: var(--text-secondary); margin-bottom: 0.5rem; letter-spacing: 0.2em;">PRE-TRADE RULE RESOLUTION</div>
                    <div class="intercept-status {txt_class}">{lbl}</div>
                    <div class="intercept-reason">{decision.reason}</div>
                    <div style="margin-top: 1rem; font-family: 'JetBrains Mono'; font-size: 0.9rem; color: var(--text-secondary);">INFERENCE LATENCY: {latency_ms:.3f} ms</div>
                </div>
            </div>
            
            <div class="glass-panel flash-update">
                <h3>Semantic Memory Assertion (Prolog Atoms)</h3>
                <div class="atom-container">
            """
            for k, v in fuzzy.as_dict().items():
                cls = get_atom_class(v)
                key_fmt = k.replace("_level", "").upper()
                atoms_html += f'<div class="atom-tag {cls}"><span>{key_fmt}</span>{v.upper()}</div>'
            atoms_html += "</div></div>"
            st.markdown(atoms_html, unsafe_allow_html=True)

        # right side: raw payload
        with right_panel:
            side_color = "up" if snapshot.ticket.side.value.lower() == "buy" else "down"
            
            # Ticket Data
            tk_html = f"""
            <div class="glass-panel flash-update">
                <h3>Trade Ticket Payload</h3>
                <div class="data-grid">
                    <div class="data-item"><span class="data-label">Ticket ID</span><span class="data-value">{snapshot.ticket.ticket_id}</span></div>
                    <div class="data-item"><span class="data-label">Symbol</span><span class="data-value" style="color: var(--text-accent);">{snapshot.ticket.symbol.upper()}</span></div>
                    <div class="data-item"><span class="data-label">Direction</span><span class="data-value {side_color}">{snapshot.ticket.side.value.upper()}</span></div>
                    <div class="data-item"><span class="data-label">Size (Lots)</span><span class="data-value">{snapshot.ticket.lots:.2f}</span></div>
                    <div class="data-item"><span class="data-label">Price</span><span class="data-value">{snapshot.ticket.price:.5f}</span></div>
                    <div class="data-item"><span class="data-label">Leverage</span><span class="data-value">{snapshot.ticket.leverage}x</span></div>
                    <div class="data-item"><span class="data-label">Type</span><span class="data-value">{snapshot.ticket.order_type.value.upper()}</span></div>
                    <div class="data-item"><span class="data-label">Account Tier</span><span class="data-value" style="font-size: 0.9rem;">{snapshot.account_tier.replace('_', ' ').upper()}</span></div>
                </div>
            </div>
            """
            st.markdown(tk_html, unsafe_allow_html=True)
            
            # Market Data
            mk_html = f"""
            <div class="glass-panel flash-update">
                <h3>Environmental Market Snapshot</h3>
                <div class="data-grid">
                    <div class="data-item"><span class="data-label">BID px</span><span class="data-value down">{snapshot.market.bid:.5f}</span></div>
                    <div class="data-item"><span class="data-label">ASK px</span><span class="data-value up">{snapshot.market.ask:.5f}</span></div>
                    <div class="data-item"><span class="data-label">Spread</span><span class="data-value">{(snapshot.market.ask - snapshot.market.bid):.5f}</span></div>
                    <div class="data-item"><span class="data-label">Vol (Ann.)</span><span class="data-value">{snapshot.market.volatility:.2f}%</span></div>
                    <div class="data-item"><span class="data-label">Acct Bal</span><span class="data-value">${snapshot.market.account_balance:,.2f}</span></div>
                    <div class="data-item"><span class="data-label">Existing Exp</span><span class="data-value">${snapshot.market.open_exposure:,.2f}</span></div>
                    <div class="data-item"><span class="data-label">Sent Index</span><span class="data-value">{snapshot.market.news_sentiment:.2f}</span></div>
                </div>
            </div>
            """
            st.markdown(mk_html, unsafe_allow_html=True)
            
        # bottom log
        if st.session_state.history:
            table_html = (
                '<div class="glass-panel" style="padding: 1.5rem; overflow-x: auto;">'
                '<h3 style="margin-bottom: 1rem;">Real-Time Audit Log (Prolog Output)</h3>'
                '<table class="audit-table">'
                '<thead>'
                '<tr>'
                '<th>TS</th><th>TID</th><th>SYM</th><th>DIR</th><th>SZ</th><th>PX</th><th>STAT</th><th>RSN</th><th>LAT</th>'
                '</tr>'
                '</thead>'
                '<tbody>'
            )
            for row in st.session_state.history:
                stat_class = "stat-approve" if row["STAT"] == "APPROVE" else "stat-reject"
                table_html += (
                    '<tr>'
                    f'<td style="color: var(--text-secondary);">{row["TS"]}</td>'
                    f'<td>{row["TID"]}</td>'
                    f'<td style="color: var(--text-accent);">{row["SYM"]}</td>'
                    f'<td>{row["DIR"]}</td>'
                    f'<td>{row["SZ"]}</td>'
                    f'<td>{row["PX"]}</td>'
                    f'<td class="{stat_class}">{row["STAT"]}</td>'
                    f'<td style="font-family: \'Inter\', sans-serif; font-size: 0.8rem; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{row["RSN"]}">{row["RSN"]}</td>'
                    f'<td style="color: var(--text-secondary);">{row["LAT"]}</td>'
                    '</tr>'
                )
            table_html += "</tbody></table></div>"
            st.html(table_html)
    else:
        st.info("System idle. Engage simulation to begin pre-trade evaluation flow.")

# tab 2: manual terminal
with manual_tab:
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <h3 style="color: var(--text-primary); margin-bottom: 0;"><span style="color: var(--text-accent);">///</span> DIRECT MARKET ACCESS (TESTING MODULE)</h3>
        <p style="color: var(--text-secondary); font-size: 0.9rem;">
        Construct an explicit Trade Ticket and Market State to probe specific regulatory bounds within the deductive Knowledge Base.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("institutional_manual_entry"):
        form_col1, form_col2 = st.columns(2)
        
        with form_col1:
            st.markdown('<h3 style="color: var(--text-accent); border-bottom: 1px solid var(--panel-border); padding-bottom: 0.5rem; margin-bottom: 1rem;">ORDER DEFINITION</h3>', unsafe_allow_html=True)
            symbol = st.selectbox("INSTRUMENT", _SYMBOLS + ("xagusd", "btc_fake", "undefined_asset"))
            
            rad1, rad2 = st.columns(2)
            side_str = rad1.radio("DIRECTION", ["buy", "sell"], horizontal=True)
            order_type_str = rad2.radio("EXEC TYPE", ["market", "limit"], horizontal=True)
            
            lots = st.number_input("SIZE (LOTS)", min_value=0.01, value=1.0, step=0.1)
            price = st.number_input("EXECUTION PRICE", min_value=0.00001, value=1.10000, format="%.5f")
            leverage = st.number_input("REQUESTED LEVERAGE", min_value=1.0, value=30.0, step=5.0)
            tif_str = st.selectbox("TIME IN FORCE", ["day", "gtc", "ioc", "fok"])
            
            account_tier = st.selectbox("AUTHORITY TIER", [
                "retail_standard", "retail_pro", "prop_funded_eval_1", "prop_funded_pro"
            ])

        with form_col2:
            st.markdown('<h3 style="color: var(--text-accent); border-bottom: 1px solid var(--panel-border); padding-bottom: 0.5rem; margin-bottom: 1rem;">ENVIRONMENTAL OVERRIDE</h3>', unsafe_allow_html=True)
            balance = st.number_input("ACCOUNT EQUITY ($)", min_value=0.0, value=10000.0, step=1000.0)
            exposure = st.number_input("GROSS OPEN EXPOSURE ($)", min_value=0.0, value=0.0, step=1000.0)
            
            mid = price
            spread_pips = st.number_input("SYNTHETIC SPREAD (PIPS)", min_value=0.0, value=2.0)
            bid = mid - (spread_pips * 0.0001) / 2
            ask = mid + (spread_pips * 0.0001) / 2
            
            volatility = st.slider("SYNTHETIC VOLATILITY (ANN. %)", 0.0, 150.0, 15.0)
            sentiment = st.slider("NEWS SENTIMENT INDEX", -1.0, 1.0, 0.0, step=0.1)
            session = st.selectbox("LIQUIDITY SESSION", ["asia", "europe", "us", "rollover"], index=2)
            
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("SYSTEM: EVALUATE COMPLIANCE RULES", use_container_width=True)
        
        if submitted:
            ticket = TradeTicket(
                ticket_id=9999, account_id="MANUAL", symbol=symbol, side=Side(side_str),
                lots=lots, price=price, order_type=OrderType(order_type_str),
                leverage=leverage, time_in_force=TimeInForce(tif_str)
            )
            market = MarketState(
                symbol=symbol, bid=bid, ask=ask, volatility=volatility,
                account_balance=balance, open_exposure=exposure, news_sentiment=sentiment
            )
            fuzzy = fuzzify(ticket, market, session)
            
            start_time = time.perf_counter()
            decision = st.session_state.engine.evaluate(
                ticket, market, fuzzy.as_dict(), account_tier=account_tier,
            )
            # just need a quick latency metric
            lat = (time.perf_counter() - start_time) * 1000
            
            st.markdown('<hr style="border-color: var(--panel-border);">', unsafe_allow_html=True)
            st.markdown('### TERMINAL: EVALUATION TRACE')
            
            box_class = "intercept-approved" if decision.status == "approve" else "intercept-rejected"
            txt_class = "status-approve" if decision.status == "approve" else "status-reject"
            lbl = "EXECUTION CLEARED" if decision.status == "approve" else "INTERCEPT DETECTED"
            
            manual_out = f"""
            <div class="intercept-core {box_class} flash-update" style="margin-bottom: 2rem;">
                <div style="font-family: 'Inter'; font-size: 1rem; color: var(--text-secondary); margin-bottom: 0.5rem; letter-spacing: 0.2em;">MANUAL INJECTION RESULT</div>
                <div class="intercept-status {txt_class}">{lbl}</div>
                <div class="intercept-reason">{decision.reason}</div>
            </div>
            
            <div class="glass-panel">
                <h3>ATOMIZED MEMORY FOOTPRINT</h3>
                <div class="atom-container">
            """
            for k, v in fuzzy.as_dict().items():
                cls = get_atom_class(v)
                key_fmt = k.replace("_level", "").upper()
                manual_out += f'<div class="atom-tag {cls}"><span>{key_fmt}</span>{v.upper()}</div>'
            manual_out += "</div></div>"
            st.markdown(manual_out, unsafe_allow_html=True)

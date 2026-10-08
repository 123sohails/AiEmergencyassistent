import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import threading
import uuid
import time
import json
import os
from pathlib import Path

# Load .env file explicitly before importing worker modules
env_path = Path('.env')
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from store import insert_reports, get_all_incidents, get_incident_reports, get_incident_events, get_matching_decision, reset_session, get_pending_reports
from worker import run_worker_loop

# --- PAGE CONFIG ---
st.set_page_config(page_title="NDRF Urban Incident Response", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS (PREMIUM DARK MODE AESTHETIC) ---
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background-color: #050b14;
        color: #e0e6ed;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Chrome */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Top Pipeline Bar */
    .pipeline-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(16, 32, 56, 0.7);
        border: 1px solid #1a365d;
        border-radius: 12px;
        padding: 15px 30px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    .pipeline-step {
        display: flex;
        align-items: center;
        gap: 10px;
        opacity: 0.5;
        transition: opacity 0.3s ease;
    }
    .pipeline-step.active {
        opacity: 1;
    }
    .step-num {
        background: transparent;
        border: 1px solid #00f0ff;
        color: #00f0ff;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: bold;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
    }
    .step-text {
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 1px;
    }
    .step-sub {
        font-size: 0.7rem;
        color: #718096;
        display: block;
    }
    .pipeline-arrow {
        color: #2d3748;
        font-size: 1.2rem;
    }

    /* Cards and Containers */
    div[data-testid="stVerticalBlock"] > div {
        background: rgba(16, 32, 56, 0.4);
        border: 1px solid #1a365d;
        border-radius: 10px;
        padding: 15px;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        color: #00f0ff;
        font-size: 1.8rem;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        color: #a0aec0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: rgba(0, 240, 255, 0.05);
        color: #00f0ff !important;
        border: 1px solid #1a365d;
        border-radius: 5px;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00f0ff 0%, #0077ff 100%);
        color: #050b14;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        width: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 240, 255, 0.4);
        color: white;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #08111e;
        border-right: 1px solid #1a365d;
    }
    
    /* Badges */
    .badge-high { background: rgba(255, 50, 50, 0.2); color: #ff4444; padding: 2px 8px; border-radius: 4px; border: 1px solid #ff4444; font-size: 0.75rem;}
    .badge-medium { background: rgba(255, 170, 0, 0.2); color: #ffaa00; padding: 2px 8px; border-radius: 4px; border: 1px solid #ffaa00; font-size: 0.75rem;}
    .badge-live { background: rgba(0, 255, 100, 0.2); color: #00ff64; padding: 2px 8px; border-radius: 4px; border: 1px solid #00ff64; font-size: 0.75rem; display: inline-block; margin-left:10px;}
</style>
""", unsafe_allow_html=True)

# --- BACKGROUND WORKER ---
@st.cache_resource
def start_worker():
    thread = threading.Thread(target=run_worker_loop, kwargs={"delay": 1.0}, daemon=True)
    thread.start()
    return thread

start_worker()

# --- STATE ---
if "active_session" not in st.session_state:
    st.session_state.active_session = "dataset"
if "raw_count" not in st.session_state:
    st.session_state.raw_count = 0
if "current_view" not in st.session_state:
    st.session_state.current_view = "overview"

# --- HEADER: NDRF BRANDING & PIPELINE ---
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
    <div>
        <h2 style="margin:0; color: white; display: inline-block;">NDRF <span style="font-weight:300; font-size:1.2rem; color:#a0aec0;">| Urban Incident Response & Risk Monitoring</span></h2>
    </div>
    <div style="text-align: right; color:#a0aec0; font-size:0.9rem;">
        <div>26 Sep 2025 14:18</div>
        <div>Mumbai, MH <span class="badge-live">● Live Feed</span></div>
    </div>
</div>

<div class="pipeline-bar">
    <div class="pipeline-step active">
        <div class="step-num">1</div>
        <div><span class="step-text">INGEST</span><span class="step-sub">Real-time Feeds</span></div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step active">
        <div class="step-num" style="box-shadow:none;">2</div>
        <div><span class="step-text">FILTER</span><span class="step-sub">Classify & Prioritize</span></div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step active">
        <div class="step-num" style="box-shadow:none;">3</div>
        <div><span class="step-text">EXTRACT</span><span class="step-sub">Entities & Locations</span></div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step active">
        <div class="step-num" style="box-shadow:none;">4</div>
        <div><span class="step-text">CLUSTER</span><span class="step-sub">Group Similar Events</span></div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step active">
        <div class="step-num" style="box-shadow:none; border-color:#718096; color:#718096;">5</div>
        <div><span class="step-text" style="color:#718096;">DISPATCH</span><span class="step-sub">Teams & Resources</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR: INGESTION ---
st.sidebar.markdown("<h3 style='color:#00f0ff;'>⛑️ Control Panel</h3>", unsafe_allow_html=True)

# Navigation
st.sidebar.markdown("<div style='margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #1a365d;'>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='color:#718096; font-size: 0.75rem; font-weight: bold; margin-bottom: 10px; letter-spacing: 1px;'>NAVIGATION</div>", unsafe_allow_html=True)
view_choice = st.sidebar.radio(
    "View",
    ["Overview", "Incidents", "Map", "Analytics", "Reports"],
    label_visibility="collapsed",
    key="nav_radio"
)
st.session_state.current_view = view_choice.lower()
st.sidebar.markdown("</div>", unsafe_allow_html=True)

session_choice = st.sidebar.radio("Session Engine", ["dataset", "live"], index=0)
st.session_state.active_session = session_choice

uploaded_files = st.sidebar.file_uploader(
    "Upload Intel (CSV/JSON/Audio)", 
    accept_multiple_files=True
)

if st.sidebar.button("Queue Dataset 🚀", type="primary"):
    import tempfile
    import os
    from pathlib import Path
    from adapters import load_any, sort_records, unique_text_groups
    from audio import process_audio
    
    if uploaded_files:
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_records = []
            for uf in uploaded_files:
                path = Path(tmpdir) / uf.name
                path.write_bytes(uf.getvalue())
                
                if path.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg", ".flac"}:
                    transcript = process_audio(str(path))
                    audio_records.append({
                        "id": f"AUDIO-{uuid.uuid4().hex[:6]}",
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "Call (Audio)",
                        "sender": "Unknown",
                        "text": transcript,
                        "stage": 1,
                        "session_id": session_choice,
                        "origin": "audio"
                    })
            
            raw_recs = sort_records(load_any(tmpdir))
            st.session_state.raw_count += (len(raw_recs) + len(audio_records))
            
            groups = unique_text_groups(raw_recs)
            records_to_process = []
            for text, rec_ids in groups.items():
                first_rec = next(r for r in raw_recs if r["id"] == rec_ids[0])
                first_rec['session_id'] = session_choice
                first_rec['origin'] = 'dataset'
                records_to_process.append(first_rec)
                
            records_to_process.extend(audio_records)
            records_to_process = sorted(records_to_process, key=lambda r: r["time"] or "9999")
            
            insert_reports(records_to_process)
            st.sidebar.success(f"Ingested {len(records_to_process)} records.")
            st.rerun()

st.sidebar.markdown("---")
with st.sidebar.expander("Manual Override"):
    new_msg = st.text_area("Intel Text", height=100)
    source = st.selectbox("Channel", ["WhatsApp", "Radio", "Twitter"])
    if st.button("Inject Intel"):
        st.session_state.raw_count += 1
        insert_reports([{
            "id": f"MANUAL-{uuid.uuid4().hex[:6]}",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "sender": "Operator",
            "text": new_msg,
            "stage": 1,
            "session_id": session_choice,
            "origin": "live"
        }])
        st.rerun()

if st.sidebar.button("↻ Refresh Dashboard"):
    st.rerun()

if st.sidebar.button("⚠ Clear Session Memory"):
    reset_session(session_choice)
    st.rerun()

# --- FETCH DATA ---
all_incidents = get_all_incidents(st.session_state.active_session)
pending = get_pending_reports()
inc_count = len(all_incidents)
crit_count = sum(1 for i in all_incidents if i['urgency'] in ['high', 'critical'])
active_incidents = [i for i in all_incidents if i['status'] != 'resolved']

# --- VIEW RENDERER ---
current_view = st.session_state.current_view

def render_map(incidents, height=550):
    """Render the incident map"""
    # Center map on first incident or default location
    if incidents and any(i['lat'] and i['lng'] for i in incidents):
        first_inc = next((i for i in incidents if i['lat'] and i['lng']), None)
        if first_inc:
            center_lat, center_lng = first_inc['lat'], first_inc['lng']
        else:
            center_lat, center_lng = 13.0827, 80.2707  # Chennai
    else:
        center_lat, center_lng = 13.0827, 80.2707  # Chennai

    m = folium.Map(location=[center_lat, center_lng], zoom_start=11, tiles="cartodbdark_matter")

    for inc in incidents:
        if inc['lat'] and inc['lng']:
            if inc['urgency'] in ["critical", "high"]:
                color, icon = "red", "warning-sign"
            elif inc['urgency'] == "medium":
                color, icon = "orange", "info-sign"
            else:
                color, icon = "blue", "info-sign"

            if inc['status'] == "resolved":
                color, icon = "green", "ok-sign"

            # Custom HTML tooltip
            tooltip_html = f"""
            <div style="background:#050b14; color:white; padding:10px; border:1px solid {color}; border-radius:5px; font-family:sans-serif;">
                <b>{inc['location_text'] or 'Unknown'}</b> <span class='badge-{inc['urgency']}'>{inc['urgency'].upper()}</span><br>
                <span style='color:#a0aec0; font-size:0.85rem;'>{inc['resource']}</span>
            </div>
            """

            folium.Marker(
                [inc['lat'], inc['lng']],
                popup=inc['summary'],
                tooltip=folium.Tooltip(tooltip_html),
                icon=folium.Icon(color=color, icon=icon)
            ).add_to(m)

    st_folium(m, width="100%", height=height, returned_objects=[])

def render_incident_panel(incidents):
    """Render the incident console panel"""
    st.markdown("<h4 style='color:white; margin-bottom:15px;'>Incident Console</h4>", unsafe_allow_html=True)
    if not incidents:
        st.info("No active incidents.")
    else:
        tabs = st.tabs(["Details", "Explainability", "Evidence"])

        inc_ids = [inc['id'] for inc in reversed(incidents)]
        selected_id = st.selectbox("Select Target", inc_ids, label_visibility="collapsed")
        inc = next(i for i in incidents if i['id'] == selected_id)

        with tabs[0]:
            st.markdown(f"**ID:** `{inc['id']}`")
            st.markdown(f"**Status:** <span style='color:#00f0ff;'>{inc['status'].upper()}</span>", unsafe_allow_html=True)
            st.markdown(f"**Priority:** <span class='badge-{inc['urgency']}'>{inc['urgency'].upper()}</span>", unsafe_allow_html=True)
            st.markdown(f"**Location:** {inc['location_text'] or 'Unknown'}")
            st.markdown(f"**Coordinates:** {inc['lat']}, {inc['lng']}")
            st.markdown(f"**Needs:** {inc['resource'] or 'Assessing'}")
            st.markdown(f"**People:** {inc['people_latest'] or 'Unknown'}")
            if inc['vulnerable']:
                vuln_list = json.loads(inc['vulnerable']) if isinstance(inc['vulnerable'], str) else inc['vulnerable']
                st.markdown(f"**Vulnerable:** {', '.join(vuln_list)}")

        with tabs[1]:
            st.markdown("**AI Clustering Logic**")
            decisions = get_matching_decision(inc['id'])
            reports = get_incident_reports(inc['id'])
            st.markdown(f"*{len(reports)} independent reports fused.*")
            for d in decisions:
                st.caption(f"→ Report {d['report_id']} merged (Score: {d['final_score']:.2f}).")

        with tabs[2]:
            st.markdown("**Raw Intel Sources**")
            reports = get_incident_reports(inc['id'])
            for r in reports:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); padding:8px; border-radius:5px; margin-bottom:10px; font-size:0.85rem;">
                    <div style="color:#00f0ff; margin-bottom:5px;">[{r['source'].upper()}] {r['received_at'][-8:]}</div>
                    "{r['raw_text']}"
                </div>
                """, unsafe_allow_html=True)

def render_pipeline_feed(pending, all_incidents):
    """Render the pipeline feed panel"""
    st.markdown("<h4 style='color:white; margin-bottom:15px;'>Multi-Modal Intel</h4>", unsafe_allow_html=True)
    st.metric("Raw Intel Processed", st.session_state.raw_count)
    st.metric("Pending in AI Queue", len(pending))

    st.markdown("---")
    st.markdown("<h5 style='color:#a0aec0;'>Live AI Pipeline Feed</h5>", unsafe_allow_html=True)
    if pending:
        st.markdown(f"<div style='color:#00f0ff; font-size:0.85rem;'>● Processing {pending[0]['id']}...</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#00ff64; font-size:0.85rem;'>● Pipeline Idle (Awaiting Intel)</div>", unsafe_allow_html=True)

    events_list = []
    for inc in all_incidents:
        events = get_incident_events(inc['id'])
        events_list.extend(events)

    events_list = sorted(events_list, key=lambda x: x['id'], reverse=True)[:5]
    for ev in events_list:
        st.markdown(f"""
        <div style="font-size:0.8rem; color:#a0aec0; margin-bottom:8px; border-left:2px solid #1a365d; padding-left:10px;">
            <span style="color:#718096;">{ev['time'][-8:]}</span><br>
            <span style="color:white;">{ev['event_type']}</span>: {ev['detail'][:40]}...
        </div>
        """, unsafe_allow_html=True)

# --- OVERVIEW VIEW ---
if current_view == "overview":
    left_col, mid_col, right_col = st.columns([1, 2.5, 1.2])

    with left_col:
        render_pipeline_feed(pending, all_incidents)

    with mid_col:
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Active Incidents", inc_count)
        col_m2.metric("High/Critical Risk", crit_count)
        people_est = sum((i.get('people_latest') or 0) for i in all_incidents)
        col_m3.metric("Affected Population", f"~ {people_est}")

        render_map(all_incidents)

    with right_col:
        render_incident_panel(active_incidents)

# --- INCIDENTS VIEW ---
elif current_view == "incidents":
    st.markdown("<h2 style='color:white; margin-bottom:20px;'>Incident Feed</h2>", unsafe_allow_html=True)

    if not all_incidents:
        st.info("No incidents to display.")
    else:
        for inc in all_incidents:
            urgency_color = "red" if inc['urgency'] in ['critical', 'high'] else "orange" if inc['urgency'] == 'medium' else "blue"
            status_color = "green" if inc['status'] == 'resolved' else "red" if inc['status'] == 'active' else "yellow"

            # Pre-calculate RGB values
            urgency_rgb = "255,50,50" if urgency_color == 'red' else "255,170,0" if urgency_color == 'orange' else "0,100,255"
            status_rgb = "0,255,100" if status_color == 'green' else "255,50,50" if status_color == 'red' else "255,170,0"

            st.markdown(f"""
            <div style="background:rgba(16, 32, 56, 0.4); border:1px solid #1a365d; border-radius:10px; padding:15px; margin-bottom:15px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div style="color:white; font-weight:bold; font-size:1.1rem;">{inc['id']}</div>
                    <div style="display:flex; gap:10px;">
                        <span style="background:rgba({urgency_rgb},0.2); color:{urgency_color}; padding:4px 12px; border-radius:4px; border:1px solid {urgency_color}; font-size:0.75rem; font-weight:bold;">{inc['urgency'].upper()}</span>
                        <span style="background:rgba({status_rgb},0.2); color:{status_color}; padding:4px 12px; border-radius:4px; border:1px solid {status_color}; font-size:0.75rem; font-weight:bold;">{inc['status'].replace('_', ' ').upper()}</span>
                    </div>
                </div>
                <div style="color:#a0aec0; font-size:0.9rem; margin-bottom:5px;">📍 {inc['location_text'] or 'Unknown Location'}</div>
                <div style="color:#e0e6ed; font-size:0.85rem; margin-bottom:10px;">{inc['summary']}</div>
                <div style="display:flex; gap:20px; color:#718096; font-size:0.8rem;">
                    <span>👥 {inc['people_latest'] or 0} people</span>
                    <span>🚑 {inc['resource'] or 'Assessing'}</span>
                    <span>🕐 {inc['last_updated'][:19] if inc['last_updated'] else 'N/A'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- MAP VIEW ---
elif current_view == "map":
    st.markdown("<h2 style='color:white; margin-bottom:20px;'>Incident Map</h2>", unsafe_allow_html=True)
    render_map(all_incidents, height=650)

# --- ANALYTICS VIEW ---
elif current_view == "analytics":
    st.markdown("<h2 style='color:white; margin-bottom:20px;'>Analytics Dashboard</h2>", unsafe_allow_html=True)

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Incidents", len(all_incidents))
    with col2:
        st.metric("Active", len(active_incidents))
    with col3:
        st.metric("Resolved", len(all_incidents) - len(active_incidents))
    with col4:
        resolution_rate = round(((len(all_incidents) - len(active_incidents)) / len(all_incidents) * 100), 1) if all_incidents else 0
        st.metric("Resolution Rate", f"{resolution_rate}%")

    # Urgency distribution
    st.markdown("<h3 style='color:white; margin-top:30px; margin-bottom:15px;'>Urgency Distribution</h3>", unsafe_allow_html=True)
    urgency_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for inc in all_incidents:
        if inc['urgency'] in urgency_counts:
            urgency_counts[inc['urgency']] += 1

    for urgency, count in urgency_counts.items():
        percentage = (count / len(all_incidents) * 100) if all_incidents else 0
        if urgency == 'critical':
            color = "red"
        elif urgency == 'high':
            color = "orange"
        elif urgency == 'medium':
            color = "yellow"
        else:
            color = "blue"
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
            <div style="width:100px; color:#a0aec0; font-weight:bold; text-transform:uppercase;">{urgency}</div>
            <div style="flex:1; background:#1a365d; border-radius:5px; height:30px; overflow:hidden;">
                <div style="background:{color}; height:100%; width:{percentage}%"></div>
            </div>
            <div style="width:50px; color:white; font-weight:bold; text-align:right;">{count}</div>
        </div>
        """, unsafe_allow_html=True)

    # Resource types
    st.markdown("<h3 style='color:white; margin-top:30px; margin-bottom:15px;'>Resource Types Needed</h3>", unsafe_allow_html=True)
    resource_counts = {}
    for inc in all_incidents:
        resource = inc['resource'] or 'unknown'
        resource_counts[resource] = resource_counts.get(resource, 0) + 1

    for resource, count in sorted(resource_counts.items(), key=lambda x: x[1], reverse=True):
        resource_pct = (count / len(all_incidents) * 100) if all_incidents else 0
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
            <div style="width:150px; color:#a0aec0; font-weight:bold; text-transform:capitalize;">{resource}</div>
            <div style="flex:1; background:#1a365d; border-radius:5px; height:30px; overflow:hidden;">
                <div style="background:#00f0ff; height:100%; width:{resource_pct}%"></div>
            </div>
            <div style="width:50px; color:white; font-weight:bold; text-align:right;">{count}</div>
        </div>
        """, unsafe_allow_html=True)

# --- REPORTS VIEW ---
elif current_view == "reports":
    st.markdown("<h2 style='color:white; margin-bottom:20px;'>Incident Reports</h2>", unsafe_allow_html=True)

    if not all_incidents:
        st.info("No incidents to report.")
    else:
        # Create dataframe for export
        df_data = []
        for inc in all_incidents:
            vuln_list = json.loads(inc['vulnerable']) if isinstance(inc['vulnerable'], str) else inc['vulnerable']
            df_data.append({
                "ID": inc['id'],
                "Status": inc['status'],
                "Urgency": inc['urgency'],
                "Location": inc['location_text'] or 'Unknown',
                "Resource": inc['resource'] or 'Assessing',
                "People": inc['people_latest'] or 0,
                "Vulnerable": ', '.join(vuln_list) if vuln_list else '',
                "First Seen": inc['first_seen'][:19] if inc['first_seen'] else 'N/A',
                "Last Updated": inc['last_updated'][:19] if inc['last_updated'] else 'N/A',
                "Summary": inc['summary']
            })

        df = pd.DataFrame(df_data)

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "active", "rescue_in_progress", "resolved"])
        with col2:
            urgency_filter = st.selectbox("Filter by Urgency", ["All", "critical", "high", "medium", "low"])
        with col3:
            st.download_button(
                "Export CSV",
                df.to_csv(index=False).encode('utf-8'),
                "incident_report.csv",
                "text/csv"
            )

        # Apply filters
        if status_filter != "All":
            df = df[df['Status'] == status_filter]
        if urgency_filter != "All":
            df = df[df['Urgency'] == urgency_filter]

        st.dataframe(df, use_container_width=True, hide_index=True)

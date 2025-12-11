"""
AeroGuard - Autonomous Disaster Response Commander
Powered by NVIDIA Grace Blackwell GB10
"""

import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import time
import backend
import vision
import cv2
import tempfile
import base64
from fpdf import FPDF
import torch
import subprocess
import os
from homepage import render_homepage

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="AeroGuard | GB10 Edge AI", 
    layout="wide", 
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# --- COMPREHENSIVE CSS ---
st.markdown("""
<style>
    /* Base Styling */
    .stApp {
        background-color: #000000;
        color: #d0e0d0;
    }
    
    /* Typography */
    h1 {
        color: #7fff00; 
        font-weight: 900; 
        letter-spacing: -1px;
        text-shadow: 0 0 15px rgba(127,255,0,0.4);
        margin-bottom: 5px;
    }
    h2 {
        color: #7fb069; 
        font-weight: 700;
        border-bottom: 2px solid #2d5a3d; 
        padding-bottom: 12px;
        margin-top: 30px;
    }
    h3 {
        color: #7fb069;
        font-weight: 600;
        margin-top: 20px;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #2d5a3d;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #7fb069 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #2d5a3d;
        margin: 20px 0;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4a8a5a 0%, #357045 100%);
        color: white !important;
        border: 1px solid #5a9a6a;
        border-radius: 8px;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 14px;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #5a9a6a 0%, #458055 100%);
        border-color: #6aaa7a;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(74,138,90,0.4);
    }
    .stButton>button:disabled {
        background: rgba(45,90,61,0.3);
        color: rgba(176,192,176,0.5) !important;
        border: 1px solid rgba(45,90,61,0.5);
        cursor: not-allowed;
        transform: none;
    }
    
    /* Download Button */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #3d6a4d 0%, #2d5a3d 100%);
        color: white !important;
        border: 1px solid #4a7a5a;
        border-radius: 6px;
        font-weight: 600;
        padding: 10px 20px;
    }
    .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #4d7a5d 0%, #3d6a4d 100%);
        box-shadow: 0 4px 12px rgba(74,138,90,0.3);
    }
    
    /* Info/Alert Boxes */
    .stAlert, [data-baseweb="notification"] {
        background: rgba(26,58,42,0.6) !important;
        border: 1px solid #2d5a3d !important;
        border-radius: 8px;
        color: #b0c0b0 !important;
    }
    .stSuccess {
        background: rgba(74,138,90,0.3) !important;
        border: 1px solid #4a8a5a !important;
        color: #7fb069 !important;
    }
    .stError {
        background: rgba(139,0,0,0.3) !important;
        border: 1px solid #8b0000 !important;
        color: #ff6b6b !important;
    }
    .stWarning {
        background: rgba(204,85,0,0.3) !important;
        border: 1px solid #cc5500 !important;
        color: #ffa500 !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #7fb069 !important;
        font-weight: 700;
        font-size: 24px;
    }
    [data-testid="stMetricLabel"] {
        color: #90b090 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 12px;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #357045 0%, #4a8a5a 50%, #5a9a6a 100%) !important;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: rgba(26,58,42,0.4);
        border: 1px solid #2d5a3d;
        border-radius: 10px;
        padding: 20px;
    }
    [data-testid="stFileUploader"] label {
        color: #7fb069 !important;
        font-weight: 600;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(26,58,42,0.5) !important;
        border: 1px solid #2d5a3d !important;
        border-radius: 8px !important;
        color: #7fb069 !important;
        font-weight: 600;
    }
    .streamlit-expanderHeader:hover {
        background: rgba(26,58,42,0.7) !important;
        border-color: #4a7c59 !important;
    }
    
    /* Captions */
    .stCaption {
        color: #90b090 !important;
        font-size: 13px;
        font-style: italic;
    }
    
    /* JSON Display */
    .stJson {
        background: rgba(15,30,15,0.8) !important;
        border: 1px solid #2d5a3d !important;
        border-radius: 6px;
    }
    
    /* Custom Components */
    .section-header {
        background: linear-gradient(90deg, rgba(74,138,90,0.2) 0%, transparent 100%);
        padding: 15px 20px;
        border-left: 4px solid #4a8a5a;
        border-radius: 4px;
        margin: 20px 0 15px 0;
    }
    .section-header h3 {
        margin: 0;
        color: #7fb069;
        font-size: 18px;
        font-weight: 700;
    }
    
    .status-card {
        background: linear-gradient(145deg, #1a3a2a 0%, #0f2419 100%);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2d5a3d;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .status-card:hover {
        border-color: #4a7c59;
        box-shadow: 0 6px 20px rgba(74,138,90,0.2);
    }
    
    .thinking-box {
        font-family: 'Courier New', monospace; 
        font-size: 13px; 
        color: #a0b0a0;
        background: linear-gradient(135deg, #0f1f15 0%, #1a2f25 100%); 
        padding: 20px; 
        border-radius: 10px;
        border: 1px solid #2d5a3d;
        max-height: 300px; 
        overflow-y: auto;
        margin-bottom: 20px;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.4);
    }
    
    .command-box {
        font-family: 'Courier New', monospace; 
        font-size: 14px; 
        color: #d0e0d0;
        background: linear-gradient(135deg, #1a3a2a 0%, #0f2419 100%); 
        padding: 20px; 
        border-radius: 10px;
        border: 1px solid #4a8a5a;
        box-shadow: 0 4px 15px rgba(74,138,90,0.2);
        margin-bottom: 20px;
    }
    
    .command-label {
        color: #7fb069; 
        font-size: 11px; 
        text-transform: uppercase; 
        letter-spacing: 2px; 
        margin-bottom: 10px;
        font-weight: 700;
        display: block;
    }
    
    .log-entry {
        font-family: 'Courier New', monospace; 
        font-size: 13px;
        margin-bottom: 8px; 
        padding: 10px 15px;
        border-radius: 6px;
        background: rgba(26,58,42,0.3);
        border-left: 3px solid #4a7c59;
        transition: all 0.2s ease;
    }
    .log-entry:hover {
        background: rgba(26,58,42,0.5);
        border-left-color: #5a9a6a;
    }
    
    /* Container Spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Image Styling */
    img {
        border-radius: 8px;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #0f1f15;
    }
    ::-webkit-scrollbar-thumb {
        background: #2d5a3d;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #4a7c59;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'page' not in st.session_state: 
    st.session_state.page = "home"
if 'latest_observation' not in st.session_state: 
    st.session_state.latest_observation = "System Ready. Awaiting visual feed..."
if 'command_log' not in st.session_state: 
    st.session_state.command_log = []
if 'hazard_level' not in st.session_state: 
    st.session_state.hazard_level = "UNKNOWN"
if 'processed_frames' not in st.session_state: 
    st.session_state.processed_frames = []
if 'last_thought' not in st.session_state: 
    st.session_state.last_thought = ""
if 'last_command' not in st.session_state: 
    st.session_state.last_command = ""
if 'last_reasoning' not in st.session_state: 
    st.session_state.last_reasoning = ""
if 'last_deployed_squad' not in st.session_state: 
    st.session_state.last_deployed_squad = ""
if 'squads' not in st.session_state: 
    st.session_state.squads = backend.SQUADS.copy()
if 'scan_completed' not in st.session_state: 
    st.session_state.scan_completed = False
if 'command_executed' not in st.session_state: 
    st.session_state.command_executed = False

# --- UTILITY FUNCTIONS ---
def get_gpu_metrics():
    """Fetch GPU telemetry from system"""
    try:
        free, total = torch.cuda.mem_get_info(0)
        used_gb = (total - free) / 1024**3
        total_gb = total / 1024**3
        mem_str = f"{used_gb:.1f} / {total_gb:.1f} GB"
        
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], 
            encoding="utf-8"
        )
        load_str = f"{result.strip()}%"
    except:
        load_str = "N/A"
        mem_str = "N/A"

    return {
        "load": load_str, 
        "mem": mem_str,
        "name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Simulation Mode"
    }

def generate_pdf_report():
    """Generate comprehensive mission PDF report"""
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'AeroGuard Mission Report', 0, 1, 'C')
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, f'Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()} | CONFIDENTIAL | GB10 Edge Gateway', 0, 0, 'C')
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # System Status
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '1. SYSTEM STATUS', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"Latest Observation:", 0, 1)
    pdf.multi_cell(0, 6, f"{st.session_state.latest_observation}")
    pdf.cell(0, 6, f"Hazard Level: {st.session_state.hazard_level}", 0, 1)
    pdf.ln(5)
    
    # Squad Assets
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. SQUAD DEPLOYMENT STATUS', 0, 1)
    pdf.set_font('Arial', '', 10)
    for name, data in st.session_state.squads.items():
        status_str = f"{name} ({data['type']}): {data['status']} @ {data['loc']}"
        pdf.cell(0, 6, f"  -- {status_str}", 0, 1)
    pdf.ln(5)
    
    # Command Logs
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3. COMMAND HISTORY', 0, 1)
    pdf.set_font('Arial', '', 9)
    for log in reversed(st.session_state.command_log):
        pdf.multi_cell(0, 5, log)
        pdf.ln(1)
    
    return bytes(pdf.output())

def render_dynamic_map():
    """Renders tactical map with professional geographic positioning"""
    import random
    
    nodes = []
    edges = []
    
    active_squad_name = st.session_state.last_deployed_squad
    
    # Map dimensions
    MAP_WIDTH = 1000
    MAP_HEIGHT = 700
    
    def get_position(name, seed_offset=0):
        """Generate consistent position for each squad"""
        random.seed(hash(name) + seed_offset)
        x = random.randint(50, MAP_WIDTH - 50)
        y = random.randint(50, MAP_HEIGHT - 50)
        return x, y
    
    # 1. HQ/Base
    base_x, base_y = 150, 150
    nodes.append(Node(
        id="Base", 
        label="HQ", 
        size=45, 
        shape="box", 
        color="#2a5a2a",
        font={'color': '#ffffff', 'size': 14, 'face': 'arial'},
        x=base_x,
        y=base_y,
        fixed=True
    ))
    
    # 2. Impact Zone
    impact_x, impact_y = MAP_WIDTH - 200, MAP_HEIGHT - 200
    t_color = "#8b0000" if "CRITICAL" in st.session_state.hazard_level else "#cc5500" if "MODERATE" in st.session_state.hazard_level else "#555555"
    t_size = 55 if "CRITICAL" in st.session_state.hazard_level else 45
    t_label = "IMPACT ZONE\n[CRITICAL]" if "CRITICAL" in st.session_state.hazard_level else "IMPACT ZONE\n[MODERATE]" if "MODERATE" in st.session_state.hazard_level else "IMPACT ZONE"
    
    nodes.append(Node(
        id="ImpactZone", 
        label=t_label, 
        size=t_size, 
        shape="box", 
        color=t_color,
        font={'color': '#ffffff', 'size': 13, 'face': 'arial'},
        x=impact_x,
        y=impact_y,
        fixed=True
    ))
    
    # 3. Squad Nodes
    squad_list = list(st.session_state.squads.items())
    
    for idx, (name, data) in enumerate(squad_list):
        base_x_offset, base_y_offset = get_position(name, seed_offset=0)
        
        if "Base" in data['loc']:
            offset_x = (idx % 3) * 120
            offset_y = (idx // 3) * 100
            x = base_x + offset_x - 60
            y = base_y + offset_y + 80
        elif "Sector 4" in data['loc'] or "Impact" in data['loc']:
            angle = (idx * 45) * (3.14159 / 180)
            radius = 180
            x = impact_x + int(radius * random.uniform(0.7, 1.0) * random.choice([-1, 1]))
            y = impact_y + int(radius * random.uniform(0.7, 1.0) * random.choice([-1, 1]))
        else:
            x = MAP_WIDTH // 2 + (idx * 80) - 200
            y = MAP_HEIGHT // 2 + ((idx % 2) * 100) - 50
        
        x = max(80, min(MAP_WIDTH - 80, x))
        y = max(80, min(MAP_HEIGHT - 80, y))
        
        if name == active_squad_name:
            s_color = "#ffa500"
            s_size = 35
            border_width = 3
        elif "Sector 4" in data['loc'] or "Impact" in data['loc']:
            s_color = "#cc3333"
            s_size = 28
            border_width = 2
        elif "Base" in data['loc']:
            s_color = "#4a7c59"
            s_size = 25
            border_width = 1
        else:
            s_color = "#6b8e23"
            s_size = 25
            border_width = 1
        
        s_label = f"{name}\n[{data['type']}]"
        
        nodes.append(Node(
            id=name, 
            label=s_label, 
            size=s_size, 
            shape="dot", 
            color=s_color,
            font={'color': '#ffffff', 'size': 11, 'face': 'arial'},
            borderWidth=border_width,
            x=x,
            y=y,
            fixed=True
        ))
    
    config = Config(
        width="100%", 
        height=650,
        directed=False,
        physics=False,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#ffa500"
    )
    
    return nodes, edges, config

# --- HOME PAGE ---
def show_home_page():
    render_homepage()

# --- DASHBOARD ---
def show_dashboard():
    # Sidebar
    with st.sidebar:
        if st.button("← Back to Home", use_container_width=True): 
            st.session_state.page = "home"
            st.rerun()
        
        st.markdown("---")
        
        # Hardware Telemetry
        st.markdown("<div class='section-header'><h3>Hardware Telemetry</h3></div>", unsafe_allow_html=True)
        
        gpu_stats = get_gpu_metrics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("GPU Load", gpu_stats["load"])
        with col2:
            st.metric("VRAM Usage", gpu_stats["mem"])
        
        try:
            val = float(gpu_stats["load"].strip('%')) / 100
        except: 
            val = 0.0
        st.progress(val)
        st.caption(f"**Device:** {gpu_stats['name']}")
        
        st.markdown("---")
        
        # Mission Controls
        st.markdown("<div class='section-header'><h3>Mission Controls</h3></div>", unsafe_allow_html=True)
        
        report_pdf = generate_pdf_report()
        download_enabled = st.session_state.command_executed
        
        st.download_button(
            "📄 Download Mission Report", 
            report_pdf, 
            f"AeroGuard_Mission_{time.strftime('%Y%m%d_%H%M%S')}.pdf", 
            "application/pdf",
            disabled=not download_enabled,
            help="Execute a command first to enable report download" if not download_enabled else "Download comprehensive mission report",
            use_container_width=True
        )
        
        if not download_enabled:
            st.caption("⚠ Execute a command to enable report download")
        
        st.markdown("---")
        
        # Squad Status
        st.markdown("<div class='section-header'><h3>Squad Assets</h3></div>", unsafe_allow_html=True)
        
        with st.expander("View Squad Status", expanded=False):
            st.json(st.session_state.squads)
    
    # Main Dashboard
    st.title("AeroGuard Command Center")
    st.caption("Real-Time Autonomous Disaster Response Coordination")
    
    # Status Overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class='status-card'>
            <div style='color: #7fb069; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;'>System Status</div>
            <div style='color: #7fff00; font-size: 20px; font-weight: 700;'>OPERATIONAL</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        hazard_color = "#cc3333" if "CRITICAL" in st.session_state.hazard_level else "#ffa500" if "MODERATE" in st.session_state.hazard_level else "#4a7c59"
        st.markdown(f"""
        <div class='status-card'>
            <div style='color: #7fb069; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;'>Hazard Level</div>
            <div style='color: {hazard_color}; font-size: 20px; font-weight: 700;'>{st.session_state.hazard_level}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        active_squads = sum(1 for s in st.session_state.squads.values() if s['status'] != 'Idle')
        st.markdown(f"""
        <div class='status-card'>
            <div style='color: #7fb069; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;'>Active Squads</div>
            <div style='color: #7fff00; font-size: 20px; font-weight: 700;'>{active_squads} / 8</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Content Area
    row1_col1, row1_col2 = st.columns([3, 2], gap="large")
    
    # LEFT: Vision Analysis
    with row1_col1:
        st.markdown("<div class='section-header'><h3>Vision Analysis Pipeline</h3></div>", unsafe_allow_html=True)
        st.caption("Real-time drone feed processing with SAM 2 + CLIP")
        
        uploaded_file = st.file_uploader(
            "Upload Drone Feed", 
            type=['mp4', 'mov'],
            help="Upload MP4 or MOV video from drone reconnaissance"
        )
        
        display_slot = st.empty()
        stats_slot = st.empty()
        
        if uploaded_file and st.button("▶ START HAZARD SCAN", type="primary", use_container_width=True):
            st.session_state.processed_frames = []
            st.session_state.scan_completed = False
            st.session_state.command_executed = False
            
            MAX_FRAMES_TO_STORE = 50
            
            uploaded_file.seek(0) 
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') 
            tfile.write(uploaded_file.read())
            video_path = tfile.name
            tfile.close()
            
            try:
                cap = cv2.VideoCapture(video_path)
                frame_count = 0
                SKIP_RATE = 25 
                error_count = 0
                MAX_ERRORS = 10
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break
                    frame_count += 1
                    
                    # Update progress
                    progress = min(frame_count / total_frames, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing frame {frame_count}/{total_frames}...")
                    
                    if frame_count % SKIP_RATE != 0: continue 
                    
                    _, buffer = cv2.imencode('.jpg', frame)
                    processed_img_bytes, stats = vision.process_frame_realtime(buffer.tobytes())
                    
                    if processed_img_bytes and stats:
                        if len(st.session_state.processed_frames) < MAX_FRAMES_TO_STORE:
                            st.session_state.processed_frames.append(processed_img_bytes)
                        
                        display_slot.image(
                            processed_img_bytes, 
                            caption="Real-Time SAM 2 Segmentation", 
                            use_container_width=True
                        )
                        
                        hazard = stats['hazard_type'].upper()
                        coverage = stats['coverage_pct']
                        tag_color = "#cc3333" if coverage > 20 else "#4a8a5a"
                        
                        stats_slot.markdown(f"""
                        <div style='background: linear-gradient(145deg, #1a3a2a 0%, #0f2419 100%); padding: 20px; border-radius: 10px; border: 1px solid {tag_color}; margin-top: 15px;'>
                            <div style='color: {tag_color}; font-size: 20px; font-weight: 700; margin-bottom: 12px;'>
                                DETECTED: {hazard}
                            </div>
                            <div style='color: #b0c0b0; font-size: 14px; line-height: 1.8;'>
                                <strong>Coverage:</strong> {coverage}% of impact zone<br>
                                <strong>Segments:</strong> {stats['mask_count']} active masks<br>
                                <strong>Confidence:</strong> {stats.get('hazard_confidence', 'N/A')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        severity = "CRITICAL" if coverage > 40 else "MODERATE" if coverage > 15 else "MINOR"
                        st.session_state.hazard_level = severity 
                        st.session_state.latest_observation = f"Visual Scan: {hazard}. Coverage: {coverage}%. Severity: {severity}. Active Masks: {stats['mask_count']}."
                    else:
                        error_count += 1
                        if error_count >= MAX_ERRORS:
                            st.warning(f"⚠ Too many frame processing errors ({MAX_ERRORS}). Stopping scan.")
                            break
                        continue
                
                cap.release()
                progress_bar.empty()
                status_text.empty()
                
                if len(st.session_state.processed_frames) == MAX_FRAMES_TO_STORE:
                    st.warning(f"⚠ Frame storage limit reached ({MAX_FRAMES_TO_STORE} frames). Only recent frames saved.")
                
                st.session_state.scan_completed = True
                st.success(f"✓ Scan Complete. Processed {frame_count // SKIP_RATE} frames. Ready for command execution.")
                
            finally:
                if os.path.exists(video_path):
                    os.unlink(video_path)
        
        if st.session_state.processed_frames:
            with st.expander("📂 Mission Gallery", expanded=False):
                cols = st.columns(4)
                for idx, img_bytes in enumerate(st.session_state.processed_frames):
                    with cols[idx % 4]: 
                        st.image(img_bytes, caption=f"Frame {idx+1}", use_container_width=True)
    
    # RIGHT: AI Commander
    with row1_col2:
        st.markdown("<div class='section-header'><h3>AI Commander Logic</h3></div>", unsafe_allow_html=True)
        st.caption("DeepSeek R1 chain-of-thought reasoning engine")
        
        st.info(f"**Observation:** {st.session_state.latest_observation}")
        
        command_enabled = st.session_state.scan_completed
        
        if st.button(
            "EXECUTE COMMAND PROTOCOL", 
            type="primary", 
            disabled=not command_enabled, 
            use_container_width=True
        ):
            timestamp = time.strftime("%H:%M:%S")
            
            think_placeholder = st.empty()
            cmd_placeholder = st.empty()
            reasoning_placeholder = st.empty()
            status_placeholder = st.empty()
            
            full_thinking = ""
            full_command = ""
            formal_reasoning = ""
            deployment_info = None  # Change to None instead of {}
            has_error = False
            
            for chunk in backend.stream_commander(st.session_state.latest_observation, st.session_state.squads):
                if chunk["type"] == "thinking":
                    full_thinking += chunk["content"]
                    think_placeholder.markdown(
                        f"<div class='thinking-box'><span class='command-label'>Chain-of-Thought Reasoning:</span>{full_thinking}▌</div>", 
                        unsafe_allow_html=True
                    )
                
                elif chunk["type"] == "answer":
                    full_command += chunk["content"]
                    cmd_placeholder.markdown(
                        f"<div class='command-box'><span class='command-label'>Structured Response:</span><code style='color: #7fb069; font-size: 12px;'>{full_command}▌</code></div>", 
                        unsafe_allow_html=True
                    )
                
                elif chunk["type"] == "reasoning":
                    # Store deployment info
                    deployment_info = {
                        "squad": chunk.get("squad", ""),
                        "location": chunk.get("location", ""),
                        "action": chunk.get("action", "")
                    }
                    formal_reasoning = chunk["content"]
                    
                    # Display reasoning immediately
                    if deployment_info["action"] == "deploy":
                        reasoning_display = f"""
                        <div style='background: linear-gradient(145deg, #1a3a2a 0%, #0f2419 100%); padding: 25px; border-radius: 12px; border: 1px solid #4a8a5a; margin: 20px 0;'>
                            <h3 style='color: #7fb069; margin: 0 0 15px 0; font-size: 18px; font-weight: 700;'>TACTICAL DECISION</h3>
                            <p style='color: #d0e0d0; font-size: 15px; line-height: 1.8; margin-bottom: 20px;'>{formal_reasoning}</p>
                            <hr style='border: none; border-top: 1px solid #2d5a3d; margin: 20px 0;'>
                            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
                                <div style='background: rgba(74,138,90,0.2); padding: 15px; border-radius: 8px;'>
                                    <div style='color: #7fb069; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>Deployed Unit</div>
                                    <div style='color: #ffffff; font-size: 20px; font-weight: 700;'>Squad {deployment_info["squad"]}</div>
                                </div>
                                <div style='background: rgba(74,138,90,0.2); padding: 15px; border-radius: 8px;'>
                                    <div style='color: #7fb069; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>Target Location</div>
                                    <div style='color: #ffffff; font-size: 20px; font-weight: 700;'>{deployment_info["location"]}</div>
                                </div>
                            </div>
                        </div>
                        """
                    else:
                        reasoning_display = f"""
                        <div style='background: linear-gradient(145deg, #2d4a3d 0%, #1a3a2a 100%); padding: 25px; border-radius: 12px; border: 1px solid #5a9a6a; margin: 20px 0;'>
                            <h3 style='color: #7fb069; margin: 0 0 15px 0; font-size: 18px; font-weight: 700;'>HOLD POSITION</h3>
                            <p style='color: #d0e0d0; font-size: 15px; line-height: 1.8;'>{formal_reasoning}</p>
                        </div>
                        """
                    
                    reasoning_placeholder.markdown(reasoning_display, unsafe_allow_html=True)
                
                elif chunk["type"] == "error":
                    st.error(f"⚠ Command Protocol Failed: {chunk['content']}")
                    has_error = True
                    break
                
                elif chunk["type"] == "status":
                    status_placeholder.success(chunk["content"])
                
                elif chunk["type"] == "warning":
                    status_placeholder.warning(chunk["content"])
            
            # After streaming completes
            if not has_error and deployment_info:
                st.session_state.last_thought = full_thinking
                st.session_state.last_command = full_command
                st.session_state.last_reasoning = formal_reasoning
                st.session_state.last_deployed_squad = deployment_info.get("squad", "")
                
                # Create log entry
                if deployment_info["action"] == "deploy":
                    log_entry = f"[{timestamp}] Deployed {deployment_info['squad']} to {deployment_info['location']}"
                else:
                    log_entry = f"[{timestamp}] HOLD: All squads maintaining position"
                
                st.session_state.command_log.insert(0, log_entry)
                st.session_state.command_executed = True
                st.rerun()

        if not command_enabled:
            st.caption("⚠ Complete a hazard scan first to enable command execution")
        
        # Persistent Display
        if st.session_state.last_thought:
            with st.expander("Chain-of-Thought History", expanded=False):
                st.markdown(f"<div class='thinking-box'>{st.session_state.last_thought}</div>", unsafe_allow_html=True)
        
        if st.session_state.last_reasoning:
            st.markdown(f"""
            <div style='background: linear-gradient(145deg, #1a3a2a 0%, #0f2419 100%); padding: 20px; border-radius: 10px; border: 1px solid #4a8a5a; margin: 15px 0;'>
                <h3 style='color: #7fb069; margin: 0 0 12px 0; font-size: 16px;'>LAST COMMAND DECISION</h3>
                <p style='color: #d0e0d0; font-size: 14px; line-height: 1.7;'>{st.session_state.last_reasoning}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Raw JSON Response", expanded=False):
                st.code(st.session_state.last_command, language="json")
        
        # Command Log
        st.markdown("<div class='section-header' style='margin-top: 30px;'><h3>Command Log</h3></div>", unsafe_allow_html=True)
        
        log_container = st.container(height=220)
        with log_container:
            if st.session_state.command_log:
                for log_entry in st.session_state.command_log:
                    color = "#4a8a5a" if "Deployed" in log_entry else "#b0c0b0"
                    st.markdown(
                        f"<div class='log-entry' style='border-left-color: {color};'>{log_entry}</div>", 
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No commands executed yet")
    
    # Map Section
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'><h3>Tactical Operations Map</h3></div>", unsafe_allow_html=True)
    st.caption("Real-time squad positioning and deployment status")
    
    # Map with terrain background
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #1a2f1a 0%, #2d4a2d 50%, #1a2f1a 100%);
        background-image: 
            repeating-linear-gradient(0deg, transparent, transparent 50px, rgba(255,255,255,0.02) 50px, rgba(255,255,255,0.02) 51px),
            repeating-linear-gradient(90deg, transparent, transparent 50px, rgba(255,255,255,0.02) 50px, rgba(255,255,255,0.02) 51px);
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #2d5a3d;
        margin: 20px 0;
    '>
    """, unsafe_allow_html=True)
    
    nodes, edges, config = render_dynamic_map()
    agraph(nodes=nodes, edges=edges, config=config)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Squad Capabilities
    st.markdown("""
    <div style='background: linear-gradient(145deg, #0f1f15 0%, #1a2f25 100%); padding: 25px; border-radius: 10px; border: 1px solid #2d5a3d; margin-top: 20px;'>
        <strong style='color: #7fb069; font-size: 16px; display: block; margin-bottom: 20px;'>SQUAD CAPABILITIES</strong>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;'>
            <div style='background: rgba(26,58,42,0.3); padding: 15px; border-radius: 8px; border-left: 3px solid #4a7c59;'>
                <div style='color: #7fb069; font-weight: 700; margin-bottom: 5px;'>Alpha (Ground)</div>
                <div style='color: #b0c0b0; font-size: 13px;'>General operations, road clearing, light medical</div>
            </div>
            <div style='background: rgba(26,58,42,0.3); padding: 15px; border-radius: 8px; border-left: 3px solid #4a7c59;'>
                <div style='color: #7fb069; font-weight: 700; margin-bottom: 5px;'>Bravo (Aerial)</div>
                <div style='color: #b0c0b0; font-size: 13px;'>Aerial reconnaissance, fire/flood assessment</div>
            </div>
            <div style='background: rgba(26,58,42,0.3); padding: 15px; border-radius: 8px; border-left: 3px solid #4a7c59;'>
                <div style='color: #7fb069; font-weight: 700; margin-bottom: 5px;'>Charlie (Medical)</div>
                <div style='color: #b0c0b0; font-size: 13px;'>Advanced medical triage, trauma care</div>
            </div>
            <div style='background: rgba(26,58,42,0.3); padding: 15px; border-radius: 8px; border-left: 3px solid #4a7c59;'>
                <div style='color: #7fb069; font-weight: 700; margin-bottom: 5px;'>Delta (Engineering)</div>
                <div style='color: #b0c0b0; font-size: 13px;'>Infrastructure repair, rubble clearing, power restoration</div>
            </div>
            <div style='background: rgba(26,58,42,0.3); padding: 15px; border-radius: 8px; border-left: 3px solid #4a7c59;'>
                <div style='color: #7fb069; font-weight: 700; margin-bottom: 5px;'>Echo (Rescue)</div>
                <div style='color: #b0c0b0; font-size: 13px;'>Water rescue, swift water operations, lifeboats</div>
            </div>
            <div style='background: rgba(26,58,42,0.3); padding: 15px; border-radius: 8px; border-left: 3px solid #4a7c59;'>
                <div style='color: #7fb069; font-weight: 700; margin-bottom: 5px;'>Foxtrot (Logistics)</div>
                <div style='color: #b0c0b0; font-size: 13px;'>Supply transport, fuel distribution, logistics</div>
            </div>
            <div style='background: rgba(26,58,42,0.3); padding: 15px; border-radius: 8px; border-left: 3px solid #4a7c59;'>
                <div style='color: #7fb069; font-weight: 700; margin-bottom: 5px;'>Golf (Recon)</div>
                <div style='color: #b0c0b0; font-size: 13px;'>Scouting, intelligence gathering, light recon</div>
            </div>
            <div style='background: rgba(26,58,42,0.3); padding: 15px; border-radius: 8px; border-left: 3px solid #4a7c59;'>
                <div style='color: #7fb069; font-weight: 700; margin-bottom: 5px;'>Hotel (Firefighting)</div>
                <div style='color: #b0c0b0; font-size: 13px;'>Fire suppression, hazmat, thermal operations</div>
            </div>
        </div>
        <div style='margin-top: 20px; padding-top: 20px; border-top: 1px solid #2d5a3d; color: #90b090; font-size: 13px;'>
            <strong>Status Indicators:</strong> Green = Idle at Base > Red = Deployed > Orange = Active Deployment
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- MAIN ROUTING ---
if st.session_state.page == "home":
    show_home_page()
else:
    show_dashboard()
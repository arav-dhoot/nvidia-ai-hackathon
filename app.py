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

# --- PAGE CONFIG ---
st.set_page_config(page_title="AeroGuard | GB10 Edge AI", layout="wide", page_icon="🚁")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp {background-color: #0e1117;}
    h1 {color: #ffffff; font-weight: 800; letter-spacing: -1px;}
    h2 {color: #00ff00; font-family: 'Courier New'; border-bottom: 2px solid #00ff00; padding-bottom: 10px;}
    .card {background-color: #1f2937; padding: 20px; border-radius: 10px; border-left: 5px solid #00ff00; margin-bottom: 20px;}
    .big-font {font-size:20px !important; color: #00ff00; font-family: 'Courier New'; font-weight: bold;}
    .log-entry {font-family: 'Courier New'; color: #e0e0e0; margin-bottom: 5px; border-left: 3px solid #00ff00; padding-left: 10px; font-size: 14px;}
    .stButton>button {width: 100%; border-radius: 5px; font-weight: bold;}
    
    /* VISUAL SEPARATION: THINKING vs COMMAND */
    .thinking-box {
        font-family: 'Courier New'; font-size: 13px; color: #aaaaaa;
        background-color: #111111; padding: 15px; border-radius: 5px;
        border: 1px dashed #444; max-height: 250px; overflow-y: auto;
        margin-bottom: 15px;
    }
    .command-box {
        font-family: 'Courier New'; font-size: 16px; color: #ffffff;
        background-color: #06402b; 
        padding: 15px; border-radius: 5px;
        border: 2px solid #00ff00;
        box-shadow: 0 0 10px #00ff00;
        margin-bottom: 20px;
        font-weight: bold;
    }
    .command-label {
        color: #00ff00; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = "home"
if 'latest_observation' not in st.session_state: st.session_state.latest_observation = "System Ready. Awaiting visual feed..."
if 'command_log' not in st.session_state: st.session_state.command_log = []
if 'hazard_level' not in st.session_state: st.session_state.hazard_level = "UNKNOWN"
if 'processed_frames' not in st.session_state: st.session_state.processed_frames = []
if 'last_thought' not in st.session_state: st.session_state.last_thought = ""
if 'last_command' not in st.session_state: st.session_state.last_command = ""

# --- TELEMETRY ---
def get_gpu_metrics():
    try:
        # Memory
        free, total = torch.cuda.mem_get_info(0)
        used_gb = (total - free) / 1024**3
        total_gb = total / 1024**3
        mem_str = f"{used_gb:.1f} / {total_gb:.1f} GB"
        
        # Utilization (via nvidia-smi)
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], 
            encoding="utf-8"
        )
        load_str = f"{result.strip()}%"
    except:
        load_str = "N/A"; mem_str = "N/A"

    return {
        "load": load_str, "mem": mem_str,
        "name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Simulation Mode"
    }

# --- PDF REPORT ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(80); self.cell(30, 10, 'AeroGuard Mission Report', 0, 0, 'C'); self.ln(20)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | CONFIDENTIAL | GB10 Edge Gateway', 0, 0, 'C')

def generate_pdf_report():
    pdf = PDF(); pdf.add_page(); pdf.set_text_color(0,0,0)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '1. SYSTEM STATUS', 0, 1)
    pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 10, f"Latest Observation: {st.session_state.latest_observation}\nHazard Level: {st.session_state.hazard_level}")
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '2. SQUAD ASSETS', 0, 1)
    pdf.set_font('Arial', '', 10)
    for name, data in backend.SQUADS.items():
        pdf.cell(0, 8, f"- {name} ({data['type']}): {data['status']} @ {data['loc']}", 0, 1)
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '3. LOGS', 0, 1)
    pdf.set_font('Arial', '', 9)
    for log in reversed(st.session_state.command_log): pdf.multi_cell(0, 6, log); pdf.ln(1)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# PAGE 1: HOME PAGE
# ==========================================
def show_home_page():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("🚁 AeroGuard")
        st.caption("AUTONOMOUS INCIDENT COMMANDER // POWERED BY NVIDIA GB10")
        st.markdown("**AeroGuard** is an air-gapped, multi-modal AI agent for disaster response.")
        if st.button("🚀 LAUNCH COMMANDER DASHBOARD", type="primary"):
            st.session_state.page = "dashboard"; st.rerun()
    with col2:
        st.info("System Status: ONLINE\n\nGateway: NVIDIA Grace Blackwell\n\nSecurity: AIR-GAPPED")
        
    st.markdown("---")
    st.header("⚡ Why NVIDIA GB10?")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("<div class='card'><h3>🔗 NVLink-C2C</h3><p>Unified Memory Architecture allows Zero-Copy data transfer between Vision (CPU) and Agent (GPU).</p></div>", unsafe_allow_html=True)
    with c2: st.markdown("<div class='card'><h3>🧠 128GB Unified Memory</h3><p>Running DeepSeek-32B, SAM 2, and CLIP simultaneously in VRAM.</p></div>", unsafe_allow_html=True)
    with c3: st.markdown("<div class='card'><h3>🚀 Tensor Cores</h3><p>Using <code>torch.compile(max-autotune)</code> for accelerated Triton kernels.</p></div>", unsafe_allow_html=True)

# ==========================================
# PAGE 2: DASHBOARD
# ==========================================
def render_dynamic_map():
    nodes = []
    edges = []
    
    # 1. Identify which squad was just activated (Target Lock)
    active_squad_name = None
    if st.session_state.last_command:
        for s_name in backend.SQUADS.keys():
            if s_name in st.session_state.last_command:
                active_squad_name = s_name
                break

    # 2. Base & Target Nodes
    nodes.append(Node(id="Base", label="HQ", size=40, shape="box", color="#00ff00", font={'color': 'white'}))
    
    t_color = "#ff4b4b" if "CRITICAL" in st.session_state.hazard_level else "#ffa500" if "MODERATE" in st.session_state.hazard_level else "#555555"
    nodes.append(Node(id="Sector4", label="Target Sector", size=30, shape="box", color=t_color, font={'color': 'white'}))
    
    # 3. Squad Nodes
    for name, data in backend.SQUADS.items():
        # Default Style
        s_size = 15
        s_color = "#00bfff" if data['type'] == "Ground" else "#e6e6fa" if data['type'] == "Aerial" else "#ff69b4"
        s_label = f"{name}\n({data['type']})"
        
        # HIGHLIGHT IF ACTIVE
        if name == active_squad_name:
            s_size = 35                  
            s_color = "#FFFF00"          # Bright Yellow Pulse
            s_label = f"★ {name} ★" 
        
        nodes.append(Node(id=name, label=s_label, size=s_size, shape="dot", color=s_color, font={'color': 'white'}))
        
        # Edges
        if "Base" in data['loc']:
            edges.append(Edge(source="Base", target=name, label="Idle", color="#555555"))
        elif "Sector 4" in data['loc']:
            # Highlight path
            e_color = "#FFFF00" if name == active_squad_name else "#00ff00"
            e_width = 4 if name == active_squad_name else 1
            edges.append(Edge(source=name, target="Sector4", label="Deployed", color=e_color, width=e_width))
        else:
            edges.append(Edge(source="Base", target=name, label="En Route", color="yellow", dashes=True))

    config = Config(width="100%", height=600, directed=True, physics=True, hierarchical=False, gravity=-2000, springLength=150, nodeHighlightBehavior=True, highlightColor="#F7A7A6", stabilization=True)
    return nodes, edges, config

def show_dashboard():
    # --- SIDEBAR ---
    with st.sidebar:
        if st.button("⬅️ Back"): st.session_state.page = "home"; st.rerun()
        st.header("Hardware Telemetry")
        gpu_stats = get_gpu_metrics()
        c1, c2 = st.columns(2)
        c1.metric("GPU Load", gpu_stats["load"])
        c2.metric("VRAM", gpu_stats["mem"])
        try:
            val = float(gpu_stats["load"].strip('%')) / 100
        except: val = 0.0
        st.progress(val)
        st.caption(f"Device: **{gpu_stats['name']}**")
        
        st.divider()
        st.header("Mission Controls")
        report_pdf = generate_pdf_report()
        st.download_button("📄 Download Report (PDF)", report_pdf, f"Mission_Log_{time.time()}.pdf", "application/pdf")
        st.write("### Squad Assets")
        st.json(backend.SQUADS)

    # --- MAIN UI ---
    col1, col2 = st.columns([1, 4])
    with col1: st.title("🚁 AeroGuard")
    with col2: st.caption("LIVE OPERATIONS DASHBOARD")

    row1_col1, row1_col2 = st.columns([3, 2])

    # LEFT: VISION LOOP
    with row1_col1:
        st.subheader("📡 Live Drone Feed")
        uploaded_file = st.file_uploader("Inject Drone Feed (MP4)", type=['mp4', 'mov'])
        display_slot = st.empty()
        stats_slot = st.empty()
        
        if uploaded_file and st.button("▶️ START HAZARD SCAN"):
            # RESET EVERYTHING
            st.session_state.processed_frames = []
            
            # FIX: Ensure file is read from start and file is closed properly
            uploaded_file.seek(0) 
            tfile = tempfile.NamedTemporaryFile(delete=False) 
            tfile.write(uploaded_file.read())
            tfile.close() # CRITICAL: Close before OpenCV opens it
            
            cap = cv2.VideoCapture(tfile.name)
            frame_count = 0; SKIP_RATE = 25 
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                frame_count += 1
                if frame_count % SKIP_RATE != 0: continue 
                
                _, buffer = cv2.imencode('.jpg', frame)
                processed_img_bytes, stats = vision.process_frame_realtime(buffer.tobytes())
                
                if processed_img_bytes:
                    st.session_state.processed_frames.append(processed_img_bytes)
                    # LIVE UPDATE
                    display_slot.image(processed_img_bytes, caption="Real-Time SAM 2 Segmentation", use_container_width=True)
                    
                    hazard = stats['hazard_type'].upper(); coverage = stats['coverage_pct']
                    tag_color = "red" if coverage > 20 else "green"
                    stats_slot.markdown(f"### DETECTED: <span style='color:{tag_color}'>{hazard}</span>\n**Coverage:** {coverage}% of Sector | **Segments:** {stats['mask_count']}", unsafe_allow_html=True)
                    
                    severity = "CRITICAL" if coverage > 40 else "MODERATE" if coverage > 15 else "MINOR"
                    st.session_state.hazard_level = severity 
                    st.session_state.latest_observation = f"Visual Scan: {hazard}. Coverage: {coverage}%. Severity: {severity}. Active Masks: {stats['mask_count']}."
            cap.release()
            st.success("Scan Complete.")

        if st.session_state.processed_frames:
            with st.expander("📂 Mission Gallery", expanded=False):
                cols = st.columns(4)
                for idx, img_bytes in enumerate(st.session_state.processed_frames):
                    with cols[idx % 4]: st.image(img_bytes, caption=f"Frame {idx*5}", use_container_width=True)

    # RIGHT: AGENT REASONING
    with row1_col2:
        st.subheader("🧠 Commander Logic")
        st.info(f"Inbound Data: {st.session_state.latest_observation}")
        
        if st.button("EXECUTE COMMAND PROTOCOL", type="primary"):
            timestamp = time.strftime("%H:%M:%S")
            
            think_placeholder = st.empty()
            cmd_placeholder = st.empty()
            full_thinking = ""; full_command = ""
            
            # STREAMING
            for chunk in backend.stream_commander(st.session_state.latest_observation):
                if chunk["type"] == "thinking":
                    full_thinking += chunk["content"]
                    think_placeholder.markdown(f"<div class='thinking-box'><b>DEEPSEEK REASONING:</b><br>{full_thinking}▌</div>", unsafe_allow_html=True)
                elif chunk["type"] == "answer":
                    full_command += chunk["content"]
                    cmd_placeholder.markdown(f"""<div class='command-box'><div class='command-label'>Incoming Transmission</div>{full_command}▌</div>""", unsafe_allow_html=True)

            # SAVE STATE
            st.session_state.last_thought = full_thinking
            st.session_state.last_command = full_command
            st.session_state.command_log.insert(0, f"[{timestamp}] {full_command}")
            st.rerun()

        # PERSISTENT DISPLAY
        if st.session_state.last_thought:
            with st.expander("👁️‍🗨️ Last Neural Chain of Thought", expanded=False):
                st.markdown(f"<div class='thinking-box'>{st.session_state.last_thought}</div>", unsafe_allow_html=True)
        
        if st.session_state.last_command:
            st.markdown(f"""<div class='command-box'><div class='command-label'>COMMAND AUTHORIZED</div>{st.session_state.last_command}</div>""", unsafe_allow_html=True)

        log_container = st.container(height=200)
        with log_container:
            for log_entry in st.session_state.command_log:
                color = "#00ff00" if "Deploy" in log_entry else "#e0e0e0"
                st.markdown(f"<div class='log-entry' style='color: {color}; border-left: 3px solid {color}'>{log_entry}</div>", unsafe_allow_html=True)

    # BOTTOM: MAP
    st.subheader("📍 Live Tactical Digital Twin")
    nodes, edges, config = render_dynamic_map()
    agraph(nodes=nodes, edges=edges, config=config)

if st.session_state.page == "home":
    show_home_page()
else:
    show_dashboard()
import streamlit as st
import time
import backend
import vision
import cv2
import tempfile
import base64

# --- PAGE CONFIG ---
st.set_page_config(page_title="AeroGuard | GB10 Edge AI", layout="wide", page_icon="🚁")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Global Dark Mode Fixes */
    .stApp {background-color: #0e1117;}
    
    /* Typography */
    h1 {color: #ffffff; font-weight: 800; letter-spacing: -1px;}
    h2 {color: #00ff00; font-family: 'Courier New'; border-bottom: 2px solid #00ff00; padding-bottom: 10px;}
    h3 {color: #e0e0e0;}
    
    /* Custom Card Styling for the Home Page */
    .card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00ff00;
        margin-bottom: 20px;
    }
    
    /* Dashboard Specifics */
    .big-font {font-size:20px !important; color: #00ff00; font-family: 'Courier New'; font-weight: bold;}
    .log-entry {font-family: 'Courier New'; color: #e0e0e0; margin-bottom: 10px; border-left: 3px solid #00ff00; padding-left: 10px;}
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'latest_observation' not in st.session_state:
    st.session_state.latest_observation = "System Ready. Waiting for Visual Scan..."
if 'command_log' not in st.session_state:
    st.session_state.command_log = []

# ==========================================
# PAGE 1: THE LANDING PAGE (PITCH DECK)
# ==========================================
def show_home_page():
    # Hero Section
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("🚁 AeroGuard")
        st.caption("AUTONOMOUS INCIDENT COMMANDER // POWERED BY NVIDIA GB10")
        st.markdown("""
        **AeroGuard** is an air-gapped, multi-modal AI agent designed for disaster zones where internet is non-existent. 
        It ingests drone feeds, performs real-time segmentation, and orchestrates rescue squads using autonomous reasoning.
        """)
        
        if st.button("🚀 LAUNCH COMMANDER DASHBOARD", type="primary"):
            st.session_state.page = "dashboard"
            st.rerun()

    with col2:
        # A placeholder for a cool logo or architecture diagram if you had one
        st.info("System Status: ONLINE\n\nGateway: NVIDIA Grace Blackwell\n\nSecurity: AIR-GAPPED")

    st.markdown("---")

    # WHY GB10 SECTION
    st.header("⚡ The GB10 Advantage")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="card">
        <h3>🧠 Massive Unified Memory</h3>
        <p>Running <b>DeepSeek-32B</b> (Reasoning), <b>SAM 2</b> (Segmentation), and <b>CLIP</b> (Vision) simultaneously requires massive VRAM. The GB10's <b>128GB Unified Memory</b> allows zero-copy data sharing between the Grace CPU and Blackwell GPU, enabling this pipeline to run entirely on the edge.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown("""
        <div class="card">
        <h3>🚀 Real-Time Transformer Compute</h3>
        <p>AeroGuard processes video at <b>high FPS</b> by leveraging the Blackwell Tensor Cores. We perform frame-by-frame hazard mapping (SAM 2) while asynchronously running chain-of-thought reasoning (DeepSeek), a feat impossible on standard edge hardware.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown("""
        <div class="card">
        <h3>🛡️ Air-Gapped Security</h3>
        <p>Disaster zones and military operations cannot rely on the cloud. By hosting the <b>entire stack locally</b> on the GB10, AeroGuard ensures zero data leakage and 100% uptime even when the grid goes down.</p>
        </div>
        """, unsafe_allow_html=True)

    # JUDGING CRITERIA MAPPING
    st.markdown("---")
    st.header("🏆 Alignment with Hackathon Goals")
    
    st.markdown("""
    | Criteria | How AeroGuard Wins |
    | :--- | :--- |
    | **Technical Merit** | Implements a complex **Multi-Modal Pipeline** (Video -> CLIP -> SAM 2 -> LLM Agent) fully locally. |
    | **Innovation** | Moves beyond simple object detection to **Semantic Reasoning**. It doesn't just see "water"; it calculates flood coverage % and reasons about logistics. |
    | **Impact & Relevance** | Solves a critical "Day 0" disaster problem: coordinating chaos when communication lines are dead. |
    | **Execution** | A fully functional, end-to-end dashboard with real-time video processing and agentic feedback loops. |
    | **Presentation** | Visually immersive UI demonstrating clear "Sense -> Think -> Act" loop. |
    """)

# ==========================================
# PAGE 2: THE COMMANDER DASHBOARD (APP)
# ==========================================
def show_dashboard():
    # Sidebar Navigation Back
    with st.sidebar:
        if st.button("⬅️ Back to Mission Brief"):
            st.session_state.page = "home"
            st.rerun()
        st.header("System Status")
        st.metric(label="GPU", value="Optimized (Mixed Precision)", delta="Active")
        st.write("### Squad Assets")
        st.json(backend.SQUADS)

    # Header
    col1, col2 = st.columns([1, 4])
    with col1: st.title("🚁 AeroGuard")
    with col2: st.caption("LIVE OPERATIONS DASHBOARD")

    # Main Layout
    row1_col1, row1_col2 = st.columns([3, 2])

    # LEFT: Real-Time Vision Loop
    with row1_col1:
        st.subheader("📡 Live Drone Feed")
        uploaded_file = st.file_uploader("Inject Drone Feed (MP4)", type=['mp4', 'mov'])
        
        display_slot = st.empty()
        stats_slot = st.empty()
        
        if uploaded_file and st.button("▶️ START HAZARD SCAN"):
            tfile = tempfile.NamedTemporaryFile(delete=False) 
            tfile.write(uploaded_file.read())
            cap = cv2.VideoCapture(tfile.name)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                # 1. Encode & Send
                _, buffer = cv2.imencode('.jpg', frame)
                processed_img_bytes, stats = vision.process_frame_realtime(buffer.tobytes())
                
                if processed_img_bytes:
                    # 2. Update Visuals
                    display_slot.image(processed_img_bytes, caption="Real-Time SAM 2 Segmentation", use_container_width=True)
                    
                    # 3. Parse Stats
                    hazard = stats['hazard_type'].upper()
                    coverage = stats['coverage_pct']
                    
                    # 4. Color Code the Hazard
                    tag_color = "red" if coverage > 20 else "green"
                    stats_slot.markdown(
                        f"""
                        ### DETECTED: <span style='color:{tag_color}'>{hazard}</span>
                        **Coverage:** {coverage}% of Sector | **Segments:** {stats['mask_count']}
                        """, unsafe_allow_html=True
                    )
                    
                    # 5. Construct Agent Memory
                    severity = "CRITICAL" if coverage > 40 else "MODERATE" if coverage > 15 else "MINOR"
                    
                    st.session_state.latest_observation = (
                        f"Visual Scan Report: Detected {hazard}."
                        f" The hazard covers {coverage}% of the visible area ({severity} severity)."
                        f" SAM 2 identified {stats['mask_count']} distinct regions."
                    )

            cap.release()

    # RIGHT: Agent Reasoning
    with row1_col2:
        st.subheader("🧠 Commander Logic")
        st.info(f"Current Vision Data: {st.session_state.latest_observation}")
        
        if st.button("EXECUTE COMMAND", type="primary"):
            with st.spinner("DeepSeek Reasoning..."):
                decision = backend.run_commander(st.session_state.latest_observation)
                
                timestamp = time.strftime("%H:%M:%S")
                st.session_state.command_log.insert(0, f"[{timestamp}] {decision}")

        # Persistent Log
        log_container = st.container(height=400)
        with log_container:
            if not st.session_state.command_log:
                st.write("No commands issued yet.")
            else:
                for log_entry in st.session_state.command_log:
                    if "SUCCESS" in log_entry: color = "#00ff00"
                    elif "CRITICAL" in log_entry: color = "#ff4b4b"
                    else: color = "#e0e0e0"
                    
                    st.markdown(f"<div class='log-entry' style='color: {color}; border-left: 3px solid {color}'>{log_entry}</div>", unsafe_allow_html=True)
    
    # Map Visualization
    st.subheader("📍 Tactical Map")
    st.graphviz_chart("""
        digraph {
            rankdir=LR;
            bgcolor="#0e1117";
            node [shape=box style=filled fillcolor="#262730" fontcolor=white fontname="Courier"];
            edge [color=white];
            
            Base [fillcolor="#00ff00" fontcolor=black];
            Sector4 [fillcolor="#ff4b4b" label="Sector 4 (TARGET)"];
            Sector9;
            
            Base -> Sector1 [label="Open"];
            Base -> Sector4 [label="HAZARD CHECK" color="yellow" style="dashed"];
            Base -> Sector9 [label="Open"];
        }
    """)

# ==========================================
# MAIN APP ROUTER
# ==========================================
if st.session_state.page == "home":
    show_home_page()
else:
    show_dashboard()
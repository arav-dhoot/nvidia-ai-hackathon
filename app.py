import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
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
if 'hazard_level' not in st.session_state:
    st.session_state.hazard_level = "UNKNOWN"

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
        st.info("System Status: ONLINE\n\nGateway: NVIDIA Grace Blackwell\n\nSecurity: AIR-GAPPED")

    st.markdown("---")

    # WHY GB10 SECTION
    st.header("⚡ The GB10 Advantage")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="card">
        <h3>🧠 Massive Unified Memory</h3>
        <p>Running <b>DeepSeek-32B</b> (Reasoning), <b>SAM 2</b> (Segmentation), and <b>CLIP</b> (Vision) simultaneously requires massive VRAM. The GB10's <b>128GB Unified Memory</b> allows zero-copy data sharing between the Grace CPU and Blackwell GPU.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown("""
        <div class="card">
        <h3>🚀 Real-Time Transformer Compute</h3>
        <p>AeroGuard processes video at <b>high FPS</b> by leveraging the Blackwell Tensor Cores and <code>torch.compile</code>. We perform frame-by-frame hazard mapping while asynchronously running chain-of-thought reasoning.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown("""
        <div class="card">
        <h3>🛡️ Air-Gapped Security</h3>
        <p>Disaster zones and military operations cannot rely on the cloud. By hosting the <b>entire stack locally</b> on the GB10, AeroGuard ensures zero data leakage and 100% uptime.</p>
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
    | **Impact** | Solves a critical "Day 0" disaster problem: coordinating chaos when communication lines are dead. |
    | **Execution** | A fully functional, end-to-end dashboard with real-time video processing and agentic feedback loops. |
    """)

# ==========================================
# PAGE 2: THE COMMANDER DASHBOARD (APP)
# ==========================================
def render_dynamic_map():
    """Generates the Agraph nodes/edges based on CURRENT Live State"""
    
    nodes = []
    edges = []
    
    # 1. FIXED NODES (Base & Target)
    nodes.append(Node(id="Base", label="HQ (Base)", size=30, shape="box", color="#00ff00", font={'color': 'white'}))
    
    # Target Sector Color depends on Vision!
    target_color = "#ff4b4b" if st.session_state.hazard_level == "CRITICAL" else "#ffa500" if st.session_state.hazard_level == "MODERATE" else "#808080"
    nodes.append(Node(id="Sector4", label="Sector 4\n(Target)", size=30, shape="box", color=target_color, font={'color': 'white'}))
    
    # 2. DYNAMIC SQUAD NODES
    # We read the backend.SQUADS dict which the Agent modifies!
    for name, data in backend.SQUADS.items():
        # Squad Color
        s_color = "#00bfff" if data['type'] == "Ground" else "#e6e6fa" if data['type'] == "Aerial" else "#ff69b4"
        
        # Create Node
        nodes.append(Node(id=name, label=f"{name}\n({data['type']})", size=15, shape="dot", color=s_color, font={'color': 'white'}))
        
        # Create Edge based on Location
        if "Base" in data['loc']:
            edges.append(Edge(source="Base", target=name, label="Idle", color="#555555"))
        elif "Sector 4" in data['loc']:
            edges.append(Edge(source=name, target="Sector4", label="Deployed", color="#00ff00", dashes=False))
        else:
            # Traveling or elsewhere
            edges.append(Edge(source="Base", target=name, label="En Route", color="yellow", dashes=True))

    # Config (Stabilization True avoids endless spinning)
    config = Config(width="100%", height=500, directed=True, 
                   physics=True, hierarchical=False, 
                   nodeHighlightBehavior=True, highlightColor="#F7A7A6",
                   stabilization=True)
                   
    return nodes, edges, config

def show_dashboard():
    # Sidebar
    with st.sidebar:
        if st.button("⬅️ Back to Mission Brief"):
            st.session_state.page = "home"
            st.rerun()
        st.header("System Status")
        st.metric(label="GPU", value="NVIDIA Blackwell GB10", delta="Active")
        st.write("### Squad Assets")
        st.json(backend.SQUADS) # This updates live when Agent moves squads!

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
            
            frame_count = 0
            SKIP_RATE = 30 # PROCESS ONLY 1 IN 5 FRAMES
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                frame_count += 1
                if frame_count % SKIP_RATE != 0: continue 
                
                # Resize before sending? Optional. Let server handle it.
                _, buffer = cv2.imencode('.jpg', frame)
                processed_img_bytes, stats = vision.process_frame_realtime(buffer.tobytes())
                
                if processed_img_bytes:
                    display_slot.image(processed_img_bytes, caption="Real-Time SAM 2 Segmentation", use_container_width=True)
                    
                    hazard = stats['hazard_type'].upper()
                    coverage = stats['coverage_pct']
                    
                    tag_color = "red" if coverage > 20 else "green"
                    stats_slot.markdown(
                        f"""
                        ### DETECTED: <span style='color:{tag_color}'>{hazard}</span>
                        **Coverage:** {coverage}% of Sector | **Segments:** {stats['mask_count']}
                        """, unsafe_allow_html=True
                    )
                    
                    # UPDATE STATE FOR AGENT & MAP
                    severity = "CRITICAL" if coverage > 40 else "MODERATE" if coverage > 15 else "MINOR"
                    st.session_state.hazard_level = severity 
                    
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
                # The Agent logic modifies backend.SQUADS inside this function!
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
                    color = "#00ff00" if "SUCCESS" in log_entry else "#ff4b4b" if "CRITICAL" in log_entry else "#e0e0e0"
                    st.markdown(f"<div class='log-entry' style='color: {color}; border-left: 3px solid {color}'>{log_entry}</div>", unsafe_allow_html=True)
    
    # BOTTOM: Dynamic Map
    st.subheader("📍 Live Tactical Digital Twin")
    
    # Generate the map based on current Squad locations and Hazard Levels
    nodes, edges, config = render_dynamic_map()
    
    # Draw
    agraph(nodes=nodes, edges=edges, config=config)

# ==========================================
# MAIN APP ROUTER
# ==========================================
if st.session_state.page == "home":
    show_home_page()
else:
    show_dashboard()
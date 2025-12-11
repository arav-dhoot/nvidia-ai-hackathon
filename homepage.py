"""
AeroGuard Homepage Module
Comprehensive landing page for the AeroGuard disaster response system
"""

import streamlit as st
import os
import base64

def get_img_as_base64(file_path):
    if not os.path.exists(file_path): return "" # Return empty if not found
    with open(file_path, "rb") as f: data = f.read()
    return base64.b64encode(data).decode()

img1_b64 = get_img_as_base64("images/1.jpeg")
img2_b64 = get_img_as_base64("images/2.jpeg")
img3_b64 = get_img_as_base64("images/3.jpeg")


def render_homepage():
    """
    Renders the complete AeroGuard homepage with enhanced visuals and content.
    Call this function from app.py to display the homepage.
    """
    
    # Custom CSS for homepage
    st.markdown("""
    <style>
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #0a1f0a 0%, #1a4d2e 50%, #0a1f0a 100%);
        padding: 60px 40px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 40px;
        border: 2px solid #2d5a2d;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        position: relative;
        overflow: hidden;
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(125,255,125,0.03) 0%, transparent 70%);
        animation: pulse 8s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.6; }
    }
    
    .hero-title {
        font-size: 56px;
        font-weight: 900;
        color: #7fff00;
        margin-bottom: 15px;
        text-shadow: 0 0 20px rgba(127,255,0,0.5);
        letter-spacing: -1px;
        position: relative;
        z-index: 1;
    }
    
    .hero-subtitle {
        font-size: 22px;
        color: #b0e0b0;
        margin-bottom: 10px;
        font-weight: 300;
        letter-spacing: 1px;
        position: relative;
        z-index: 1;
    }
    
    .hero-description {
        font-size: 16px;
        color: #90c090;
        max-width: 800px;
        margin: 0 auto 30px;
        line-height: 1.8;
        position: relative;
        z-index: 1;
    }
    
    /* Feature Cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 25px;
        margin: 40px 0;
    }
    
    .feature-card {
        background: linear-gradient(145deg, #1a3a2a 0%, #0f2419 100%);
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #2d5a3d;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        border-color: #4a8a5a;
        box-shadow: 0 8px 25px rgba(74,138,90,0.3);
    }
    
    .feature-icon {
        font-size: 48px;
        margin-bottom: 15px;
        display: block;
    }
    
    .feature-title {
        font-size: 22px;
        font-weight: 700;
        color: #7fb069;
        margin-bottom: 12px;
    }
    
    .feature-description {
        font-size: 15px;
        color: #b0c0b0;
        line-height: 1.7;
    }
    
    /* Tech Specs Section */
    .tech-section {
        background: rgba(20, 40, 25, 0.6);
        padding: 40px;
        border-radius: 12px;
        margin: 40px 0;
        border: 1px solid #2d5a3d;
    }
    
    .section-title {
        font-size: 32px;
        font-weight: 800;
        color: #7fff00;
        margin-bottom: 25px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .spec-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-top: 30px;
    }
    
    .spec-item {
        background: rgba(30, 50, 35, 0.5);
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #4a8a5a;
    }
    
    .spec-label {
        font-size: 13px;
        color: #7fb069;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .spec-value {
        font-size: 20px;
        color: #d0e0d0;
        font-weight: 700;
    }
    
    .spec-detail {
        font-size: 13px;
        color: #90b090;
        margin-top: 5px;
    }
    
    /* Architecture Diagram */
    .architecture-box {
        background: linear-gradient(135deg, #0f1f15 0%, #1a2f25 100%);
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #3d6d4d;
        margin: 30px 0;
    }
    
    .arch-component {
        background: rgba(40, 70, 50, 0.4);
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
        border: 1px solid #4a7a5a;
    }
    
    .arch-component-title {
        font-size: 18px;
        font-weight: 700;
        color: #7fb069;
        margin-bottom: 10px;
    }
    
    .arch-component-desc {
        font-size: 14px;
        color: #b0c0b0;
        line-height: 1.6;
    }
    
    /* CTA Button */
    .cta-container {
        text-align: center;
        margin: 50px 0 30px;
    }
    
    .launch-button {
        background: linear-gradient(135deg, #4a8a5a 0%, #357045 100%);
        color: white;
        padding: 18px 50px;
        font-size: 20px;
        font-weight: 700;
        border: 2px solid #5a9a6a;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: 0 4px 15px rgba(74,138,90,0.4);
    }
    
    .launch-button:hover {
        background: linear-gradient(135deg, #5a9a6a 0%, #458055 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(74,138,90,0.6);
    }
    
    /* Stats Bar */
    .stats-bar {
        display: flex;
        justify-content: space-around;
        margin: 40px 0;
        padding: 30px;
        background: rgba(20, 40, 25, 0.4);
        border-radius: 10px;
        border: 1px solid #2d5a3d;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-number {
        font-size: 42px;
        font-weight: 900;
        color: #7fff00;
        display: block;
        margin-bottom: 8px;
    }
    
    .stat-label {
        font-size: 14px;
        color: #90b090;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Use Cases */
    .use-case {
        background: linear-gradient(90deg, rgba(26,58,42,0.6) 0%, rgba(15,36,25,0.3) 100%);
        padding: 25px 30px;
        border-radius: 10px;
        margin: 20px 0;
        border-left: 5px solid #4a8a5a;
    }
    
    .use-case-title {
        font-size: 20px;
        font-weight: 700;
        color: #7fb069;
        margin-bottom: 12px;
    }
    
    .use-case-desc {
        font-size: 15px;
        color: #b0c0b0;
        line-height: 1.7;
    }
    
    /* Security Badge */
    .security-badge {
        display: inline-block;
        background: rgba(139, 0, 0, 0.2);
        color: #ff6b6b;
        padding: 8px 20px;
        border-radius: 20px;
        border: 1px solid #8b0000;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 1px;
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">⚡ AeroGuard</div>
        <div class="hero-subtitle">AUTONOMOUS DISASTER RESPONSE COMMANDER</div>
        <div class="hero-description">
            Next-generation AI agent for real-time disaster response coordination. 
            Powered by NVIDIA Grace Blackwell GB10, AeroGuard autonomously analyzes drone footage, 
            assesses hazards, and deploys specialized rescue squads with millisecond precision.
        </div>
        <span class="security-badge">🔒 AIR-GAPPED • SECURE • EDGE-DEPLOYED</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats Bar
    st.markdown("""
    <div class="stats-bar">
        <div class="stat-item">
            <span class="stat-number">&lt;100ms</span>
            <span class="stat-label">Inference Latency</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">8</span>
            <span class="stat-label">Specialized Squads</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">128GB</span>
            <span class="stat-label">Unified Memory</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">100%</span>
            <span class="stat-label">Autonomous</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Core Features
    st.markdown('<div class="section-title">Core Capabilities</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <span class="feature-icon">👁️</span>
            <div class="feature-title">Real-Time Vision Analysis</div>
            <div class="feature-description">
                SAM 2 segmentation processes drone footage at 30 FPS, identifying floods, fires, 
                rubble, and infrastructure damage with pixel-level precision. CLIP-based classification 
                determines hazard types and severity levels autonomously.
            </div>
        </div>
        
    <div class="feature-card">
            <span class="feature-icon">🧠</span>
            <div class="feature-title">Chain-of-Thought Reasoning</div>
            <div class="feature-description">
                DeepSeek R1 generates transparent reasoning chains, evaluating squad capabilities, 
                equipment needs, and tactical priorities. Every deployment decision is auditable 
                with full CoT transparency.
            </div>
        </div>
        
        
    <div class="feature-card">
            <span class="feature-icon">🔒</span>
            <div class="feature-title">Air-Gapped Security</div>
            <div class="feature-description">
                Runs entirely on edge hardware with zero cloud dependencies. All inference, vision 
                processing, and decision-making occurs on-device. Perfect for military, disaster zones, 
                and sensitive operations requiring complete data sovereignty.
            </div>
        </div>
        
    <div class="feature-card">
            <span class="feature-icon">⚡</span>
            <div class="feature-title">Unified Memory Architecture</div>
            <div class="feature-description">
                NVLink-C2C enables zero-copy data transfer between CPU (vision processing) and GPU 
                (LLM inference). Eliminates PCIe bottlenecks, enabling 3 concurrent AI models 
                in 128GB shared memory space.
            </div>
        </div>
        
    <div class="feature-card">
            <span class="feature-icon">📊</span>
            <div class="feature-title">Mission Reporting</div>
            <div class="feature-description">
                Automatically generates comprehensive PDF mission reports with squad status, deployment 
                logs, hazard assessments, and command decisions. Full audit trail for post-mission 
                analysis and compliance documentation.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # System Architecture
    st.markdown('<div class="section-title">System Architecture</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="architecture-box">
    <div class="arch-component">
            <div class="arch-component-title">📹 Vision Pipeline (CPU - Grace)</div>
            <div class="arch-component-desc">
                <strong>Input:</strong> Drone video feed (MP4/MOV) → <strong>Processing:</strong> Frame extraction, 
                SAM 2 segmentation, CLIP classification → <strong>Output:</strong> Hazard type, coverage percentage, 
                severity level, annotated frames
            </div>
        </div>
        
    <div class="arch-component">
            <div class="arch-component-title">🧠 Reasoning Engine (GPU - Blackwell)</div>
            <div class="arch-component-desc">
                <strong>Input:</strong> Hazard report + squad status → <strong>Processing:</strong> DeepSeek R1 
                chain-of-thought reasoning → <strong>Output:</strong> Structured JSON command (squad selection, 
                location, tactical reasoning)
            </div>
        </div>
        
    <div class="arch-component">
            <div class="arch-component-title">🗺️ Command & Control (CPU - Grace)</div>
            <div class="arch-component-desc">
                <strong>Input:</strong> Deployment commands → <strong>Processing:</strong> State management, 
                tactical map rendering, mission logging → <strong>Output:</strong> Live operational dashboard, 
                PDF reports, squad tracking
            </div>
        </div>
        
    <div class="arch-component">
            <div class="arch-component-title">⚡ NVLink-C2C Interconnect</div>
            <div class="arch-component-desc">
                <strong>Zero-copy data transfer:</strong> Vision pipeline output (CPU) directly accessible by 
                reasoning engine (GPU) without memory duplication. SAM 2 masks and CLIP embeddings remain in 
                shared 128GB memory space throughout inference pipeline.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Use Cases
    st.markdown('<div class="section-title">Mission Scenarios</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="use-case">
            <div class="use-case-title">🌊 Flood Response</div>
            <div class="use-case-desc">
                Drone surveys inundated region → SAM 2 detects 45% water coverage → CLIP classifies as flood → 
                DeepSeek R1 reasons: "Echo squad has lifeboats and swift water training" → Autonomous deployment 
                to impact zone with rescue equipment manifest
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="use-case">
            <div class="use-case-title">🔥 Wildfire Containment</div>
            <div class="use-case-desc">
                Aerial reconnaissance identifies fire perimeter → CLIP detects "raging fire and smoke" → 
                System assesses Hotel (firefighting) squad as busy → Deploys Bravo (aerial) for reconnaissance 
                and Delta (engineering) for firebreak construction
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="use-case">
            <div class="use-case-title">🏚️ Urban Search & Rescue</div>
            <div class="use-case-desc">
                Building collapse detected via segmentation → SAM 2 identifies rubble patterns → DeepSeek reasons: 
                "Delta has excavation equipment, Charlie has medical triage capability" → Dual deployment with 
                coordinated extraction and treatment protocols
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="use-case">
            <div class="use-case-title">⚠️ Infrastructure Assessment</div>
            <div class="use-case-desc">
                Post-earthquake damage survey → Computer vision identifies blocked roads, compromised bridges → 
                Golf (recon) deployed for intelligence gathering → Delta (engineering) follows for structural 
                assessment and emergency repairs
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Technical Advantages
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="tech-section" style="height: 100%;">
            <h3 style="color: #7fb069; margin-bottom: 20px;">Why GB10 Edge AI?</h3>
            <ul style="color: #b0c0b0; line-height: 2.0; font-size: 15px;">
                <li><strong>Zero Latency Overhead:</strong> NVLink-C2C eliminates PCIe data transfer delays</li>
                <li><strong>Model Colocation:</strong> Run DeepSeek-32B, SAM 2, and CLIP simultaneously</li>
                <li><strong>Offline Operation:</strong> No cloud dependency for sensitive operations</li>
                <li><strong>Real-Time Inference:</strong> Sub-100ms end-to-end latency for critical decisions</li>
                <li><strong>Power Efficiency:</strong> 500W total system power vs. 1kW+ for discrete systems</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="tech-section" style="height: 100%;">
            <h3 style="color: #7fb069; margin-bottom: 20px;">Key Optimizations</h3>
            <ul style="color: #b0c0b0; line-height: 2.0; font-size: 15px;">
                <li><strong>torch.compile():</strong> Triton kernel fusion for SAM 2 encoder</li>
                <li><strong>BF16/FP8 Quantization:</strong> 2x memory efficiency for DeepSeek R1</li>
                <li><strong>Prefix Caching:</strong> System prompt reuse across inferences</li>
                <li><strong>Chunked Prefill:</strong> Reduces time-to-first-token for streaming</li>
                <li><strong>Batched Inference:</strong> Process multiple frames in parallel</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Visual Showcase Section - Placeholder for Images
    st.markdown('<div class="section-title" style="margin-top: 60px;">System in Action</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    /* Note: CSS braces are doubled {{ }} because this is a Python f-string */
    .showcase-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 30px;
        margin: 40px 0;
    }}

    .showcase-item {{
        background: linear-gradient(145deg, #1a3a2a 0%, #0f2419 100%);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #2d5a3d;
        transition: all 0.3s ease;
    }}

    .showcase-item:hover {{
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(74,138,90,0.4);
        border-color: #4a8a5a;
    }}

    /* Updated container for the image */
    .showcase-image-container {{
        width: 100%;
        height: 240px;
        background: #0a1f0a;
        border-bottom: 1px solid #2d5a3d;
        overflow: hidden; /* Ensures image doesn't spill out */
    }}

    /* The actual image style */
    .showcase-img {{
        width: 100%;
        height: 100%;
        object-fit: cover; /* Ensures image fills the box without stretching */
        display: block;
    }}

    .showcase-content {{
        padding: 25px;
    }}

    .showcase-title {{
        font-size: 20px;
        font-weight: 700;
        color: #7fb069;
        margin-bottom: 12px;
    }}

    .showcase-description {{
        font-size: 14px;
        color: #b0c0b0;
        line-height: 1.7;
    }}
    </style>

    <div class="showcase-grid">
        <div class="showcase-item">
            <div class="showcase-image-container">
                <img src="data:image/jpeg;base64,{img1_b64}" class="showcase-img" alt="Vision Analysis">
            </div>
            <div class="showcase-content">
                <div class="showcase-title">Real-Time Vision Analysis</div>
                <div class="showcase-description">
                    SAM 2 segmentation identifying flood zones with pixel-level precision. 
                    Annotated drone footage showing coverage percentages and hazard classifications 
                    processed at 30 FPS on GB10 hardware.
                </div>
            </div>
        </div>
        
    <div class="showcase-item">
            <div class="showcase-image-container">
                <img src="data:image/jpeg;base64,{img2_b64}" class="showcase-img" alt="Tactical Dashboard">
            </div>
            <div class="showcase-content">
                <div class="showcase-title">Tactical Command Dashboard</div>
                <div class="showcase-description">
                    Live operational map displaying squad positions, deployment status, and impact zones. 
                    Real-time state management with chain-of-thought reasoning shown alongside 
                    autonomous deployment decisions.
                </div>
            </div>
        </div>
        
    <div class="showcase-item">
            <div class="showcase-image-container">
                <img src="data:image/jpeg;base64,{img3_b64}" class="showcase-img" alt="Inference Pipeline">
            </div>
            <div class="showcase-content">
                <div class="showcase-title">Multi-Model Inference Pipeline</div>
                <div class="showcase-description">
                    DeepSeek R1 generating structured JSON commands while SAM 2 and CLIP run 
                    concurrently in unified memory. NVLink-C2C enabling zero-copy data sharing 
                    between CPU vision processing and GPU inference.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA
    st.markdown('<div class="cta-container">', unsafe_allow_html=True)
    if st.button("🚀 LAUNCH COMMANDER DASHBOARD", key="cta_button", type="primary", use_container_width=False):
        st.session_state.page = "dashboard"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer Info
    st.markdown("""
    <div style="text-align: center; margin-top: 60px; padding: 30px; 
                background: rgba(20,40,25,0.3); border-radius: 10px; border: 1px solid #2d5a3d;">
        <p style="color: #7fb069; font-size: 14px; margin-bottom: 10px;">
            <strong>AeroGuard</strong> is a demonstration of edge AI capabilities for disaster response coordination.
        </p>
        <p style="color: #90b090; font-size: 13px; line-height: 1.8;">
            Built with NVIDIA Grace Blackwell GB10 • DeepSeek R1 Reasoning • SAM 2 Segmentation • CLIP Vision<br>
            Designed for air-gapped deployment in critical infrastructure, military operations, and disaster zones
        </p>
    </div>
    """, unsafe_allow_html=True)

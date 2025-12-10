import os
from openai import OpenAI

# --- CONFIGURATION ---
# Point to the local vLLM server
VLLM_API_URL = "http://localhost:8000/v1"
MODEL_NAME = "deepseek-reasoner"
API_KEY = "EMPTY" 

# Initialize OpenAI Client pointing to local vLLM
client = OpenAI(base_url=VLLM_API_URL, api_key=API_KEY)

# --- EXPANDED SQUAD ROSTER ---
SQUADS = {
    "Alpha": {"status": "Idle", "type": "Ground", "loc": "Base", "capacity": 10, "equipment": ["Rations", "Medical Kit"]},
    "Bravo": {"status": "Idle", "type": "Aerial", "loc": "Base", "capacity": 5, "equipment": ["Surveillance Drone", "Radio"]},
    "Charlie": {"status": "Busy",  "type": "Medical", "loc": "Sector 9", "capacity": 8, "equipment": ["Stretcher", "First Aid"]},
    "Delta": {"status": "Idle", "type": "Engineering", "loc": "Base", "capacity": 6, "equipment": ["Toolbox", "Generator"]},
    "Echo": {"status": "Idle", "type": "Rescue", "loc": "Base", "capacity": 12, "equipment": ["Ropes", "Lifeboat"]},
    "Foxtrot": {"status": "Idle", "type": "Logistics", "loc": "Base", "capacity": 15, "equipment": ["Supplies", "Fuel"]},
    "Golf": {"status": "Idle", "type": "Recon", "loc": "Base", "capacity": 4, "equipment": ["Binoculars", "Map"]},
    "Hotel": {"status": "Busy", "type": "Firefighting", "loc": "Sector 3", "capacity": 10, "equipment": ["Hose", "Extinguisher"]}
}

# --- COMMANDER PERSONALITY & LOGIC ---
SYSTEM_PROMPT = """
You are AeroGuard Commander, an autonomous AI responsible for disaster response logistics.
Your goal is to analyze visual hazard reports and deploy the *most specialized* available squad.

CURRENT ASSETS & SPECIALTIES:
- Alpha (Ground): General infantry, light medical. Good for clears roads.
- Bravo (Aerial): Fast recon drone swarm. Best for assessing large fires or floods from above.
- Charlie (Medical): *CURRENTLY BUSY at Sector 9*. specialized in triage.
- Delta (Engineering): Bridge repair, power generation, rubble clearing.
- Echo (Rescue): Swift water rescue, high-angle rescue. Carries Lifeboats. BEST FOR FLOODS.
- Foxtrot (Logistics): Heavy transport (fuel/food).
- Golf (Recon): Light scouts.
- Hotel (Firefighting): *CURRENTLY BUSY at Sector 3*. Specialized in fire suppression.

RULES OF ENGAGEMENT:
1. **Analyze the Hazard:**
   - If FLOOD detected -> Deploy **Echo** (Lifeboats) or **Bravo** (Aerial view).
   - If FIRE detected -> Deploy **Hotel** (if free) or **Bravo** (Aerial).
   - If RUBBLE/BLOCKED ROAD -> Deploy **Delta** (Engineering) to clear it.
   - If ROAD CLEAR -> Deploy **Alpha** or **Foxtrot** to secure the route.

2. **Check Status:**
   - Do NOT redeploy squads marked "Busy" unless the new threat is Catastrophic (Severity: CRITICAL).
   - Prioritize "Idle" squads.

3. **Output Format (STRICT):**
   - You must reason internally about which squad has the right equipment.
   - Your FINAL output line must be a single command in this format:
     "Deploy [Squad Name] to [Location]"
     or
     "Hold all squads at Base"
   
   Examples:
   "Deploy Echo to Sector 4"
   "Deploy Delta to Sector 4"
   "Hold all squads at Base"
"""

def stream_commander(observation_text):
    """
    Streams response from DeepSeek, yielding thoughts (CoT) and final commands.
    """
    try:
        # Build a dynamic status report string to feed the LLM
        squad_status_str = "\n".join([f"- {name}: {data['status']} ({data['type']})" for name, data in SQUADS.items()])

        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"INCOMING VISUAL REPORT: {observation_text}\n\nCURRENT SQUAD STATUS:\n{squad_status_str}\n\nYOUR COMMAND:"}
            ],
            max_tokens=512,
            temperature=0.1,
            stream=True 
        )

        reasoning_content = ""
        final_content = ""

        for chunk in stream:
            # 1. Capture "Thinking" (Reasoning)
            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'reasoning_content'):
                 r_chunk = chunk.choices[0].delta.reasoning_content
                 if r_chunk:
                     reasoning_content += r_chunk
                     yield {"type": "thinking", "content": r_chunk}

            # 2. Capture Final Answer (Command)
            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                f_chunk = chunk.choices[0].delta.content
                if f_chunk:
                    final_content += f_chunk
                    yield {"type": "answer", "content": f_chunk}
        
        # --- EXECUTE STATE UPDATE ---
        # Parse the final string to actually move the squad in Python memory
        command_str = final_content.strip()
        
        if "Deploy" in command_str:
            # Expected format: "Deploy [Name] to [Location]"
            try:
                parts = command_str.split(" to ")
                squad_name = parts[0].replace("Deploy ", "").strip()
                location = parts[1].strip()
                
                # Update the Global Dict
                if squad_name in SQUADS:
                    SQUADS[squad_name]["status"] = "Deployed"
                    SQUADS[squad_name]["loc"] = location
            except:
                pass # If LLM outputs weird text, just skip state update

        elif "Hold" in command_str:
             # Reset non-busy squads to Base? Or just do nothing?
             # Let's just log it.
             pass

    except Exception as e:
        yield {"type": "error", "content": f"Connection Error: {str(e)}"}
import os
import json
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
- Alpha (Ground): General infantry, light medical. Good for clearing roads.
- Bravo (Aerial): Fast recon drone swarm. Best for assessing large fires or floods from above.
- Charlie (Medical): *CURRENTLY BUSY at Sector 9*. Specialized in triage.
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

3. **Output Format (STRICT - MUST BE VALID JSON):**
   You must respond with ONLY a valid JSON object in this exact format:
   
   {
     "reasoning": "Detailed explanation of your decision including: hazard analysis, squad capabilities assessment, and why this squad is optimal",
     "squad_name": "SquadName",
     "location": "Sector X",
     "action": "deploy"
   }
   
   OR if no deployment is needed:
   
   {
     "reasoning": "Explanation of why no deployment is necessary",
     "action": "hold"
   }
   
   CRITICAL RULES:
   - Your final output MUST be valid JSON only - no additional text before or after
   - squad_name must be one of: Alpha, Bravo, Charlie, Delta, Echo, Foxtrot, Golf, Hotel
   - action must be either "deploy" or "hold"
   - reasoning should be 2-3 sentences explaining your tactical decision
   
   Examples:
   
   {
     "reasoning": "Flood detected with 45% coverage indicates CRITICAL severity. Echo squad has specialized swift water rescue equipment including lifeboats, making them optimal for water-based emergencies. They are currently Idle at Base.",
     "squad_name": "Echo",
     "location": "Sector 4",
     "action": "deploy"
   }
   
   {
     "reasoning": "Clear road detected with minimal hazards. No immediate deployment required as the sector is secure.",
     "action": "hold"
   }
"""

def update_squad_state(squads_dict, squad_name, location):
    """
    Updates squad state in the provided dictionary (which should be st.session_state.squads).
    
    Args:
        squads_dict: The squad dictionary to update (typically st.session_state.squads)
        squad_name: Name of the squad to update
        location: New location for the squad
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if squad_name not in squads_dict:
        return False, f"Unknown squad: {squad_name}"
    
    squads_dict[squad_name]["status"] = "Deployed"
    squads_dict[squad_name]["loc"] = location
    return True, f"✓ {squad_name} deployed to {location}"

def parse_deployment_command(json_str):
    """
    Parse JSON response from the LLM.
    
    Expected format:
    {
      "reasoning": "...",
      "squad_name": "Echo",
      "location": "Sector 4",
      "action": "deploy"
    }
    
    Returns:
        dict: Parsed command with keys: reasoning, squad_name, location, action
              Returns None if parsing fails
    """
    try:
        # Remove markdown code fences if present
        clean_json = json_str.strip()
        
        # Find the first { and last } to extract only JSON
        first_brace = clean_json.find('{')
        last_brace = clean_json.rfind('}')
        
        if first_brace == -1 or last_brace == -1:
            print(f"No JSON braces found in: {clean_json[:100]}")
            return None
        
        # Extract only the JSON part
        clean_json = clean_json[first_brace:last_brace + 1]
        
        # Parse JSON
        data = json.loads(clean_json)
        
        # Validate required fields
        if "action" not in data:
            return None
        
        if data["action"].lower() == "deploy":
            if "squad_name" not in data or "location" not in data:
                return None
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Attempted to parse: {clean_json[:200]}")
        return None
    except Exception as e:
        print(f"Unexpected parsing error: {e}")
        return None

def stream_commander(observation_text, squads_dict):
    """
    Streams response from DeepSeek, yielding thoughts (CoT) and final commands.
    
    Args:
        observation_text: The observation/hazard report from vision system
        squads_dict: The squad dictionary to update (st.session_state.squads)
    
    Yields:
        dict: Chunks with type and content
            - {"type": "thinking", "content": "..."} - Real-time CoT reasoning
            - {"type": "answer", "content": "..."} - Raw JSON response (streamed)
            - {"type": "reasoning", "content": "...", "squad": "...", "location": "...", "action": "..."}
            - {"type": "error", "content": "..."}
            - {"type": "status", "content": "..."}
            - {"type": "warning", "content": "..."}
    """
    try:
        # Build a dynamic status report string to feed the LLM
        squad_status_str = "\n".join([
            f"- {name}: {data['status']} ({data['type']})" 
            for name, data in squads_dict.items()
        ])

        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"INCOMING VISUAL REPORT: {observation_text}\n\nCURRENT SQUAD STATUS:\n{squad_status_str}\n\nYOUR COMMAND (respond with valid JSON only):"}
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
        
        # --- PARSE JSON RESPONSE ---
        parsed_command = parse_deployment_command(final_content.strip())
        
        if parsed_command is None:
            yield {"type": "warning", "content": f"⚠️ Could not parse JSON response. Raw output: {final_content[:100]}..."}
            return
        
        # --- PROCESS COMMAND (NORMALIZE ACTION TO LOWERCASE) ---
        action = parsed_command.get("action", "").lower()  # <-- FIX: Normalize to lowercase
        reasoning = parsed_command.get("reasoning", "No reasoning provided")
        
        if action == "deploy":
            squad_name = parsed_command.get("squad_name", "")
            location = parsed_command.get("location", "")
            
            if not squad_name or not location:
                yield {"type": "warning", "content": "⚠️ JSON missing required fields: squad_name or location"}
                return
            
            # Validate squad exists
            if squad_name not in squads_dict:
                yield {"type": "warning", "content": f"⚠️ Unknown squad: {squad_name}"}
                return
            
            # Update state
            success, message = update_squad_state(squads_dict, squad_name, location)
            
            # Yield structured reasoning with deployment info
            yield {
                "type": "reasoning",
                "content": reasoning,
                "squad": squad_name,
                "location": location,
                "action": "deploy"  # <-- Always lowercase
            }
            
            if success:
                yield {"type": "status", "content": message}
            else:
                yield {"type": "warning", "content": message}
        
        elif action == "hold":
            # Yield reasoning for hold decision
            yield {
                "type": "reasoning",
                "content": reasoning,
                "action": "hold"  # <-- Always lowercase
            }
            yield {"type": "status", "content": "✓ All squads holding position at Base"}
        
        else:
            yield {"type": "warning", "content": f"⚠️ Unknown action: {action}. Expected 'deploy' or 'hold'. Got: {parsed_command.get('action', 'N/A')}"} # Added more debug info

    except ConnectionError as e:
        yield {"type": "error", "content": f"Cannot connect to vLLM server at {VLLM_API_URL}. Is it running?"}
    except Exception as e:
        yield {"type": "error", "content": f"Unexpected error: {str(e)}"}
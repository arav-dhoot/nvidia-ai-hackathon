import json
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

# --- SETUP MODEL ---
# Make sure your Docker command uses "--served-model-name deepseek-reasoner"
llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",
    model="deepseek-reasoner", 
    temperature=0.1
)

# --- TOOLS ---
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

@tool
def get_all_squad_status():
    """Returns a list of all squads, their status, type, and location."""
    return str(SQUADS)

@tool
def deploy_squad(squad_name: str, sector: str):
    """Deploys a squad to a sector. Fails if squad is Busy."""
    if squad_name not in SQUADS:
        return f"Error: {squad_name} does not exist."
    if SQUADS[squad_name]['status'] == "Busy":
        return f"FAILURE: {squad_name} is busy at {SQUADS[squad_name]['loc']}."
    SQUADS[squad_name]['status'] = "Busy"
    SQUADS[squad_name]['loc'] = sector
    return f"SUCCESS: {squad_name} deployed to {sector}."

@tool
def check_route_hazard(sector: str):
    """Checks if the route to a sector is blocked by flood or debris."""
    if "Sector 4" in sector:
        return "CRITICAL: Route to Sector 4 is BLOCKED by floodwaters."
    return "Route is Clear."

tools = [get_all_squad_status, deploy_squad, check_route_hazard]
tools_map = {t.name: t for t in tools}

# --- AGENT LOOP ---
def run_commander(drone_observation):
    llm_with_tools = llm.bind_tools(tools, tool_choice="auto")
    
    messages = [
        SystemMessage(content=(
            "You are the AeroGuard Incident Commander. "
            "Your goal is to save lives. "
            "1. Check hazards before deploying Ground teams. "
            "2. Use Aerial teams (Bravo) if roads are blocked. "
            "3. Be concise."
        )),
        HumanMessage(content=f"Drone Observation: {drone_observation}")
    ]
    
    # Pass 1
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    # Tool Execution Loop
    if ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            selected_tool = tools_map[tool_call["name"]]
            tool_output = selected_tool.invoke(tool_call["args"])
            messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))
            
        # Pass 2 (Final Answer)
        final_response = llm_with_tools.invoke(messages)
        content = final_response.content
    else:
        content = ai_msg.content

    # Clean up DeepSeek thinking tags if present
    if "</think>" in content:
        content = content.split("</think>")[-1].strip()
        
    return content
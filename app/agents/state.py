from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    # Input
    user_message:   str
    session_id:     str

    # Agent reasoning
    intent:         str
    plan:           List[str]          # list of tool names to call
    reasoning:      str                # why agent chose these tools

    # Execution
    tool_results:   Dict[str, Any]     # tool_name → result dict
    tools_called:   List[str]          # tools actually executed

    # Memory
    chat_history:   List[Dict]         # previous messages for context

    # Output
    final_response: str
    response_data:  Dict[str, Any]     # structured response payload
    status:         str                # Good / Average / Poor / Info / Error

    # Meta
    error:          Optional[str]
    execution_time: float
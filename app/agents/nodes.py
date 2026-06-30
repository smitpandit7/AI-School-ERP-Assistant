import json
import time
from typing import Any, Dict
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.state import AgentState
from app.tools import (
    get_attendance,
    get_marks,
    get_fee_status,
    get_homework,
    get_timetable,
    get_academic_summary
)
from app.utils.logger import get_logger
from dotenv import load_dotenv
import os

load_dotenv()
logger = get_logger()

# ── LLM Setup ─────────────────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
    temperature=0.3
)

# ── Tool Registry ──────────────────────────────────────────────────────────────
TOOL_REGISTRY = {
    "get_attendance":     get_attendance,
    "get_marks":          get_marks,
    "get_fee_status":     get_fee_status,
    "get_homework":       get_homework,
    "get_timetable":      get_timetable,
    "get_academic_summary": get_academic_summary
}

TOOL_DESCRIPTIONS = """
Available ERP Tools:
1. get_attendance     - attendance records, percentage, absent dates. Args: month (YYYY-MM, optional)
2. get_marks          - subject marks, averages, grade. Args: subject (optional, e.g. 'Mathematics')
3. get_fee_status     - fee records, paid/pending amounts. Args: filter_status (optional: 'Paid'/'Pending'/'Overdue')
4. get_homework       - homework assignments. Args: filter_type ('pending'/'today'/'tomorrow'/'submitted'/'all')
5. get_timetable      - class schedule. Args: day (optional: 'Monday'/.../'today'/'tomorrow')
6. get_academic_summary - full academic summary with suggestions. Args: none
"""


# ══════════════════════════════════════════════════════════════════════════════
# NODE 1 — Intent Classifier
# ══════════════════════════════════════════════════════════════════════════════
def intent_classifier_node(state: AgentState) -> AgentState:
    """
    Reads user message + chat history.
    Identifies the intent label.
    """
    logger.info(f"[Intent Node] Message: {state['user_message']}")

    # Build history context
    history_text = ""
    if state.get("chat_history"):
        recent = state["chat_history"][-6:]  # last 3 exchanges
        history_text = "\n".join([
            f"{m['role'].upper()}: {m['message']}"
            for m in recent
        ])

    system_prompt = """You are an intent classifier for a School ERP system.
Classify the user's message into ONE of these intents:
- Attendance
- Marks
- Fees
- Homework
- Timetable
- AcademicSummary
- MultiStep
- Unknown

MultiStep means the user is asking about MORE than one ERP area in a single message.
Use chat history to resolve follow-up questions (e.g. "which subject?" after marks were shown).

Respond with ONLY a JSON object, no extra text:
{
  "intent": "<intent_label>",
  "reasoning": "<one line explanation>"
}"""

    user_prompt = f"""Chat History:
{history_text if history_text else 'No previous conversation.'}

Current Message: {state['user_message']}"""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        raw = response.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed    = json.loads(raw.strip())
        intent    = parsed.get("intent", "Unknown")
        reasoning = parsed.get("reasoning", "")

        logger.info(f"[Intent Node] Intent: {intent} | Reasoning: {reasoning}")

        return {
            **state,
            "intent":    intent,
            "reasoning": reasoning
        }

    except Exception as e:
        logger.error(f"[Intent Node] Failed: {e}")
        return {
            **state,
            "intent":    "Unknown",
            "reasoning": f"Intent classification failed: {str(e)}"
        }


# ══════════════════════════════════════════════════════════════════════════════
# NODE 2 — Planner
# ══════════════════════════════════════════════════════════════════════════════
def planner_node(state: AgentState) -> AgentState:
    """
    Based on intent + user message, decides:
    - Which tools to call
    - What arguments to pass to each tool
    """
    logger.info(f"[Planner Node] Planning for intent: {state['intent']}")

    # Build history context
    history_text = ""
    if state.get("chat_history"):
        recent = state["chat_history"][-6:]
        history_text = "\n".join([
            f"{m['role'].upper()}: {m['message']}"
            for m in recent
        ])

    system_prompt = f"""You are an ERP agent planner. Based on the user's intent and message,
decide which tools to call and what arguments to pass.

{TOOL_DESCRIPTIONS}

Respond with ONLY a JSON object, no extra text:
{{
  "plan": [
    {{
      "tool": "<tool_name>",
      "args": {{}}
    }}
  ],
  "plan_description": "<brief description of what you will do>"
}}

Rules:
- For MultiStep intent, include ALL relevant tools
- For follow-up questions, use context from chat history
- If intent is Unknown, return empty plan
- Keep args as empty dict {{}} if tool needs no arguments
- For get_marks with a specific subject mentioned, pass the subject name
- For get_homework, choose filter_type based on user's question
- For get_timetable, pass the day if mentioned"""

    user_prompt = f"""Chat History:
{history_text if history_text else 'No previous conversation.'}

Intent: {state['intent']}
User Message: {state['user_message']}"""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())

        plan             = parsed.get("plan", [])
        plan_description = parsed.get("plan_description", "")

        tool_names = [step["tool"] for step in plan]
        logger.info(f"[Planner Node] Plan: {tool_names} | {plan_description}")

        return {
            **state,
            "plan":      plan,
            "reasoning": state.get("reasoning", "") + f" | Plan: {plan_description}"
        }

    except Exception as e:
        logger.error(f"[Planner Node] Failed: {e}")
        return {
            **state,
            "plan":  [],
            "error": f"Planning failed: {str(e)}"
        }


# ══════════════════════════════════════════════════════════════════════════════
# NODE 3 — Tool Executor
# ══════════════════════════════════════════════════════════════════════════════
def tool_executor_node(state: AgentState) -> AgentState:
    """
    Executes each tool in the plan sequentially.
    Stores all results in tool_results dict.
    """
    logger.info(f"[Executor Node] Executing {len(state.get('plan', []))} tools")

    plan         = state.get("plan", [])
    tool_results = {}
    tools_called = []

    if not plan:
        logger.warning("[Executor Node] No tools to execute")
        return {
            **state,
            "tool_results": {"message": "No tools were selected for this query"},
            "tools_called": []
        }

    for step in plan:
        tool_name = step.get("tool")
        tool_args = step.get("args", {})

        if tool_name not in TOOL_REGISTRY:
            logger.warning(f"[Executor Node] Unknown tool: {tool_name}")
            tool_results[tool_name] = {"error": f"Tool '{tool_name}' not found"}
            continue

        try:
            tool_fn = TOOL_REGISTRY[tool_name]
            logger.info(f"[Executor Node] Calling {tool_name} with args: {tool_args}")

            # Call tool with or without args
            if tool_args:
                result = tool_fn.invoke(tool_args)
            else:
                result = tool_fn.invoke({})

            tool_results[tool_name] = result
            tools_called.append(tool_name)
            logger.info(f"[Executor Node] {tool_name} completed successfully")

        except Exception as e:
            logger.error(f"[Executor Node] Tool {tool_name} failed: {e}")
            tool_results[tool_name] = {"error": f"Tool execution failed: {str(e)}"}

    return {
        **state,
        "tool_results": tool_results,
        "tools_called": tools_called
    }


# ══════════════════════════════════════════════════════════════════════════════
# NODE 4 — Response Generator
# ══════════════════════════════════════════════════════════════════════════════
def response_generator_node(state: AgentState) -> AgentState:
    """
    Takes tool results + user message.
    Calls Groq to generate a natural, friendly response.
    Returns structured JSON response.
    """
    logger.info(f"[Response Node] Generating response for intent: {state['intent']}")

    tool_results  = state.get("tool_results", {})
    user_message  = state["user_message"]
    intent        = state["intent"]
    tools_called  = state.get("tools_called", [])

    # Handle unknown intent / no tools
    if intent == "Unknown" or not tools_called:
        return {
            **state,
            "final_response": "I'm sorry, I couldn't understand your request. Please ask about attendance, marks, fees, homework, or timetable.",
            "response_data":  {"intent": intent, "tools_called": tools_called},
            "status":         "Error"
        }

    system_prompt = """You are a friendly School ERP Assistant helping a student named Smit.
You receive ERP data from tools and must generate a clear, helpful, natural response.

Rules:
- Be concise but complete
- Use simple language a student would understand  
- Highlight important numbers (percentages, amounts, dates, fees)
- If data shows issues (low marks, pending fees, low attendance), mention them gently
- For multi-tool results, organize the response section by section
- Never make up data — only use what's provided in tool results
- End with a helpful tip if relevant"""

    user_prompt = f"""User asked: "{user_message}"
Intent detected: {intent}
Tools called: {tools_called}

Tool Results:
{json.dumps(tool_results, indent=2)}

Generate a helpful, natural response based on the above data."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        final_response = response.content.strip()

        # Determine overall status
        status = _determine_status(intent, tool_results)

        logger.info(f"[Response Node] Response generated. Status: {status}")

        return {
            **state,
            "final_response": final_response,
            "response_data": {
                "intent":       intent,
                "tools_called": tools_called,
                "tool_results": tool_results
            },
            "status": status
        }

    except Exception as e:
        logger.error(f"[Response Node] Failed: {e}")
        return {
            **state,
            "final_response": "I encountered an error generating your response. Please try again.",
            "response_data":  {"error": str(e)},
            "status":         "Error"
        }


def _determine_status(intent: str, tool_results: Dict[str, Any]) -> str:
    """Derive a meaningful status from tool results."""
    try:
        if intent == "Attendance":
            result = tool_results.get("get_attendance", {})
            return result.get("status", "Info")

        elif intent == "Marks":
            result = tool_results.get("get_marks", {})
            avg    = result.get("overall_average", 0)
            if avg >= 80: return "Good"
            if avg >= 60: return "Average"
            return "Poor"

        elif intent == "Fees":
            result  = tool_results.get("get_fee_status", {})
            pending = result.get("pending_amount", 0)
            return "Clear" if pending == 0 else "Pending"

        elif intent == "Homework":
            result  = tool_results.get("get_homework", {})
            pending = result.get("total", 0)
            return "Clear" if pending == 0 else "Pending"

        elif intent == "Timetable":
            return "Info"

        elif intent == "AcademicSummary":
            result = tool_results.get("get_academic_summary", {})
            avg    = result.get("overall_average", 0)
            if avg >= 80: return "Good"
            if avg >= 60: return "Average"
            return "Poor"

        elif intent == "MultiStep":
            return "Info"

    except Exception:
        pass

    return "Info"
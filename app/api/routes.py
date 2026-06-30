import time
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ChatRequest, ChatResponse,
    HistoryResponse, HistoryMessage,
    SessionsResponse,
    ClearSessionRequest, ClearSessionResponse
)
from app.agents.graph import erp_agent
from app.memory.chat_memory import save_message, get_history, get_all_sessions, clear_session
from app.utils.logger import get_logger, log_request

logger = get_logger()
router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# POST /chat
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """
    Main chat endpoint. Send a natural language message,
    get back an AI-generated structured response.
    """
    start_time = time.time()

    # ── Error Handling: Empty request ──────────────────────────────
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = request.session_id or "default"

    try:
        # ── Fetch chat history for context ─────────────────────────
        history = get_history(session_id, limit=10)

        # ── Build initial agent state ──────────────────────────────
        initial_state = {
            "user_message":   request.message,
            "session_id":     session_id,
            "intent":         "",
            "plan":           [],
            "reasoning":      "",
            "tool_results":   {},
            "tools_called":   [],
            "chat_history":   history,
            "final_response": "",
            "response_data":  {},
            "status":         "",
            "error":          None,
            "execution_time": 0.0
        }

        # ── Run the LangGraph agent ─────────────────────────────────
        result = erp_agent.invoke(initial_state)

        execution_time = round(time.time() - start_time, 3)

        # ── Save conversation to memory ─────────────────────────────
        save_message(session_id, "user", request.message, result.get("intent"))
        save_message(session_id, "assistant", result.get("final_response", ""), result.get("intent"))

        # ── Log the request ──────────────────────────────────────────
        log_request(
            session_id=session_id,
            user_query=request.message,
            intent=result.get("intent", "Unknown"),
            tools_used=result.get("tools_called", []),
            execution_time=execution_time,
            response=result.get("final_response", ""),
            status=result.get("status", "Info")
        )

        # ── Build response ────────────────────────────────────────────
        return ChatResponse(
            intent=result.get("intent", "Unknown"),
            response=result.get("final_response", "Something went wrong."),
            status=result.get("status", "Error"),
            session_id=session_id,
            tools_called=result.get("tools_called", []),
            plan=result.get("plan", []),
            reasoning=result.get("reasoning", ""),
            execution_time=execution_time,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data=result.get("response_data", {})
        )

    except Exception as e:
        execution_time = round(time.time() - start_time, 3)
        logger.error(f"[Chat Endpoint] Unexpected error: {e}")

        log_request(
            session_id=session_id,
            user_query=request.message,
            intent="Error",
            tools_used=[],
            execution_time=execution_time,
            response=str(e),
            status="Error"
        )

        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while processing your request: {str(e)}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# GET /chat/history
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/chat/history", response_model=HistoryResponse, tags=["Chat"])
def chat_history(session_id: str = "default", limit: int = 20):
    """
    Fetch conversation history for a given session.
    """
    try:
        history = get_history(session_id, limit=limit)

        messages = [
            HistoryMessage(
                role=h["role"],
                message=h["message"],
                intent=h.get("intent"),
                timestamp=h["timestamp"]
            )
            for h in history
        ]

        return HistoryResponse(
            session_id=session_id,
            total_messages=len(messages),
            messages=messages
        )

    except Exception as e:
        logger.error(f"[History Endpoint] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# GET /chat/sessions  (extra utility — good for demo/screen recording)
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/chat/sessions", response_model=SessionsResponse, tags=["Chat"])
def list_sessions():
    """
    List all active chat sessions. Useful for debugging and demos.
    """
    try:
        sessions = get_all_sessions()
        return SessionsResponse(
            total_sessions=len(sessions),
            sessions=sessions
        )
    except Exception as e:
        logger.error(f"[Sessions Endpoint] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /chat/history  (extra utility)
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/chat/history", response_model=ClearSessionResponse, tags=["Chat"])
def clear_chat_history(request: ClearSessionRequest):
    """
    Clear conversation history for a given session.
    """
    try:
        success = clear_session(request.session_id)
        return ClearSessionResponse(
            success=success,
            session_id=request.session_id,
            message="Session history cleared." if success else "Failed to clear session."
        )
    except Exception as e:
        logger.error(f"[Clear Endpoint] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")
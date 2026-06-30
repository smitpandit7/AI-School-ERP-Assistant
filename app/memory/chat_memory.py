from datetime import datetime
from typing import List, Dict
from app.utils.db import get_connection
from app.utils.logger import get_logger

logger = get_logger()


def save_message(
    session_id: str,
    role:       str,
    message:    str,
    intent:     str = None
):
    """
    Save a single message to chat_history table.
    role: 'user' or 'assistant'
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO chat_history (session_id, role, message, intent, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            role,
            message,
            intent,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        logger.debug(f"[Memory] Saved {role} message for session {session_id}")

    except Exception as e:
        logger.error(f"[Memory] Failed to save message: {e}")
    finally:
        conn.close()


def get_history(session_id: str, limit: int = 20) -> List[Dict]:
    """
    Fetch recent chat history for a session.
    Returns list of dicts with role, message, intent, timestamp.
    limit: max number of messages to return (default 20)
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT role, message, intent, timestamp
            FROM chat_history
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (session_id, limit))

        rows = cursor.fetchall()

        # Reverse so oldest is first (chronological order)
        history = [dict(r) for r in reversed(rows)]
        logger.debug(f"[Memory] Fetched {len(history)} messages for session {session_id}")
        return history

    except Exception as e:
        logger.error(f"[Memory] Failed to fetch history: {e}")
        return []
    finally:
        conn.close()


def get_all_sessions() -> List[Dict]:
    """
    Returns summary of all sessions.
    Used for admin/debug purposes.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                session_id,
                COUNT(*) as message_count,
                MIN(timestamp) as started_at,
                MAX(timestamp) as last_active
            FROM chat_history
            GROUP BY session_id
            ORDER BY last_active DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

    except Exception as e:
        logger.error(f"[Memory] Failed to fetch sessions: {e}")
        return []
    finally:
        conn.close()


def clear_session(session_id: str) -> bool:
    """
    Clears all messages for a given session.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM chat_history WHERE session_id = ?
        """, (session_id,))
        conn.commit()
        logger.info(f"[Memory] Cleared session {session_id}")
        return True

    except Exception as e:
        logger.error(f"[Memory] Failed to clear session: {e}")
        return False
    finally:
        conn.close()
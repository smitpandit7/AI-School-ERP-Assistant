import logging
import os
from datetime import datetime

LOG_DIR  = os.path.join(os.path.dirname(__file__), "../../logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def get_logger(name: str = "school_erp") -> logging.Logger:
    """
    Returns a configured logger that writes to:
    - Console (INFO level)
    - logs/app.log file (DEBUG level)
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Console Handler ────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    ))

    # ── File Handler ───────────────────────────────────────────────
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def log_request(
    session_id:     str,
    user_query:     str,
    intent:         str,
    tools_used:     list,
    execution_time: float,
    response:       str,
    status:         str
):
    """
    Writes a structured request log entry to app.log.
    Called once per /chat request after agent completes.
    """
    logger = get_logger()

    divider       = "─" * 60
    response_prev = response[:120] + "..." if len(response) > 120 else response

    log_entry = f"""
{divider}
TIMESTAMP      : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
SESSION_ID     : {session_id}
USER_QUERY     : {user_query}
INTENT         : {intent}
TOOLS_USED     : {', '.join(tools_used) if tools_used else 'None'}
EXECUTION_TIME : {execution_time:.3f}s
STATUS         : {status}
RESPONSE       : {response_prev}
{divider}"""

    logger.debug(log_entry)
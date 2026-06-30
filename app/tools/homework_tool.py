from langchain_core.tools import tool
from app.utils.db import get_connection
from datetime import datetime, timedelta

@tool
def get_homework(filter_type: str = "pending") -> dict:
    """
    Fetch homework for student S001.
    filter_type options:
      - 'pending'   → all pending homework
      - 'today'     → due today
      - 'tomorrow'  → due tomorrow
      - 'submitted' → already submitted
      - 'all'       → everything
    """
    student_id = "S001"

    today    = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Validate student
        cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            return {"error": "Student not found", "student_id": student_id}

        # Build query based on filter
        if filter_type == "today":
            cursor.execute("""
                SELECT subject, description, assigned_date, due_date, status
                FROM homework
                WHERE student_id = ? AND due_date = ?
                ORDER BY subject
            """, (student_id, today))

        elif filter_type == "tomorrow":
            cursor.execute("""
                SELECT subject, description, assigned_date, due_date, status
                FROM homework
                WHERE student_id = ? AND due_date = ?
                ORDER BY subject
            """, (student_id, tomorrow))

        elif filter_type == "submitted":
            cursor.execute("""
                SELECT subject, description, assigned_date, due_date, status
                FROM homework
                WHERE student_id = ? AND status = 'Submitted'
                ORDER BY due_date DESC
            """, (student_id,))

        elif filter_type == "all":
            cursor.execute("""
                SELECT subject, description, assigned_date, due_date, status
                FROM homework
                WHERE student_id = ?
                ORDER BY due_date ASC
            """, (student_id,))

        else:  # default: pending
            cursor.execute("""
                SELECT subject, description, assigned_date, due_date, status
                FROM homework
                WHERE student_id = ? AND status = 'Pending'
                ORDER BY due_date ASC
            """, (student_id,))

        rows = cursor.fetchall()

        if not rows:
            return {
                "message": f"No homework found for filter: {filter_type}",
                "filter":  filter_type,
                "today":   today,
                "records": []
            }

        records = [dict(r) for r in rows]

        # Mark overdue
        for r in records:
            if r["status"] == "Pending" and r["due_date"] < today:
                r["overdue"] = True
            else:
                r["overdue"] = False

        overdue_count = sum(1 for r in records if r.get("overdue"))

        return {
            "student_id":    student_id,
            "student_name":  student["name"],
            "filter":        filter_type,
            "today":         today,
            "tomorrow":      tomorrow,
            "total":         len(records),
            "overdue_count": overdue_count,
            "records":       records
        }

    except Exception as e:
        return {"error": f"Homework tool failed: {str(e)}"}
    finally:
        conn.close()
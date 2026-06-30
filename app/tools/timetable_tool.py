from langchain_core.tools import tool
from app.utils.db import get_connection
from datetime import datetime

# Map Python weekday number to day name
WEEKDAY_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

@tool
def get_timetable(day: str = None) -> dict:
    """
    Fetch timetable for student S001.
    day: 'Monday', 'Tuesday', etc.
    If day is None, returns today's timetable.
    Pass day='tomorrow' to get tomorrow's timetable.
    """
    student_id = "S001"

    today_index   = datetime.now().weekday()
    today_name    = WEEKDAY_MAP.get(today_index, "Monday")
    tomorrow_name = WEEKDAY_MAP.get((today_index + 1) % 7, "Tuesday")

    # Resolve day
    if not day or day.lower() == "today":
        target_day = today_name
    elif day.lower() == "tomorrow":
        target_day = tomorrow_name
    else:
        target_day = day.capitalize()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Validate student
        cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            return {"error": "Student not found", "student_id": student_id}

        # Weekend check
        if target_day in ("Saturday", "Sunday"):
            return {
                "student_id":   student_id,
                "student_name": student["name"],
                "day":          target_day,
                "message":      "No classes on weekends.",
                "records":      []
            }

        # Fetch timetable
        cursor.execute("""
            SELECT period, subject, teacher, start_time, end_time
            FROM timetable
            WHERE student_id = ? AND LOWER(day) = LOWER(?)
            ORDER BY period ASC
        """, (student_id, target_day))

        rows = cursor.fetchall()

        if not rows:
            return {
                "error":   "No timetable found",
                "day":     target_day,
                "student_id": student_id
            }

        records = [dict(r) for r in rows]

        first_class = records[0]
        last_class  = records[-1]

        # Find specific subject times
        subject_schedule = {}
        for r in records:
            subject_schedule[r["subject"]] = {
                "period":     r["period"],
                "start_time": r["start_time"],
                "end_time":   r["end_time"],
                "teacher":    r["teacher"]
            }

        return {
            "student_id":       student_id,
            "student_name":     student["name"],
            "day":              target_day,
            "today":            today_name,
            "total_periods":    len(records),
            "first_class":      first_class,
            "last_class":       last_class,
            "subject_schedule": subject_schedule,
            "records":          records
        }

    except Exception as e:
        return {"error": f"Timetable tool failed: {str(e)}"}
    finally:
        conn.close()
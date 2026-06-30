from langchain_core.tools import tool
from app.utils.db import get_connection
from datetime import datetime

@tool
def get_attendance(month: str = None) -> dict:
    """
    Fetch attendance records for student S001.
    month format: 'YYYY-MM' e.g. '2026-06'
    If month is None, returns current month attendance.
    """
    student_id = "S001"

    if not month:
        month = datetime.now().strftime("%Y-%m")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Validate student
        cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            return {"error": "Student not found", "student_id": student_id}

        # Fetch attendance for given month
        cursor.execute("""
            SELECT date, status, subject
            FROM attendance
            WHERE student_id = ? AND date LIKE ?
            ORDER BY date ASC
        """, (student_id, f"{month}%"))

        rows = cursor.fetchall()

        if not rows:
            return {
                "error": "No attendance records found",
                "month": month,
                "student_id": student_id
            }

        records = [dict(r) for r in rows]

        # Calculate stats
        total_days   = len(records)
        present_days = sum(1 for r in records if r["status"] == "Present")
        absent_days  = sum(1 for r in records if r["status"] == "Absent")
        holidays     = sum(1 for r in records if r["status"] == "Holiday")
        working_days = total_days - holidays
        percentage   = round((present_days / working_days) * 100, 2) if working_days > 0 else 0

        # Absent dates
        absent_dates = [r["date"] for r in records if r["status"] == "Absent"]

        return {
            "student_id":    student_id,
            "student_name":  student["name"],
            "month":         month,
            "total_days":    total_days,
            "working_days":  working_days,
            "present_days":  present_days,
            "absent_days":   absent_days,
            "holidays":      holidays,
            "percentage":    percentage,
            "absent_dates":  absent_dates,
            "records":       records,
            "status":        "Good" if percentage >= 90 else "Average" if percentage >= 75 else "Poor"
        }

    except Exception as e:
        return {"error": f"Attendance tool failed: {str(e)}"}
    finally:
        conn.close()
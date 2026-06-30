from langchain_core.tools import tool
from app.utils.db import get_connection
from datetime import datetime

@tool
def get_academic_summary() -> dict:
    """
    Generate a complete academic performance summary for student S001.
    Includes marks analysis, attendance, homework status, and fee status.
    Used for bonus: Academic Performance Summary feature.
    """
    student_id = "S001"
    month = datetime.now().strftime("%Y-%m")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Student info
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            return {"error": "Student not found"}

        # ── Marks Summary ──────────────────────────────────────────
        cursor.execute("""
            SELECT subject, AVG(marks) as avg_marks
            FROM marks
            WHERE student_id = ?
            GROUP BY subject
        """, (student_id,))
        marks_rows = cursor.fetchall()
        subject_averages = {r["subject"]: round(r["avg_marks"], 2) for r in marks_rows}
        overall_avg = round(sum(subject_averages.values()) / len(subject_averages), 2) if subject_averages else 0

        sorted_subjects = sorted(subject_averages.items(), key=lambda x: x[1], reverse=True)
        strong_subjects = [s[0] for s in sorted_subjects if s[1] >= 80]
        weak_subjects   = [s[0] for s in sorted_subjects if s[1] < 70]

        # ── Attendance Summary ─────────────────────────────────────
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM attendance
            WHERE student_id = ? AND date LIKE ?
            GROUP BY status
        """, (student_id, f"{month}%"))
        att_rows     = {r["status"]: r["count"] for r in cursor.fetchall()}
        present      = att_rows.get("Present", 0)
        absent       = att_rows.get("Absent", 0)
        holidays     = att_rows.get("Holiday", 0)
        working_days = present + absent
        att_pct      = round((present / working_days) * 100, 2) if working_days > 0 else 0

        # ── Homework Summary ───────────────────────────────────────
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM homework
            WHERE student_id = ?
            GROUP BY status
        """, (student_id,))
        hw_rows       = {r["status"]: r["count"] for r in cursor.fetchall()}
        hw_pending    = hw_rows.get("Pending", 0)
        hw_submitted  = hw_rows.get("Submitted", 0)

        # ── Fee Summary ────────────────────────────────────────────
        cursor.execute("""
            SELECT status, SUM(amount) as total
            FROM fees
            WHERE student_id = ?
            GROUP BY status
        """, (student_id,))
        fee_rows      = {r["status"]: r["total"] for r in cursor.fetchall()}
        fee_pending   = fee_rows.get("Pending", 0)

        # ── AI Suggestions ─────────────────────────────────────────
        suggestions = []
        if weak_subjects:
            suggestions.append(f"Focus more on {', '.join(weak_subjects)} — your average is below 70%.")
        if att_pct < 90:
            suggestions.append("Try to improve attendance. Aim for at least 90%.")
        if hw_pending > 0:
            suggestions.append(f"You have {hw_pending} pending homework assignments. Complete them soon.")
        if fee_pending > 0:
            suggestions.append(f"₹{fee_pending} in fees are pending. Please clear them before the due date.")
        if not suggestions:
            suggestions.append("Great performance! Keep it up.")

        return {
            "student_id":       student_id,
            "student_name":     dict(student)["name"],
            "month":            month,
            "overall_average":  overall_avg,
            "grade":            _get_grade(overall_avg),
            "subject_averages": subject_averages,
            "strong_subjects":  strong_subjects,
            "weak_subjects":    weak_subjects,
            "attendance": {
                "present":      present,
                "absent":       absent,
                "percentage":   att_pct,
                "status":       "Good" if att_pct >= 90 else "Needs Improvement"
            },
            "homework": {
                "pending":      hw_pending,
                "submitted":    hw_submitted
            },
            "fees": {
                "pending_amount": fee_pending
            },
            "suggestions":      suggestions
        }

    except Exception as e:
        return {"error": f"Summary tool failed: {str(e)}"}
    finally:
        conn.close()


def _get_grade(avg: float) -> str:
    if avg >= 90: return "A+"
    if avg >= 80: return "A"
    if avg >= 70: return "B"
    if avg >= 60: return "C"
    if avg >= 50: return "D"
    return "F"
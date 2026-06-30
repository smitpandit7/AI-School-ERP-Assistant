from langchain_core.tools import tool
from app.utils.db import get_connection

@tool
def get_marks(subject: str = None) -> dict:
    """
    Fetch marks for student S001.
    subject: optional filter e.g. 'Mathematics', 'Science'
    If subject is None, returns all subjects.
    """
    student_id = "S001"

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Validate student
        cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            return {"error": "Student not found", "student_id": student_id}

        # Fetch marks
        if subject:
            cursor.execute("""
                SELECT subject, exam_type, marks, max_marks, exam_date
                FROM marks
                WHERE student_id = ? AND LOWER(subject) = LOWER(?)
                ORDER BY exam_date ASC
            """, (student_id, subject))
        else:
            cursor.execute("""
                SELECT subject, exam_type, marks, max_marks, exam_date
                FROM marks
                WHERE student_id = ?
                ORDER BY subject, exam_date ASC
            """, (student_id,))

        rows = cursor.fetchall()

        if not rows:
            return {
                "error": "No marks found",
                "subject": subject or "All",
                "student_id": student_id
            }

        records = [dict(r) for r in rows]

        # Subject-wise average
        subject_map = {}
        for r in records:
            sub = r["subject"]
            if sub not in subject_map:
                subject_map[sub] = {"marks": [], "max_marks": []}
            subject_map[sub]["marks"].append(r["marks"])
            subject_map[sub]["max_marks"].append(r["max_marks"])

        subject_averages = {}
        for sub, data in subject_map.items():
            avg = round(sum(data["marks"]) / len(data["marks"]), 2)
            subject_averages[sub] = avg

        # Overall average
        all_marks = [r["marks"] for r in records]
        overall_avg = round(sum(all_marks) / len(all_marks), 2)

        # Best and worst subject
        best_subject  = max(subject_averages, key=subject_averages.get)
        worst_subject = min(subject_averages, key=subject_averages.get)

        return {
            "student_id":       student_id,
            "student_name":     student["name"],
            "filter_subject":   subject or "All",
            "records":          records,
            "subject_averages": subject_averages,
            "overall_average":  overall_avg,
            "best_subject":     best_subject,
            "best_score":       subject_averages[best_subject],
            "worst_subject":    worst_subject,
            "worst_score":      subject_averages[worst_subject],
            "grade":            _get_grade(overall_avg)
        }

    except Exception as e:
        return {"error": f"Marks tool failed: {str(e)}"}
    finally:
        conn.close()


def _get_grade(avg: float) -> str:
    if avg >= 90: return "A+"
    if avg >= 80: return "A"
    if avg >= 70: return "B"
    if avg >= 60: return "C"
    if avg >= 50: return "D"
    return "F"
from langchain_core.tools import tool
from app.utils.db import get_connection

@tool
def get_fee_status(filter_status: str = None) -> dict:
    """
    Fetch fee records for student S001.
    filter_status: optional — 'Paid', 'Pending', 'Overdue'
    If None, returns all fee records.
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

        # Fetch fees
        if filter_status:
            cursor.execute("""
                SELECT fee_type, amount, due_date, paid_date, status
                FROM fees
                WHERE student_id = ? AND LOWER(status) = LOWER(?)
                ORDER BY due_date DESC
            """, (student_id, filter_status))
        else:
            cursor.execute("""
                SELECT fee_type, amount, due_date, paid_date, status
                FROM fees
                WHERE student_id = ?
                ORDER BY due_date DESC
            """, (student_id,))

        rows = cursor.fetchall()

        if not rows:
            return {
                "error": "No fee records found",
                "filter": filter_status or "All",
                "student_id": student_id
            }

        records = [dict(r) for r in rows]

        # Calculate totals
        total_amount  = sum(r["amount"] for r in records)
        paid_amount   = sum(r["amount"] for r in records if r["status"] == "Paid")
        pending_amount = sum(r["amount"] for r in records if r["status"] == "Pending")
        overdue_amount = sum(r["amount"] for r in records if r["status"] == "Overdue")

        # Pending fee list
        pending_fees = [r for r in records if r["status"] in ("Pending", "Overdue")]
        paid_fees    = [r for r in records if r["status"] == "Paid"]

        return {
            "student_id":      student_id,
            "student_name":    student["name"],
            "filter":          filter_status or "All",
            "records":         records,
            "total_amount":    total_amount,
            "paid_amount":     paid_amount,
            "pending_amount":  pending_amount,
            "overdue_amount":  overdue_amount,
            "pending_fees":    pending_fees,
            "paid_fees":       paid_fees,
            "all_clear":       pending_amount == 0 and overdue_amount == 0
        }

    except Exception as e:
        return {"error": f"Fee tool failed: {str(e)}"}
    finally:
        conn.close()
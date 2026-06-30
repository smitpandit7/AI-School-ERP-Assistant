from app.tools.attendance_tool import get_attendance
from app.tools.marks_tool      import get_marks
from app.tools.fees_tool       import get_fee_status
from app.tools.homework_tool   import get_homework
from app.tools.timetable_tool  import get_timetable
from app.tools.summary_tool    import get_academic_summary

ALL_TOOLS = [
    get_attendance,
    get_marks,
    get_fee_status,
    get_homework,
    get_timetable,
    get_academic_summary
]
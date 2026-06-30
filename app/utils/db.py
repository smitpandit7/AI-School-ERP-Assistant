import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../../mock_data/school.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # ── TABLE 1: Students ──────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id   TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            class        TEXT NOT NULL,
            section      TEXT NOT NULL,
            parent_email TEXT
        )
    """)

    # ── TABLE 2: Attendance ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            date        TEXT NOT NULL,
            status      TEXT NOT NULL,  -- Present / Absent / Holiday
            subject     TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # ── TABLE 3: Marks ────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            subject     TEXT NOT NULL,
            exam_type   TEXT NOT NULL,  -- Unit Test / Midterm / Final
            marks       REAL NOT NULL,
            max_marks   REAL NOT NULL,
            exam_date   TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # ── TABLE 4: Fees ─────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id    TEXT NOT NULL,
            fee_type      TEXT NOT NULL,  -- Tuition / Transport / Library
            amount        REAL NOT NULL,
            due_date      TEXT NOT NULL,
            paid_date     TEXT,           -- NULL means unpaid
            status        TEXT NOT NULL,  -- Paid / Pending / Overdue
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # ── TABLE 5: Homework ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            subject     TEXT NOT NULL,
            description TEXT NOT NULL,
            assigned_date TEXT NOT NULL,
            due_date    TEXT NOT NULL,
            status      TEXT NOT NULL,   -- Pending / Submitted / Overdue
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # ── TABLE 6: Timetable ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT NOT NULL,
            day         TEXT NOT NULL,   -- Monday, Tuesday...
            period      INTEGER NOT NULL,
            subject     TEXT NOT NULL,
            teacher     TEXT NOT NULL,
            start_time  TEXT NOT NULL,
            end_time    TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # ── TABLE 7: Chat History ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            role        TEXT NOT NULL,   -- user / assistant
            message     TEXT NOT NULL,
            intent      TEXT,
            timestamp   TEXT NOT NULL
        )
    """)

    conn.commit()

    # ── SEED DATA (only if empty) ─────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        _seed_data(cursor)
        conn.commit()
        print("✅ Mock data seeded successfully.")
    else:
        print("✅ Database already initialized.")

    conn.close()

def validate_student(student_id: str) -> dict | None:
    """
    Returns student record if valid, None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def _seed_data(cursor):

    # Students
    cursor.execute("""
        INSERT INTO students VALUES 
        ('S001', 'Smit Pandit', '10th', 'A', 'parent@example.com')
    """)

    # Second student — Aman
    cursor.execute("""
        INSERT INTO students VALUES 
        ('S002', 'Aman Verma', '10th', 'B', 'aman.parent@example.com')
    """)
    attendance_data_aman = [
        ('S002', '2026-06-01', 'Present', 'Mathematics'),
        ('S002', '2026-06-02', 'Absent',  'Science'),
        ('S002', '2026-06-03', 'Absent',  'English'),
        ('S002', '2026-06-04', 'Present', 'History'),
        ('S002', '2026-06-05', 'Present', 'Mathematics'),
        ('S002', '2026-06-06', 'Holiday', None),
        ('S002', '2026-06-07', 'Holiday', None),
        ('S002', '2026-06-08', 'Present', 'Science'),
        ('S002', '2026-06-09', 'Absent',  'English'),
        ('S002', '2026-06-10', 'Present', 'Mathematics'),
        ('S002', '2026-06-11', 'Present', 'History'),
        ('S002', '2026-06-12', 'Absent',  'Science'),
        ('S002', '2026-06-13', 'Holiday', None),
        ('S002', '2026-06-14', 'Holiday', None),
        ('S002', '2026-06-15', 'Present', 'Mathematics'),
        ('S002', '2026-06-16', 'Present', 'English'),
        ('S002', '2026-06-17', 'Absent',  'Science'),
        ('S002', '2026-06-18', 'Present', 'History'),
        ('S002', '2026-06-19', 'Absent',  'Mathematics'),
        ('S002', '2026-06-20', 'Holiday', None),
        ('S002', '2026-06-21', 'Holiday', None),
        ('S002', '2026-06-22', 'Present', 'Science'),
        ('S002', '2026-06-23', 'Present', 'English'),
        ('S002', '2026-06-24', 'Present', 'Mathematics'),
        ('S002', '2026-06-25', 'Absent',  'History'),
        ('S002', '2026-06-26', 'Present', 'Science'),
        ('S002', '2026-06-27', 'Holiday', None),
        ('S002', '2026-06-28', 'Holiday', None),
        ('S002', '2026-06-29', 'Present', 'Mathematics'),
    ]

    
    cursor.executemany("""
        INSERT INTO attendance (student_id, date, status, subject)
        VALUES (?, ?, ?, ?)
    """, attendance_data_aman)

    # Attendance — June 2026 (mix of present/absent)
    attendance_data = [
        ('S001', '2026-06-01', 'Present', 'Mathematics'),
        ('S001', '2026-06-02', 'Present', 'Science'),
        ('S001', '2026-06-03', 'Absent',  'English'),
        ('S001', '2026-06-04', 'Present', 'History'),
        ('S001', '2026-06-05', 'Present', 'Mathematics'),
        ('S001', '2026-06-06', 'Holiday', None),
        ('S001', '2026-06-07', 'Holiday', None),
        ('S001', '2026-06-08', 'Present', 'Science'),
        ('S001', '2026-06-09', 'Present', 'English'),
        ('S001', '2026-06-10', 'Absent',  'Mathematics'),
        ('S001', '2026-06-11', 'Present', 'History'),
        ('S001', '2026-06-12', 'Present', 'Science'),
        ('S001', '2026-06-13', 'Holiday', None),
        ('S001', '2026-06-14', 'Holiday', None),
        ('S001', '2026-06-15', 'Present', 'Mathematics'),
        ('S001', '2026-06-16', 'Present', 'English'),
        ('S001', '2026-06-17', 'Absent',  'Science'),
        ('S001', '2026-06-18', 'Present', 'History'),
        ('S001', '2026-06-19', 'Present', 'Mathematics'),
        ('S001', '2026-06-20', 'Holiday', None),
        ('S001', '2026-06-21', 'Holiday', None),
        ('S001', '2026-06-22', 'Present', 'Science'),
        ('S001', '2026-06-23', 'Present', 'English'),
        ('S001', '2026-06-24', 'Present', 'Mathematics'),
        ('S001', '2026-06-25', 'Absent',  'History'),
        ('S001', '2026-06-26', 'Present', 'Science'),
        ('S001', '2026-06-27', 'Holiday', None),
        ('S001', '2026-06-28', 'Holiday', None),
        ('S001', '2026-06-29', 'Present', 'Mathematics'),
    ]
    cursor.executemany("""
        INSERT INTO attendance (student_id, date, status, subject)
        VALUES (?, ?, ?, ?)
    """, attendance_data)


    # Marks — multiple subjects and exam types
    marks_data = [
        ('S001', 'Mathematics', 'Unit Test',  88, 100, '2026-04-10'),
        ('S001', 'Mathematics', 'Midterm',    76, 100, '2026-05-15'),
        ('S001', 'Mathematics', 'Final',      91, 100, '2026-06-20'),

        ('S001', 'Science',     'Unit Test',  92, 100, '2026-04-11'),
        ('S001', 'Science',     'Midterm',    85, 100, '2026-05-16'),
        ('S001', 'Science',     'Final',      89, 100, '2026-06-21'),

        ('S001', 'English',     'Unit Test',  70, 100, '2026-04-12'),
        ('S001', 'English',     'Midterm',    65, 100, '2026-05-17'),
        ('S001', 'English',     'Final',      72, 100, '2026-06-22'),

        ('S001', 'History',     'Unit Test',  55, 100, '2026-04-13'),
        ('S001', 'History',     'Midterm',    60, 100, '2026-05-18'),
        ('S001', 'History',     'Final',      58, 100, '2026-06-23'),

        ('S001', 'Computer',    'Unit Test',  95, 100, '2026-04-14'),
        ('S001', 'Computer',    'Midterm',    93, 100, '2026-05-19'),
        ('S001', 'Computer',    'Final',      97, 100, '2026-06-24'),
    ]
    cursor.executemany("""
        INSERT INTO marks (student_id, subject, exam_type, marks, max_marks, exam_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, marks_data)

    marks_data_aman = [
        ('S002', 'Mathematics', 'Unit Test',  52, 100, '2026-04-10'),
        ('S002', 'Mathematics', 'Midterm',    48, 100, '2026-05-15'),
        ('S002', 'Mathematics', 'Final',      55, 100, '2026-06-20'),

        ('S002', 'Science',     'Unit Test',  65, 100, '2026-04-11'),
        ('S002', 'Science',     'Midterm',    70, 100, '2026-05-16'),
        ('S002', 'Science',     'Final',      68, 100, '2026-06-21'),

        ('S002', 'English',     'Unit Test',  88, 100, '2026-04-12'),
        ('S002', 'English',     'Midterm',    91, 100, '2026-05-17'),
        ('S002', 'English',     'Final',      89, 100, '2026-06-22'),

        ('S002', 'History',     'Unit Test',  92, 100, '2026-04-13'),
        ('S002', 'History',     'Midterm',    95, 100, '2026-05-18'),
        ('S002', 'History',     'Final',      90, 100, '2026-06-23'),

        ('S002', 'Computer',    'Unit Test',  74, 100, '2026-04-14'),
        ('S002', 'Computer',    'Midterm',    78, 100, '2026-05-19'),
        ('S002', 'Computer',    'Final',      80, 100, '2026-06-24'),
    ]
    cursor.executemany("""
        INSERT INTO marks (student_id, subject, exam_type, marks, max_marks, exam_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, marks_data_aman)

    # Fees
    fees_data = [
        ('S001', 'Tuition Fee',   12000, '2026-06-01', '2026-06-01', 'Paid'),
        ('S001', 'Transport Fee',  3000, '2026-06-01', '2026-06-03', 'Paid'),
        ('S001', 'Library Fee',     500, '2026-06-01', None,         'Pending'),
        ('S001', 'Tuition Fee',   12000, '2026-07-01', None,         'Pending'),
        ('S001', 'Transport Fee',  3000, '2026-07-01', None,         'Pending'),
        ('S001', 'Tuition Fee',   12000, '2026-05-01', '2026-05-02', 'Paid'),
        ('S001', 'Transport Fee',  3000, '2026-05-01', '2026-05-01', 'Paid'),
    ]
    cursor.executemany("""
        INSERT INTO fees (student_id, fee_type, amount, due_date, paid_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, fees_data)

    fees_data_aman = [
        ('S002', 'Tuition Fee',   12000, '2026-06-01', None,         'Overdue'),
        ('S002', 'Transport Fee',  3000, '2026-06-01', None,         'Pending'),
        ('S002', 'Library Fee',     500, '2026-06-01', '2026-06-02', 'Paid'),
        ('S002', 'Tuition Fee',   12000, '2026-05-01', '2026-05-05', 'Paid'),
        ('S002', 'Transport Fee',  3000, '2026-05-01', '2026-05-05', 'Paid'),
    ]
    cursor.executemany("""
        INSERT INTO fees (student_id, fee_type, amount, due_date, paid_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, fees_data_aman)

    # Homework
    homework_data = [
        ('S001', 'Mathematics', 'Solve exercises 5.1 to 5.3',           '2026-06-27', '2026-06-30', 'Pending'),
        ('S001', 'Science',     'Write notes on photosynthesis',         '2026-06-27', '2026-06-30', 'Pending'),
        ('S001', 'English',     'Write essay on climate change',         '2026-06-25', '2026-06-29', 'Pending'),
        ('S001', 'History',     'Read chapter 7 and answer questions',   '2026-06-28', '2026-07-01', 'Pending'),
        ('S001', 'Computer',    'Complete Python list exercises',        '2026-06-28', '2026-07-01', 'Pending'),
        ('S001', 'Mathematics', 'Practice quadratic equations',          '2026-06-20', '2026-06-23', 'Submitted'),
        ('S001', 'Science',     'Draw diagram of human digestive system','2026-06-18', '2026-06-21', 'Submitted'),
        ('S001', 'English',     'Grammar worksheet unit 4',              '2026-06-15', '2026-06-18', 'Submitted'),
    ]
    cursor.executemany("""
        INSERT INTO homework (student_id, subject, description, assigned_date, due_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, homework_data)

    homework_data_aman = [
        ('S002', 'Mathematics', 'Solve exercises 5.1 to 5.3',           '2026-06-27', '2026-06-30', 'Pending'),
        ('S002', 'Science',     'Write notes on photosynthesis',         '2026-06-20', '2026-06-23', 'Pending'),
        ('S002', 'English',     'Write essay on climate change',         '2026-06-25', '2026-06-29', 'Submitted'),
        ('S002', 'History',     'Read chapter 7 and answer questions',   '2026-06-28', '2026-07-01', 'Pending'),
        ('S002', 'Computer',    'Complete Python list exercises',        '2026-06-15', '2026-06-18', 'Submitted'),
    ]
    cursor.executemany("""
        INSERT INTO homework (student_id, subject, description, assigned_date, due_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, homework_data_aman)

    # Timetable — full week
    timetable_data = [
        # Monday
        ('S001', 'Monday', 1, 'Mathematics', 'Mr. Sharma',   '08:00', '08:45'),
        ('S001', 'Monday', 2, 'Science',     'Mrs. Kulkarni','08:45', '09:30'),
        ('S001', 'Monday', 3, 'English',     'Ms. Desai',    '09:45', '10:30'),
        ('S001', 'Monday', 4, 'History',     'Mr. Patil',    '10:30', '11:15'),
        ('S001', 'Monday', 5, 'Computer',    'Mr. Joshi',    '11:30', '12:15'),
        ('S001', 'Monday', 6, 'Mathematics', 'Mr. Sharma',   '13:00', '13:45'),

        # Tuesday
        ('S001', 'Tuesday', 1, 'Science',    'Mrs. Kulkarni','08:00', '08:45'),
        ('S001', 'Tuesday', 2, 'Computer',   'Mr. Joshi',    '08:45', '09:30'),
        ('S001', 'Tuesday', 3, 'Mathematics','Mr. Sharma',   '09:45', '10:30'),
        ('S001', 'Tuesday', 4, 'English',    'Ms. Desai',    '10:30', '11:15'),
        ('S001', 'Tuesday', 5, 'History',    'Mr. Patil',    '11:30', '12:15'),
        ('S001', 'Tuesday', 6, 'Science',    'Mrs. Kulkarni','13:00', '13:45'),

        # Wednesday
        ('S001', 'Wednesday', 1, 'English',  'Ms. Desai',    '08:00', '08:45'),
        ('S001', 'Wednesday', 2, 'History',  'Mr. Patil',    '08:45', '09:30'),
        ('S001', 'Wednesday', 3, 'Science',  'Mrs. Kulkarni','09:45', '10:30'),
        ('S001', 'Wednesday', 4, 'Computer', 'Mr. Joshi',    '10:30', '11:15'),
        ('S001', 'Wednesday', 5, 'Mathematics','Mr. Sharma',  '11:30', '12:15'),
        ('S001', 'Wednesday', 6, 'English',  'Ms. Desai',    '13:00', '13:45'),

        # Thursday
        ('S001', 'Thursday', 1, 'History',   'Mr. Patil',    '08:00', '08:45'),
        ('S001', 'Thursday', 2, 'Mathematics','Mr. Sharma',   '08:45', '09:30'),
        ('S001', 'Thursday', 3, 'Computer',  'Mr. Joshi',    '09:45', '10:30'),
        ('S001', 'Thursday', 4, 'Science',   'Mrs. Kulkarni','10:30', '11:15'),
        ('S001', 'Thursday', 5, 'English',   'Ms. Desai',    '11:30', '12:15'),
        ('S001', 'Thursday', 6, 'History',   'Mr. Patil',    '13:00', '13:45'),

        # Friday
        ('S001', 'Friday', 1, 'Computer',    'Mr. Joshi',    '08:00', '08:45'),
        ('S001', 'Friday', 2, 'English',     'Ms. Desai',    '08:45', '09:30'),
        ('S001', 'Friday', 3, 'History',     'Mr. Patil',    '09:45', '10:30'),
        ('S001', 'Friday', 4, 'Mathematics', 'Mr. Sharma',   '10:30', '11:15'),
        ('S001', 'Friday', 5, 'Science',     'Mrs. Kulkarni','11:30', '12:15'),
        ('S001', 'Friday', 6, 'Computer',    'Mr. Joshi',    '13:00', '13:45'),
    ]
    cursor.executemany("""
        INSERT INTO timetable (student_id, day, period, subject, teacher, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, timetable_data)

    timetable_data_aman = [
        ('S002', 'Monday', 1, 'Science',     'Mrs. Kulkarni','08:00', '08:45'),
        ('S002', 'Monday', 2, 'Mathematics', 'Mr. Sharma',   '08:45', '09:30'),
        ('S002', 'Monday', 3, 'History',     'Mr. Patil',    '09:45', '10:30'),
        ('S002', 'Monday', 4, 'English',     'Ms. Desai',    '10:30', '11:15'),
        ('S002', 'Monday', 5, 'Computer',    'Mr. Joshi',    '11:30', '12:15'),
        ('S002', 'Monday', 6, 'Science',     'Mrs. Kulkarni','13:00', '13:45'),

        ('S002', 'Tuesday', 1, 'History',    'Mr. Patil',    '08:00', '08:45'),
        ('S002', 'Tuesday', 2, 'English',    'Ms. Desai',    '08:45', '09:30'),
        ('S002', 'Tuesday', 3, 'Computer',   'Mr. Joshi',    '09:45', '10:30'),
        ('S002', 'Tuesday', 4, 'Mathematics','Mr. Sharma',   '10:30', '11:15'),
        ('S002', 'Tuesday', 5, 'Science',    'Mrs. Kulkarni','11:30', '12:15'),
        ('S002', 'Tuesday', 6, 'History',    'Mr. Patil',    '13:00', '13:45'),

        ('S002', 'Wednesday', 1, 'Computer', 'Mr. Joshi',    '08:00', '08:45'),
        ('S002', 'Wednesday', 2, 'Mathematics','Mr. Sharma',  '08:45', '09:30'),
        ('S002', 'Wednesday', 3, 'English',  'Ms. Desai',    '09:45', '10:30'),
        ('S002', 'Wednesday', 4, 'History',  'Mr. Patil',    '10:30', '11:15'),
        ('S002', 'Wednesday', 5, 'Science',  'Mrs. Kulkarni','11:30', '12:15'),
        ('S002', 'Wednesday', 6, 'Computer', 'Mr. Joshi',    '13:00', '13:45'),

        ('S002', 'Thursday', 1, 'English',   'Ms. Desai',    '08:00', '08:45'),
        ('S002', 'Thursday', 2, 'History',   'Mr. Patil',    '08:45', '09:30'),
        ('S002', 'Thursday', 3, 'Science',   'Mrs. Kulkarni','09:45', '10:30'),
        ('S002', 'Thursday', 4, 'Computer',  'Mr. Joshi',    '10:30', '11:15'),
        ('S002', 'Thursday', 5, 'Mathematics','Mr. Sharma',   '11:30', '12:15'),
        ('S002', 'Thursday', 6, 'English',   'Ms. Desai',    '13:00', '13:45'),

        ('S002', 'Friday', 1, 'Mathematics', 'Mr. Sharma',   '08:00', '08:45'),
        ('S002', 'Friday', 2, 'Computer',    'Mr. Joshi',    '08:45', '09:30'),
        ('S002', 'Friday', 3, 'History',     'Mr. Patil',    '09:45', '10:30'),
        ('S002', 'Friday', 4, 'Science',     'Mrs. Kulkarni','10:30', '11:15'),
        ('S002', 'Friday', 5, 'English',     'Ms. Desai',    '11:30', '12:15'),
        ('S002', 'Friday', 6, 'Mathematics', 'Mr. Sharma',   '13:00', '13:45'),
    ]
    cursor.executemany("""
        INSERT INTO timetable (student_id, day, period, subject, teacher, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, timetable_data_aman)
# models.py
import sqlite3
from contextlib import closing

class StudentTracker:
    def __init__(self, db_path="students.db"):
        self.db_path = db_path
        self._create_tables()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        with self._connect() as conn, closing(conn.cursor()) as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    roll_number TEXT UNIQUE NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_grades_subject ON grades(subject)")
            conn.commit()

    # Students
    def get_all_students(self):
        with self._connect() as conn, closing(conn.cursor()) as c:
            c.execute("SELECT id, name, roll_number FROM students ORDER BY id DESC")
            rows = c.fetchall()
        return [dict(r) for r in rows]

    def add_student(self, name, roll_number):
        try:
            with self._connect() as conn, closing(conn.cursor()) as c:
                c.execute("INSERT INTO students (name, roll_number) VALUES (?, ?)", (name, roll_number))
                conn.commit()
            return True, None
        except sqlite3.IntegrityError:
            return False, "Roll number already exists. Use a unique roll number."

    def find_student_by_id(self, student_id):
        with self._connect() as conn, closing(conn.cursor()) as c:
            c.execute("SELECT id, name, roll_number FROM students WHERE id=?", (student_id,))
            r = c.fetchone()
            return dict(r) if r else None

    # Grades
    def add_grade(self, student_id, subject, score):
        if not (0 <= score <= 100):
            return False, "Score must be between 0 and 100."
        with self._connect() as conn, closing(conn.cursor()) as c:
            c.execute("SELECT 1 FROM students WHERE id=?", (student_id,))
            if not c.fetchone():
                return False, "Student does not exist."
            c.execute("INSERT INTO grades (student_id, subject, score) VALUES (?, ?, ?)",
                      (student_id, subject, score))
            conn.commit()
        return True, None

    def get_grades_for_student(self, student_id):
        with self._connect() as conn, closing(conn.cursor()) as c:
            c.execute("SELECT subject, score FROM grades WHERE student_id=? ORDER BY id DESC", (student_id,))
            rows = c.fetchall()
        return [{"subject": r["subject"], "score": r["score"]} for r in rows]

    def calculate_average_for_student(self, student_id):
        with self._connect() as conn, closing(conn.cursor()) as c:
            c.execute("SELECT AVG(score) AS avgscore FROM grades WHERE student_id=?", (student_id,))
            row = c.fetchone()
            avg = row["avgscore"] if row else None
        return round(avg, 2) if avg is not None else 0

    # Reports
    def subject_topper(self, subject):
        with self._connect() as conn, closing(conn.cursor()) as c:
            c.execute("""
                SELECT s.name AS name, g.score AS score
                FROM grades g
                JOIN students s ON g.student_id = s.id
                WHERE g.subject=?
                ORDER BY g.score DESC, s.name ASC
                LIMIT 1
            """, (subject,))
            row = c.fetchone()
        return {"name": row["name"], "score": row["score"]} if row else None

    def class_average_for_subject(self, subject):
        with self._connect() as conn, closing(conn.cursor()) as c:
            c.execute("SELECT AVG(score) AS avgscore FROM grades WHERE subject=?", (subject,))
            row = c.fetchone()
            avg = row["avgscore"] if row else None
        return round(avg, 2) if avg is not None else 0

    # Backup
    def export_backup(self):
        with self._connect() as conn, closing(conn.cursor()) as c:
            c.execute("SELECT id, name, roll_number FROM students")
            students = [dict(r) for r in c.fetchall()]
            c.execute("SELECT id, student_id, subject, score FROM grades")
            grades = [dict(r) for r in c.fetchall()]
        return {"students": students, "grades": grades}


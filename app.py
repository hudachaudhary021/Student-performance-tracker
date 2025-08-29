# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from models import StudentTracker
import os
app = Flask(__name__)
# Use environment variable for secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret')

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "replace-this-secret")
    # DB file in project root (VaultofCodes/students.db)
    app.config["DATABASE"] = os.path.join(os.path.dirname(__file__), "students.db")

    tracker = StudentTracker(app.config["DATABASE"])

    @app.route("/")
    def index():
        students = tracker.get_all_students()
        return render_template("index.html", page="home", students=students)

    @app.route("/students")
    def students_page():
        students = tracker.get_all_students()
        return render_template("index.html", page="students", students=students)

    @app.route("/student/add", methods=["GET", "POST"])
    def add_student():
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            roll = (request.form.get("roll_number") or "").strip()

            if not name or not roll:
                flash("Name and Roll number are required.", "error")
                return redirect(url_for("add_student"))

            ok, msg = tracker.add_student(name, roll)
            if not ok:
                flash(msg or "Roll number already exists.", "error")
                return redirect(url_for("add_student"))

            flash("Student added successfully.", "success")
            return redirect(url_for("students_page"))
        return render_template("index.html", page="add_student")

    @app.route("/student/<int:student_id>")
    def student_detail(student_id):
        student = tracker.find_student_by_id(student_id)
        if not student:
            return render_template("index.html", page="404"), 404
        avg = tracker.calculate_average_for_student(student_id)
        grades = tracker.get_grades_for_student(student_id)
        return render_template("index.html", page="student_detail", student=student, average=avg, grades=grades)

    @app.route("/student/<int:student_id>/grades", methods=["GET", "POST"])
    def add_grades(student_id):
        student = tracker.find_student_by_id(student_id)
        if not student:
            flash("Student not found.", "error")
            return redirect(url_for("students_page"))
        if request.method == "POST":
            subject = (request.form.get("subject") or "").strip()
            score_raw = (request.form.get("score") or "").strip()
            if not subject:
                flash("Subject is required.", "error")
                return redirect(url_for("add_grades", student_id=student_id))
            try:
                score = int(score_raw)
                if not (0 <= score <= 100):
                    raise ValueError
            except Exception:
                flash("Score must be an integer between 0 and 100.", "error")
                return redirect(url_for("add_grades", student_id=student_id))
            ok, msg = tracker.add_grade(student_id, subject, score)
            if not ok:
                flash(msg or "Could not save grade.", "error")
            else:
                flash("Grade saved.", "success")
            return redirect(url_for("student_detail", student_id=student_id))
        return render_template("index.html", page="add_grades", student=student)

    @app.route("/reports", methods=["GET", "POST"])
    def reports():
        topper = None
        class_avg = None
        subject = None
        if request.method == "POST":
            subject = (request.form.get("subject") or "").strip()
            if subject:
                topper = tracker.subject_topper(subject)
                class_avg = tracker.class_average_for_subject(subject)
        return render_template("index.html", page="reports", topper=topper, class_avg=class_avg, subject=subject)

    @app.route("/backup")
    def backup():
        data = tracker.export_backup()
        return jsonify(data)

    @app.route("/favicon.ico")
    def favicon():
        return make_response(b"", 204)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("index.html", page="404"), 404

    return app

if __name__ == "__main__":
    app = create_app()
    # Use host 0.0.0.0 so you can open from phone browser and other devices on LAN
    app.run(debug=True, host="0.0.0.0", port=5000)
    

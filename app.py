from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

users = []
faculty = []
rooms = []
courses = []

# Route for the login page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "0880":
            session['role'] = 'admin'
            return redirect(url_for("admin_panel"))
        elif username.isdigit() and len(username) == 5 and password == "0770":
            session['role'] = 'teacher'
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# Route for the Dashboard (main page)
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

# Route for Generate Timetable
@app.route("/generate")
def generate():
    return render_template("generate.html", active_page="generate")

# Route for Teacher View
@app.route("/teacher")
def teacher_view():
    return render_template("teacherView.html", active_page="teacher")

# Route for Admin Panel
@app.route("/admin")
def admin_panel():
    return render_template("adminPanel.html", active_page="admin")

@app.route("/create_user")
def create_user():
    return render_template("createUser.html")

@app.route("/get_users", methods=["GET"])
def get_users():
    return {"users": users}

@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.get_json()
    users.append(data)
    return {"success": True}

@app.route("/manage_faculty")
def manage_faculty():
    return render_template(
        "management.html",
        header_title="Manage Faculty",
        item_name="Faculty",
        add_url="/add_faculty",
        get_url="/get_faculty",
        form_fields=[
            {"name": "username", "label": "Username", "type": "text"},
            {"name": "subject", "label": "Subject", "type": "text"},
        ],
    )

@app.route("/get_faculty", methods=["GET"])
def get_faculty():
    return {"items": faculty}

@app.route("/add_faculty", methods=["POST"])
def add_faculty():
    data = request.get_json()
    faculty.append(data)
    return {"success": True}

@app.route("/manage_rooms")
def manage_rooms():
    return render_template(
        "management.html",
        header_title="Manage Rooms",
        item_name="Room",
        add_url="/add_room",
        get_url="/get_rooms",
        form_fields=[
            {"name": "room_number", "label": "Room Number", "type": "text"},
            {"name": "type", "label": "Type", "type": "text"},
        ],
    )

@app.route("/get_rooms", methods=["GET"])
def get_rooms():
    return {"items": rooms}

@app.route("/add_room", methods=["POST"])
def add_room():
    data = request.get_json()
    rooms.append(data)
    return {"success": True}

@app.route("/manage_courses")
def manage_courses():
    return render_template(
        "management.html",
        header_title="Manage Courses",
        item_name="Course",
        add_url="/add_course",
        get_url="/get_courses",
        form_fields=[
            {"name": "subject_name", "label": "Subject Name", "type": "text"},
            {"name": "credit_hour", "label": "Credit Hour", "type": "text"},
        ],
    )

@app.route("/get_courses", methods=["GET"])
def get_courses():
    return {"items": courses}

@app.route("/add_course", methods=["POST"])
def add_course():
    data = request.get_json()
    courses.append(data)
    return {"success": True}

@app.route("/view_timetable")
def view_timetable():
    return render_template("selectFloor.html", active_page="view_timetable")

@app.route("/view_timetable/<int:floor_number>")
def view_timetable_floor(floor_number):
    return render_template("viewTimetable.html", floor_number=floor_number, active_page="view_timetable")

if __name__ == "__main__":
    app.run(debug=True, port=5000)

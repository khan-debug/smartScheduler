from flask import Flask, render_template, request, redirect, url_for, session
import os
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

users = []
faculty = []
rooms = []
courses = []

# Decorator for requiring login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route for the login page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "0880":
            session['role'] = 'admin'
            return redirect(url_for("admin_panel"))
        
        # Check for teacher credentials
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['role'] = 'teacher'
                return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# Route for logging out
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))


# Route for the Dashboard (main page)
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

# Route for Generate Timetable
@app.route("/generate")
@login_required
def generate():
    return render_template("generate.html", active_page="generate")

# Route for Teacher View
@app.route("/teacher")
@login_required
def teacher_view():
    return render_template("teacherView.html", active_page="teacher")

# Route for Admin Panel
@app.route("/admin")
@login_required
def admin_panel():
    return render_template("adminPanel.html", active_page="admin")

@app.route("/create_user")
@login_required
def create_user():
    return redirect(url_for("manage_users"))

@app.route("/get_users", methods=["GET"])
@login_required
def get_users():
    return {"items": users}

@app.route("/add_user", methods=["POST"])
@login_required
def add_user():
    data = request.get_json()
    users.append(data)
    return {"success": True}

@app.route("/get_user/<int:user_id>", methods=["GET"])
@login_required
def get_user(user_id):
    if 0 <= user_id < len(users):
        return users[user_id]
    return {"error": "User not found"}, 404

@app.route("/update_user/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    if 0 <= user_id < len(users):
        data = request.get_json()
        users[user_id]["username"] = data.get("username", users[user_id]["username"])
        if data.get("password"):
            users[user_id]["password"] = data.get("password")
        return {"success": True}
    return {"error": "User not found"}, 404

@app.route("/delete_user/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    if 0 <= user_id < len(users):
        users.pop(user_id)
        return {"success": True}
    return {"error": "User not found"}, 404

@app.route("/manage_users")
@login_required
def manage_users():
    return render_template(
        "management.html",
        header_title="Manage Users",
        item_name="User",
        add_url="/add_user",
        get_url="/get_users",
        form_fields=[
            {"name": "username", "label": "Username", "type": "text", "table_display": True, "form_display": True},
            {"name": "password", "label": "Password", "type": "password", "table_display": True, "form_display": True},
        ],
    )

@app.route("/manage_faculty")
@login_required
def manage_faculty():
    return render_template(
        "management.html",
        header_title="Manage Faculty",
        item_name="Faculty",
        add_url="/add_faculty",
        get_url="/get_faculty",
        form_fields=[
            {"name": "username", "label": "Username", "type": "text", "table_display": True, "form_display": True},
            {"name": "subject", "label": "Subject", "type": "text", "table_display": True, "form_display": True},
        ],
    )

@app.route("/get_faculty", methods=["GET"])
@login_required
def get_faculty():
    return {"items": faculty}

@app.route("/add_faculty", methods=["POST"])
@login_required
def add_faculty():
    data = request.get_json()
    faculty.append(data)
    return {"success": True}

@app.route("/manage_rooms")
@login_required
def manage_rooms():
    return render_template(
        "management.html",
        header_title="Manage Rooms",
        item_name="Room",
        add_url="/add_room",
        get_url="/get_rooms",
        form_fields=[
            {"name": "room_number", "label": "Room Number", "type": "text", "table_display": True, "form_display": True},
            {"name": "type", "label": "Type", "type": "select", "options": ["Lab", "Lecture Hall"], "table_display": True, "form_display": True},
            {"name": "floor_number", "label": "Floor Number", "table_display": True, "form_display": False},
        ],
    )


def _extract_floor_from_room_number(room_number_str):
    try:
        # Ensure room_number_str is treated as a string
        room_number_str = str(room_number_str)
        if len(room_number_str) > 2:
            return room_number_str[:-2]
        else:
            return "" # Or handle as error/unknown
    except (ValueError, TypeError):
        return "" # Handle cases where conversion to string fails


@app.route("/get_rooms", methods=["GET"])
@login_required
def get_rooms():
    rooms_with_floor = []
    for room in rooms:
        room_data = room.copy()
        room_number_str = room_data.get("room_number", "")
        room_data["floor_number"] = _extract_floor_from_room_number(room_number_str)
        rooms_with_floor.append(room_data)
    return {"items": rooms_with_floor}

@app.route("/add_room", methods=["POST"])
@login_required
def add_room():
    data = request.get_json()
    rooms.append(data)
    return {"success": True}

@app.route("/manage_courses")
@login_required
def manage_courses():
    return render_template(
        "management.html",
        header_title="Manage Courses",
        item_name="Course",
        add_url="/add_course",
        get_url="/get_courses",
        form_fields=[
            {"name": "course_name", "label": "Course Name", "type": "text", "table_display": True, "form_display": True},
            {"name": "credit_hour", "label": "Credit Hour", "type": "select", "options": ["1", "3"], "table_display": True, "form_display": True},
            {"name": "section_code", "label": "Section Code", "type": "text", "table_display": True, "form_display": True},
        ],
    )

@app.route("/get_courses", methods=["GET"])
@login_required
def get_courses():
    return {"items": courses}

@app.route("/add_course", methods=["POST"])
@login_required
def add_course():
    data = request.get_json()
    courses.append(data)
    return {"success": True}

@app.route("/view_timetable")
@login_required
def view_timetable():
    return render_template("selectFloor.html", active_page="view_timetable")

@app.route("/view_timetable/<int:floor_number>")
@login_required
def view_timetable_floor(floor_number):
    return render_template("viewTimetable.html", floor_number=floor_number, active_page="view_timetable")

data_stores = {
    "user": users,
    "faculty": faculty,
    "room": rooms,
    "course": courses,
}

@app.route("/get_item/<item_type>/<int:item_id>", methods=["GET"])
@login_required
def get_item(item_type, item_id):
    if item_type in data_stores:
        data_list = data_stores[item_type]
        if 0 <= item_id < len(data_list):
            return data_list[item_id]
    return {"error": "Item not found"}, 404

@app.route("/update_item/<item_type>/<int:item_id>", methods=["PUT"])
@login_required
def update_item(item_type, item_id):
    if item_type in data_stores:
        data_list = data_stores[item_type]
        if 0 <= item_id < len(data_list):
            data = request.get_json()
            for key, value in data.items():
                if key in data_list[item_id]:
                    data_list[item_id][key] = value
            return {"success": True}
    return {"error": "Item not found"}, 404

@app.route("/delete_item/<item_type>/<int:item_id>", methods=["DELETE"])
@login_required
def delete_item(item_type, item_id):
    if item_type in data_stores:
        data_list = data_stores[item_type]
        if 0 <= item_id < len(data_list):
            data_list.pop(item_id)
            return {"success": True}
    return {"error": "Item not found"}, 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
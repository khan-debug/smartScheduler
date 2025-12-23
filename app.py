from flask import Flask, render_template, request, redirect, url_for, session
import os
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

users = []
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
                session['username'] = user['username']
                return redirect(url_for("teacher_view"))

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
    teacher_count = len(users)
    course_count = len(courses)
    room_count = len(rooms)
    return render_template("dashboard.html", active_page="dashboard", teacher_count=teacher_count, course_count=course_count, room_count=room_count)

# Route for Generate Timetable
@app.route("/generate")
@login_required
def generate():
    return render_template("generate.html", active_page="generate")

@app.route("/view_generated_timetable")
@login_required
def view_generated_timetable():
    return render_template("viewGeneratedTimetable.html", active_page="generate")

# Route for Teacher View
@app.route("/teacher")
@login_required
def teacher_view():
    return render_template("teacherView.html", active_page="teacher", username=session.get('username'))

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

data_stores = {
    "user": users,
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
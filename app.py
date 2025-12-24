from flask import Flask, render_template, request, redirect, url_for, session
import os
from functools import wraps
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = os.urandom(24)

users = []
rooms = []
courses = []

# Load email settings
def load_email_settings():
    try:
        with open('EmailSettings Enabled.txt', 'r') as f:
            content = f.read()
            # Wrap content in braces to make it valid JSON
            json_content = '{' + content.strip().rstrip(',') + '}'
            settings = json.loads(json_content)
            email_config = settings.get('EmailSettings', {})
            print(f"Email settings loaded successfully: Enabled={email_config.get('Enabled')}")
            return email_config
    except Exception as e:
        print(f"Error loading email settings: {e}")
        import traceback
        traceback.print_exc()
        return None

email_settings = load_email_settings()

# Function to send email
def send_user_email(to_email, username, password):
    """Send email to new/updated user with their credentials"""
    if not email_settings or not email_settings.get('Enabled'):
        raise Exception("Email settings not configured or disabled")

    smtp_config = email_settings.get('Smtp', {})
    from_email = email_settings.get('FromEmail')
    email_name = email_settings.get('EmailName', 'SmartScheduler')
    subject = email_settings.get('Subject', 'Account Created')

    # Create email message
    msg = MIMEMultipart()
    msg['From'] = f"{email_name} <{from_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    # Email body
    body = f"""Dear {username},

Congratulations! Your registration to the portal has been successful.

    Login Username: {username}
    Temporary Password: {password}

We strongly recommend that you change your password immediately after your first login for security purposes.

We wish you a smooth and successful experience using the portal.

This is an automated message. Please do not reply to this email.

Best regards,

The Portal Team
"""

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(smtp_config.get('Server'), smtp_config.get('Port'))
        server.starttls()
        server.login(smtp_config.get('Username'), smtp_config.get('Password'))

        # Send email
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")

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

        return render_template("auth/login.html", error="Invalid credentials")
    return render_template("auth/login.html")

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
    return render_template("pages/dashboard.html", active_page="dashboard", teacher_count=teacher_count, course_count=course_count, room_count=room_count)

# Route for Generate Timetable
@app.route("/generate")
@login_required
def generate():
    return render_template("pages/generate.html", active_page="generate")

@app.route("/view_generated_timetable")
@login_required
def view_generated_timetable():
    return render_template(
        "timetables/timetable_base.html",
        active_page="generate",
        page_title="View Generated Timetable",
        hide_top_bar=False,
        show_back_button=True,
        show_teacher_header=False,
        show_page_title=True,
        page_title_text="Generated Timetable"
    )

# Route for Teacher View
@app.route("/teacher")
@login_required
def teacher_view():
    return render_template(
        "timetables/timetable_base.html",
        active_page="teacher",
        page_title="Timetable",
        hide_top_bar=False,
        show_back_button=False,
        show_teacher_header=True,
        show_page_title=False,
        username=session.get('username')
    )

# Route for Admin Panel
@app.route("/admin")
@login_required
def admin_panel():
    return render_template("pages/adminPanel.html", active_page="admin")

@app.route("/get_users", methods=["GET"])
@login_required
def get_users():
    return {"items": users}

@app.route("/add_user", methods=["POST"])
@login_required
def add_user():
    data = request.get_json()

    # Extract user details
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    # Validate required fields
    if not email:
        return {"success": False, "error": "Email address is required"}, 400

    # Try to send email first
    try:
        send_user_email(email, username, password)
    except Exception as e:
        return {"success": False, "error": f"Failed to send email: {str(e)}"}, 500

    # If email sent successfully, add user
    users.append(data)
    return {"success": True}

@app.route("/manage_users")
@login_required
def manage_users():
    from_dashboard = request.args.get('from_dashboard', 'false').lower() == 'true'
    return render_template(
        "management/management.html",
        header_title="Manage Users",
        item_name="User",
        add_url="/add_user",
        get_url="/get_users",
        form_fields=[
            {"name": "username", "label": "Username", "type": "text", "table_display": True, "form_display": True},
            {"name": "email", "label": "Email Address", "type": "email", "table_display": True, "form_display": True},
            {"name": "password", "label": "Password", "type": "password", "table_display": False, "form_display": True},
            {"name": "confirm_password", "label": "Confirm Password", "type": "password", "table_display": False, "form_display": True},
        ],
        from_dashboard=from_dashboard,
    )

@app.route("/manage_rooms")
@login_required
def manage_rooms():
    from_dashboard = request.args.get('from_dashboard', 'false').lower() == 'true'
    return render_template(
        "management/management.html",
        header_title="Manage Rooms",
        item_name="Room",
        add_url="/add_room",
        get_url="/get_rooms",
        form_fields=[
            {"name": "room_number", "label": "Room Number", "type": "text", "table_display": True, "form_display": True},
            {"name": "type", "label": "Type", "type": "select", "options": ["Lab", "Lecture Hall"], "table_display": True, "form_display": True},
            {"name": "floor_number", "label": "Floor Number", "table_display": True, "form_display": False},
        ],
        from_dashboard=from_dashboard,
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
    from_dashboard = request.args.get('from_dashboard', 'false').lower() == 'true'
    return render_template(
        "management/management.html",
        header_title="Manage Courses",
        item_name="Course",
        add_url="/add_course",
        get_url="/get_courses",
        form_fields=[
            {"name": "course_name", "label": "Course Name", "type": "text", "table_display": True, "form_display": True},
            {"name": "credit_hour", "label": "Credit Hour", "type": "select", "options": ["1", "3"], "table_display": True, "form_display": True},
            {"name": "section_code", "label": "Section Code", "type": "text", "table_display": True, "form_display": True},
        ],
        from_dashboard=from_dashboard,
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
    return render_template("pages/selectFloor.html", active_page="view_timetable")

@app.route("/view_timetable/<int:floor_number>")
@login_required
def view_timetable_floor(floor_number):
    return render_template(
        "timetables/timetable_base.html",
        floor_number=floor_number,
        active_page="view_timetable",
        page_title="View Timetable",
        hide_top_bar=True,
        show_back_button=True,
        show_teacher_header=False,
        show_page_title=True,
        page_title_text=f"Weekly Timetable - Floor {floor_number}"
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

            # If updating a user, send email notification
            if item_type == "user":
                username = data.get('username')
                password = data.get('password')
                email = data.get('email')

                # Validate email exists
                if not email:
                    return {"success": False, "error": "Email address is required"}, 400

                # Try to send email first
                try:
                    send_user_email(email, username, password)
                except Exception as e:
                    return {"success": False, "error": f"Failed to send email: {str(e)}"}, 500

            # Update the item
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
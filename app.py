from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from functools import wraps
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pymongo import MongoClient
from bson import ObjectId
import certifi
import random
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB Connection
MONGO_URI = "mongodb+srv://aarij:aarij0990@smartscheduler.tqtyuhp.mongodb.net/?retryWrites=true&w=majority&appName=smartscheduler"

# Try to connect to MongoDB
try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000
    )
    # Test connection
    client.admin.command('ping')
    db = client['smartscheduler_db']

    # Collections
    users_collection = db['users']
    rooms_collection = db['rooms']
    courses_collection = db['courses']

    print("✓ MongoDB connection successful!")
except Exception as e:
    print(f"✗ MongoDB connection failed: {str(e)[:200]}")
    print("\nERROR: Cannot connect to MongoDB. Please check:")
    print("1. MongoDB Atlas Network Access - Add your IP address")
    print("2. MongoDB cluster status - Ensure it's running")
    print("3. OpenSSL compatibility - Python 3.14.2 + OpenSSL 3.6.0 may be too new")
    print("\nApplication will not function without database connection.")
    import sys
    sys.exit(1)

# Load email settings
def load_email_settings():
    try:
        with open('config/email_settings.txt', 'r') as f:
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

# Function to send OTP email
def send_otp_email(to_email, otp):
    """Send OTP email to admin for password change verification"""
    if not email_settings or not email_settings.get('Enabled'):
        raise Exception("Email settings not configured or disabled")

    smtp_config = email_settings.get('Smtp', {})
    from_email = email_settings.get('FromEmail')
    email_name = email_settings.get('EmailName', 'SmartScheduler')

    # Create email message
    msg = MIMEMultipart()
    msg['From'] = f"{email_name} <{from_email}>"
    msg['To'] = to_email
    msg['Subject'] = 'Admin Password Change - OTP Verification'

    # Email body
    body = f"""Dear Admin,

You have requested to change your admin password.

Your One-Time Password (OTP) is: {otp}

This OTP is valid for 10 minutes only.

If you did not request this password change, please ignore this email and your password will remain unchanged.

This is an automated message. Please do not reply to this email.

Best regards,

The SmartScheduler System
"""

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to SMTP server
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

        # Check admin credentials
        if username == "admin":
            # Try to load custom admin password from file
            admin_password = "0880"  # Default password
            admin_creds_path = 'config/admin_credentials.txt'

            if os.path.exists(admin_creds_path):
                try:
                    with open(admin_creds_path, 'r') as f:
                        creds = json.load(f)
                        admin_password = creds.get('password', "0880")
                except:
                    admin_password = "0880"  # Fallback to default on error

            if password == admin_password:
                session['role'] = 'admin'
                return redirect(url_for("admin_panel"))

        # Check for teacher credentials in MongoDB using registration_number
        user = users_collection.find_one({'registration_number': username, 'password': password})
        if user:
            session['role'] = 'teacher'
            session['username'] = user['username']  # Store actual username in session
            session['registration_number'] = user['registration_number']  # Store reg number too
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
    teacher_count = users_collection.count_documents({})
    course_count = courses_collection.count_documents({})
    room_count = rooms_collection.count_documents({})
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

@app.route("/manual_timetable_edit")
@login_required
def manual_timetable_edit():
    return render_template("pages/selectFloorEdit.html", active_page="generate")

@app.route("/edit_timetable/<int:floor_number>")
@login_required
def edit_timetable_floor(floor_number):
    return render_template(
        "timetables/timetable_base.html",
        floor_number=floor_number,
        active_page="generate",
        page_title="Edit Timetable",
        hide_top_bar=True,
        show_back_button=True,
        show_teacher_header=False,
        show_page_title=True,
        page_title_text=f"Edit Timetable - Floor {floor_number}",
        edit_mode=True
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

# Route for Teacher About (Profile)
@app.route("/teacher/about")
@login_required
def teacher_about():
    """Show teacher profile with their information and assigned courses"""
    if session.get('role') != 'teacher':
        return redirect(url_for('login'))

    # Get teacher information from session
    teacher_username = session.get('username')
    teacher_reg_number = session.get('registration_number')

    # Fetch complete teacher info from database
    teacher = users_collection.find_one({'registration_number': teacher_reg_number})

    # Get courses assigned to this teacher
    assigned_courses = list(courses_collection.find({
        'teacher_registration': teacher_reg_number
    }))

    return render_template(
        "pages/teacher_about.html",
        active_page="teacher_about",
        teacher=teacher,
        assigned_courses=assigned_courses
    )

# Route for Admin Panel
@app.route("/admin")
@login_required
def admin_panel():
    return render_template("pages/adminPanel.html", active_page="admin")

# Route to initiate admin password change (send OTP)
@app.route("/request_admin_password_change", methods=["POST"])
@login_required
def request_admin_password_change():
    """Generate OTP and send to admin email"""
    try:
        # Check if user is admin
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP in session with timestamp (valid for 10 minutes)
        session['admin_password_otp'] = otp
        session['otp_timestamp'] = time.time()

        # Get admin email from settings (using FromEmail as admin email)
        admin_email = email_settings.get('FromEmail')
        if not admin_email:
            return jsonify({'success': False, 'error': 'Admin email not configured'}), 500

        # Send OTP email
        send_otp_email(admin_email, otp)

        return jsonify({
            'success': True,
            'message': f'OTP has been sent to {admin_email}',
            'email': admin_email
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Route to verify OTP and change admin password
@app.route("/change_admin_password", methods=["POST"])
@login_required
def change_admin_password():
    """Verify OTP and change admin password"""
    try:
        # Check if user is admin
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403

        data = request.get_json()
        entered_otp = data.get('otp')
        new_password = data.get('new_password')

        # Validate inputs
        if not entered_otp or not new_password:
            return jsonify({'success': False, 'error': 'OTP and new password are required'}), 400

        # Check if OTP exists in session
        if 'admin_password_otp' not in session or 'otp_timestamp' not in session:
            return jsonify({'success': False, 'error': 'No OTP request found. Please request OTP first.'}), 400

        # Check if OTP is expired (10 minutes = 600 seconds)
        otp_age = time.time() - session['otp_timestamp']
        if otp_age > 600:
            # Clear expired OTP
            session.pop('admin_password_otp', None)
            session.pop('otp_timestamp', None)
            return jsonify({'success': False, 'error': 'OTP has expired. Please request a new one.'}), 400

        # Verify OTP
        if entered_otp != session['admin_password_otp']:
            return jsonify({'success': False, 'error': 'Invalid OTP. Please try again.'}), 400

        # OTP is valid, update password in login route
        # Note: Since admin password is hardcoded in the login route, we'll need to store it somewhere
        # For now, we'll store it in session and check it in the login route
        # A better approach would be to store admin credentials in database

        # Store new password in a simple file or environment variable
        # For this implementation, we'll create a simple admin credentials file
        admin_creds_path = 'config/admin_credentials.txt'
        os.makedirs('config', exist_ok=True)

        with open(admin_creds_path, 'w') as f:
            json.dump({'password': new_password}, f)

        # Clear OTP from session
        session.pop('admin_password_otp', None)
        session.pop('otp_timestamp', None)

        return jsonify({
            'success': True,
            'message': 'Admin password changed successfully! Please login again with your new password.'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/get_users", methods=["GET"])
@login_required
def get_users():
    users_list = list(users_collection.find({}))
    # Convert ObjectId to string for JSON serialization
    for user in users_list:
        user['_id'] = str(user['_id'])
    return {"items": users_list}

@app.route("/add_user", methods=["POST"])
@login_required
def add_user():
    data = request.get_json()

    # Extract user details
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    registration_number = data.get('registration_number')

    # Validate required fields
    if not username:
        return {"success": False, "error": "Username is required"}, 400
    if not registration_number:
        return {"success": False, "error": "Registration number is required"}, 400
    if not email:
        return {"success": False, "error": "Email address is required"}, 400
    if not password:
        return {"success": False, "error": "Password is required"}, 400

    # Check if username already exists
    if users_collection.find_one({'username': username}):
        return {"success": False, "error": "Username already exists"}, 400

    # Try to send email first
    try:
        send_user_email(email, username, password)
    except Exception as e:
        return {"success": False, "error": f"Failed to send email: {str(e)}"}, 500

    # Remove confirm_password from data before saving to database
    user_data = {
        'username': username,
        'registration_number': registration_number,
        'email': email,
        'password': password
    }

    # If email sent successfully, add user to MongoDB
    users_collection.insert_one(user_data)
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
            {"name": "registration_number", "label": "Registration Number", "type": "text", "table_display": True, "form_display": True},
            {"name": "email", "label": "Email Address", "type": "email", "table_display": True, "form_display": True},
            {"name": "password", "label": "Password", "type": "password", "table_display": False, "form_display": True},
            {"name": "confirm_password", "label": "Confirm Password", "type": "password", "table_display": False, "form_display": True},
        ],
        from_dashboard=from_dashboard,
    )

@app.route("/manage_rooms")
@login_required
def manage_rooms():
    # Show floor selection page
    return render_template("management/room_floor_selection.html", active_page="admin")

@app.route("/manage_rooms/all")
@login_required
def manage_rooms_all():
    # View all rooms in one table
    from_dashboard = request.args.get('from_dashboard', 'false').lower() == 'true'
    return render_template(
        "management/management.html",
        header_title="Manage Rooms - All Floors",
        item_name="Room",
        add_url="/add_room",
        get_url="/get_rooms",
        form_fields=[
            {"name": "room_number", "label": "Room Number", "type": "text", "table_display": True, "form_display": True},
            {"name": "type", "label": "Type", "type": "select", "options": ["Lab", "Lecture Hall"], "table_display": True, "form_display": True},
            {"name": "floor_number", "label": "Floor Number", "table_display": True, "form_display": False},
        ],
        from_dashboard=from_dashboard,
        show_back_button=True,
        back_url="/manage_rooms"
    )

@app.route("/manage_rooms/floor/<int:floor_number>")
@login_required
def manage_rooms_floor(floor_number):
    # View rooms for specific floor
    return render_template(
        "management/management.html",
        header_title=f"Manage Rooms - Floor {floor_number}",
        item_name="Room",
        add_url="/add_room",
        get_url=f"/get_rooms_by_floor/{floor_number}",
        form_fields=[
            {"name": "room_number", "label": "Room Number", "type": "text", "table_display": True, "form_display": True},
            {"name": "type", "label": "Type", "type": "select", "options": ["Lab", "Lecture Hall"], "table_display": True, "form_display": True},
            {"name": "floor_number", "label": "Floor Number", "table_display": True, "form_display": False},
        ],
        from_dashboard=False,
        show_back_button=True,
        back_url="/manage_rooms"
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
    rooms_list = list(rooms_collection.find({}))
    rooms_with_floor = []
    for room in rooms_list:
        room_data = room.copy()
        room_data['_id'] = str(room_data['_id'])
        room_number_str = room_data.get("room_number", "")
        room_data["floor_number"] = _extract_floor_from_room_number(room_number_str)
        rooms_with_floor.append(room_data)
    return {"items": rooms_with_floor}

@app.route("/add_room", methods=["POST"])
@login_required
def add_room():
    data = request.get_json()
    room_number = data.get('room_number')

    # Validate room number format (should be 3 digits minimum)
    if not room_number or len(str(room_number)) < 3:
        return {"success": False, "error": "Room number must be at least 3 digits (e.g., 101)"}, 400

    # Extract floor from room number
    floor = str(room_number)[:-2]
    room_on_floor = str(room_number)[-2:]

    # Get all rooms on this floor
    floor_rooms = list(rooms_collection.find({}))
    floor_rooms = [r for r in floor_rooms if str(r.get('room_number', '')).startswith(floor)]

    if floor_rooms:
        # Sort rooms to find the highest room number on this floor
        room_numbers = sorted([int(r.get('room_number', 0)) for r in floor_rooms])
        expected_next = room_numbers[-1] + 1

        # Check if the new room number is sequential
        if int(room_number) != expected_next:
            return {
                "success": False,
                "error": f"Room number must be sequential. Expected {expected_next}, got {room_number}. No gaps allowed."
            }, 400

    rooms_collection.insert_one(data)
    return {"success": True}

@app.route("/bulk_create_rooms", methods=["POST"])
@login_required
def bulk_create_rooms():
    data = request.get_json()
    floor_input = data.get('floors', '').strip()
    rooms_per_floor = data.get('rooms_per_floor')
    room_type = data.get('type')

    # Validate inputs
    if not floor_input or not rooms_per_floor or not room_type:
        return {"success": False, "error": "All fields are required"}, 400

    try:
        rooms_per_floor = int(rooms_per_floor)
        if rooms_per_floor < 1:
            return {"success": False, "error": "Rooms per floor must be at least 1"}, 400
    except ValueError:
        return {"success": False, "error": "Rooms per floor must be a number"}, 400

    # Parse floor input (single floor or range)
    floors = []
    if '-' in floor_input:
        # Range like "1-6"
        try:
            start, end = floor_input.split('-')
            start, end = int(start.strip()), int(end.strip())
            if start > end:
                return {"success": False, "error": "Invalid floor range"}, 400
            floors = list(range(start, end + 1))
        except:
            return {"success": False, "error": "Invalid floor format. Use single number (1) or range (1-6)"}, 400
    else:
        # Single floor
        try:
            floors = [int(floor_input)]
        except:
            return {"success": False, "error": "Floor must be a number"}, 400

    # Auto-fill missing floors to avoid gaps
    # Get existing floors from database
    all_rooms = list(rooms_collection.find({}))
    existing_floors = set()
    for room in all_rooms:
        room_number = str(room.get('room_number', ''))
        if len(room_number) >= 3:
            floor_num = room_number[:-2]
            existing_floors.add(int(floor_num))

    # Find the range we need to cover
    if existing_floors:
        min_existing = min(existing_floors)
        max_requested = max(floors)
        min_requested = min(floors)

        # Determine the full range we need to create (fill gaps)
        start_floor = min(min_existing, min_requested)
        end_floor = max_requested

        # Create a complete range with no gaps
        floors_to_create = list(range(start_floor, end_floor + 1))
    else:
        # No existing floors, just create the requested ones
        floors_to_create = floors

    # Create rooms for each floor
    created_count = 0
    updated_count = 0
    gap_filled_count = 0

    for floor in floors_to_create:
        # Check if this floor was in the original request or is a gap-fill
        is_gap_fill = floor not in floors

        # Delete existing rooms on this floor
        deleted = rooms_collection.delete_many({
            "room_number": {"$regex": f"^{floor}"}
        })

        if deleted.deleted_count > 0:
            updated_count += 1

        # Create new rooms
        for room_num in range(1, rooms_per_floor + 1):
            room_number = f"{floor}{room_num:02d}"  # Format: 101, 102, etc.
            room_data = {
                "room_number": room_number,
                "type": room_type
            }
            rooms_collection.insert_one(room_data)
            created_count += 1

        if is_gap_fill:
            gap_filled_count += 1

    # Build message
    message_parts = []
    if gap_filled_count > 0:
        message_parts.append(f"Auto-filled {gap_filled_count} missing floor(s)")

    total_floors = len(floors_to_create)
    message_parts.append(f"Created {created_count} rooms on {total_floors} floor(s)")

    if updated_count > 0:
        message_parts.append(f"Updated {updated_count} existing floor(s)")

    return {
        "success": True,
        "message": " | ".join(message_parts)
    }

@app.route("/get_floors", methods=["GET"])
@login_required
def get_floors():
    """Get all floors with room counts"""
    all_rooms = list(rooms_collection.find({}))

    # Group rooms by floor
    floors = {}
    for room in all_rooms:
        room_number = str(room.get('room_number', ''))
        if len(room_number) >= 3:
            floor = room_number[:-2]
            if floor not in floors:
                floors[floor] = 0
            floors[floor] += 1

    # Convert to list format
    floor_list = [
        {"floor": int(floor), "count": count}
        for floor, count in sorted(floors.items(), key=lambda x: int(x[0]))
    ]

    return {"floors": floor_list}

@app.route("/get_rooms_by_floor/<int:floor_number>", methods=["GET"])
@login_required
def get_rooms_by_floor(floor_number):
    """Get all rooms on a specific floor"""
    rooms_list = list(rooms_collection.find({
        "room_number": {"$regex": f"^{floor_number}"}
    }))

    rooms_with_floor = []
    for room in rooms_list:
        room_data = room.copy()
        room_data['_id'] = str(room_data['_id'])
        room_number_str = room_data.get("room_number", "")
        room_data["floor_number"] = _extract_floor_from_room_number(room_number_str)
        rooms_with_floor.append(room_data)

    # Sort by room number
    rooms_with_floor.sort(key=lambda x: int(x.get('room_number', 0)))

    return {"items": rooms_with_floor}

@app.route("/delete_floor/<int:floor_number>", methods=["DELETE"])
@login_required
def delete_floor(floor_number):
    """Delete an entire floor and all its rooms"""
    try:
        # Delete all rooms on this floor
        result = rooms_collection.delete_many({
            "room_number": {"$regex": f"^{floor_number}"}
        })

        if result.deleted_count > 0:
            return {
                "success": True,
                "message": f"Deleted floor {floor_number} ({result.deleted_count} rooms)"
            }
        else:
            return {
                "success": False,
                "error": f"Floor {floor_number} not found or already empty"
            }, 404

    except Exception as e:
        return {
            "success": False,
            "error": f"Error deleting floor: {str(e)}"
        }, 500

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
            {"name": "shift", "label": "Shift Time", "type": "select", "options": ["Morning", "Evening"], "table_display": False, "form_display": True},
            {"name": "section_digits", "label": "Section Code (3 digits)", "type": "text", "table_display": False, "form_display": True, "maxlength": "3", "pattern": "[0-9]{3}", "placeholder": "e.g., 123"},
            {"name": "section_code", "label": "Section Code", "type": "text", "table_display": True, "form_display": True, "readonly": True},
            {"name": "teacher_registration", "label": "Teacher Registration Number", "type": "text", "table_display": False, "form_display": True, "placeholder": "Enter registration number"},
            {"name": "teacher_name", "label": "Teacher Name", "type": "text", "table_display": True, "form_display": True, "readonly": True, "placeholder": "Auto-filled from registration"},
        ],
        from_dashboard=from_dashboard,
    )

@app.route("/lookup_teacher/<registration_number>", methods=["GET"])
@login_required
def lookup_teacher(registration_number):
    """Lookup teacher by registration number and return their details"""
    try:
        teacher = users_collection.find_one({'registration_number': registration_number})
        if teacher:
            return jsonify({
                'success': True,
                'teacher': {
                    'registration_number': teacher.get('registration_number'),
                    'username': teacher.get('username'),
                    'email': teacher.get('email')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Teacher not found with this registration number'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/get_courses", methods=["GET"])
@login_required
def get_courses():
    courses_list = list(courses_collection.find({}))
    # Convert ObjectId to string for JSON serialization
    for course in courses_list:
        course['_id'] = str(course['_id'])
    return {"items": courses_list}

@app.route("/add_course", methods=["POST"])
@login_required
def add_course():
    data = request.get_json()
    courses_collection.insert_one(data)
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
    "user": users_collection,
    "room": rooms_collection,
    "course": courses_collection,
}

@app.route("/get_item/<item_type>/<int:item_id>", methods=["GET"])
@login_required
def get_item(item_type, item_id):
    if item_type in data_stores:
        collection = data_stores[item_type]
        # Get all items and find by index
        items_list = list(collection.find({}))
        if 0 <= item_id < len(items_list):
            item = items_list[item_id]
            item['_id'] = str(item['_id'])
            return item
    return {"error": "Item not found"}, 404

@app.route("/update_item/<item_type>/<int:item_id>", methods=["PUT"])
@login_required
def update_item(item_type, item_id):
    if item_type in data_stores:
        collection = data_stores[item_type]
        # Get all items and find by index
        items_list = list(collection.find({}))
        if 0 <= item_id < len(items_list):
            data = request.get_json()
            item_to_update = items_list[item_id]

            # If updating a user, send email notification and validate
            if item_type == "user":
                username = data.get('username')
                password = data.get('password')
                email = data.get('email')
                registration_number = data.get('registration_number')

                # Validate required fields
                if not username:
                    return {"success": False, "error": "Username is required"}, 400
                if not registration_number:
                    return {"success": False, "error": "Registration number is required"}, 400
                if not email:
                    return {"success": False, "error": "Email address is required"}, 400
                if not password:
                    return {"success": False, "error": "Password is required"}, 400

                # Try to send email first
                try:
                    send_user_email(email, username, password)
                except Exception as e:
                    return {"success": False, "error": f"Failed to send email: {str(e)}"}, 500

                # Remove confirm_password from data before updating database
                update_data = {
                    'username': username,
                    'registration_number': registration_number,
                    'email': email,
                    'password': password
                }
            else:
                update_data = data

            # Update the item in MongoDB
            collection.update_one(
                {"_id": item_to_update["_id"]},
                {"$set": update_data}
            )
            return {"success": True}
    return {"error": "Item not found"}, 404

@app.route("/delete_item/<item_type>/<int:item_id>", methods=["DELETE"])
@login_required
def delete_item(item_type, item_id):
    if item_type in data_stores:
        collection = data_stores[item_type]
        # Get all items and find by index
        items_list = list(collection.find({}))
        if 0 <= item_id < len(items_list):
            item_to_delete = items_list[item_id]
            collection.delete_one({"_id": item_to_delete["_id"]})
            return {"success": True}
    return {"error": "Item not found"}, 404

if __name__ == "__main__":
    # Test MongoDB connection
    try:
        client.admin.command('ping')
        print("✓ Successfully connected to MongoDB!")
        print(f"✓ Database: {db.name}")
        print(f"✓ Collections: users, rooms, courses")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        print("Please check your connection string and network access.")

    app.run(debug=True, port=5000)

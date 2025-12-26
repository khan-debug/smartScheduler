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
import string
import time
import csv
import io
from datetime import datetime

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
    floors_collection = db['floors']
    scheduled_classes_collection = db['scheduled_classes']

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

# Function to generate random password
def generate_password(length=10):
    """Generate a random password with letters, digits, and special characters"""
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = '@#$%&*'

    # Ensure at least one character from each set
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special_chars)
    ]

    # Fill the rest with random characters from all sets
    all_chars = lowercase + uppercase + digits + special_chars
    password += [random.choice(all_chars) for _ in range(length - 4)]

    # Shuffle to avoid predictable pattern
    random.shuffle(password)

    return ''.join(password)

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

# Function to send course assignment email
def send_course_assignment_email(to_email, teacher_name, course_details):
    """Send email to teacher about course assignment"""
    if not email_settings or not email_settings.get('Enabled'):
        raise Exception("Email settings not configured or disabled")

    smtp_config = email_settings.get('Smtp', {})
    from_email = email_settings.get('FromEmail')
    email_name = email_settings.get('EmailName', 'SmartScheduler')

    # Create email message
    msg = MIMEMultipart()
    msg['From'] = f"{email_name} <{from_email}>"
    msg['To'] = to_email
    msg['Subject'] = 'Course Assignment Notification'

    # Email body
    body = f"""Dear {teacher_name},

You have been assigned to teach a new course.

Course Details:
- Course Name: {course_details['course_name']}
- Section Code: {course_details['section_code']}
- Course Type: {course_details['course_type']}
- Credit Hours: {course_details['credit_hour']}
- Shift: {course_details['shift']}

You can view the full course details and timetable in your SmartScheduler dashboard.

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

@app.route("/manual_edit_by_course")
@login_required
def manual_edit_by_course():
    """Show course list for manual scheduling"""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template("pages/editByCourse.html", active_page="generate")

@app.route("/manual_edit_by_room")
@login_required
def manual_edit_by_room():
    """Show room list for manual scheduling"""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    # TODO: Implement room-based editing
    return render_template("pages/editByRoom.html", active_page="generate")

@app.route("/get_all_courses_with_sections", methods=["GET"])
@login_required
def get_all_courses_with_sections():
    """Get all courses with their section codes"""
    try:
        courses_list = list(courses_collection.find({}))
        courses_data = []

        for course in courses_list:
            # Get teacher name
            teacher = users_collection.find_one({'registration_number': course.get('teacher_registration')})
            teacher_name = teacher.get('username', 'Unknown') if teacher else 'Unknown'

            # Handle both old (section_code) and new (section_codes) format
            sections = course.get('section_codes', [])
            if not sections and course.get('section_code'):
                # Old format - convert to array
                sections = [course.get('section_code')]

            courses_data.append({
                '_id': str(course.get('_id')),
                'course_name': course.get('course_name', ''),
                'credit_hour': course.get('credit_hour', 0),
                'course_type': course.get('course_type', ''),
                'shift': course.get('shift', ''),
                'teacher_name': teacher_name,
                'teacher_registration': course.get('teacher_registration', ''),
                'sections': sections
            })

        # Sort by course name
        courses_data.sort(key=lambda x: x['course_name'])

        return jsonify({
            'success': True,
            'courses': courses_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/get_course_details", methods=["GET"])
@login_required
def get_course_details():
    """Get details of a specific course"""
    try:
        from bson.objectid import ObjectId

        course_id = request.args.get('course_id')
        section_code = request.args.get('section_code')

        if not course_id or not section_code:
            return jsonify({'success': False, 'error': 'Missing course_id or section_code'}), 400

        # Get course from database
        course = courses_collection.find_one({'_id': ObjectId(course_id)})

        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404

        # Verify section exists - handle both old (section_code) and new (section_codes) format
        section_codes = course.get('section_codes', [])
        if not section_codes and course.get('section_code'):
            # Old format - convert to array
            section_codes = [course.get('section_code')]

        if section_code not in section_codes:
            return jsonify({'success': False, 'error': 'Section not found'}), 404

        # Get teacher name
        teacher = users_collection.find_one({'registration_number': course.get('teacher_registration')})
        teacher_name = teacher.get('username', 'Unknown') if teacher else 'Unknown'

        course_data = {
            '_id': str(course.get('_id')),
            'course_name': course.get('course_name', ''),
            'credit_hour': course.get('credit_hour', 0),
            'course_type': course.get('course_type', ''),
            'shift': course.get('shift', ''),
            'teacher_name': teacher_name,
            'teacher_registration': course.get('teacher_registration', '')
        }

        return jsonify({
            'success': True,
            'course': course_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/schedule_class")
@login_required
def schedule_class_page():
    """Show scheduling form for a course section"""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template("pages/scheduleClass.html", active_page="generate")

@app.route("/save_scheduled_class", methods=["POST"])
@login_required
def save_scheduled_class():
    """Save a scheduled class to the database"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        from bson.objectid import ObjectId

        data = request.get_json()
        course_id = data.get('course_id')
        section_code = data.get('section_code')
        day = data.get('day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        room_number = data.get('room_number')

        # Validation
        if not all([course_id, section_code, day, start_time, end_time, room_number]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Get course details
        course = courses_collection.find_one({'_id': ObjectId(course_id)})
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404

        # Verify section exists - handle both old (section_code) and new (section_codes) format
        section_codes = course.get('section_codes', [])
        if not section_codes and course.get('section_code'):
            # Old format - convert to array
            section_codes = [course.get('section_code')]

        if section_code not in section_codes:
            return jsonify({'success': False, 'error': 'Section not found'}), 404

        # Get room details
        room = rooms_collection.find_one({'room_number': room_number})
        if not room:
            return jsonify({'success': False, 'error': 'Room not found'}), 404

        # Check for conflicts
        # 1. Check if room is already occupied at this time
        existing_schedule = scheduled_classes_collection.find_one({
            'room_number': room_number,
            'day': day,
            '$or': [
                {
                    'start_time': {'$lte': start_time},
                    'end_time': {'$gt': start_time}
                },
                {
                    'start_time': {'$lt': end_time},
                    'end_time': {'$gte': end_time}
                },
                {
                    'start_time': {'$gte': start_time},
                    'end_time': {'$lte': end_time}
                }
            ]
        })

        if existing_schedule:
            return jsonify({
                'success': False,
                'error': f'Room {room_number} is already occupied on {day} at this time'
            }), 400

        # 2. Check if teacher is already teaching at this time
        teacher_schedule = scheduled_classes_collection.find_one({
            'teacher_registration': course.get('teacher_registration'),
            'day': day,
            '$or': [
                {
                    'start_time': {'$lte': start_time},
                    'end_time': {'$gt': start_time}
                },
                {
                    'start_time': {'$lt': end_time},
                    'end_time': {'$gte': end_time}
                },
                {
                    'start_time': {'$gte': start_time},
                    'end_time': {'$lte': end_time}
                }
            ]
        })

        if teacher_schedule:
            return jsonify({
                'success': False,
                'error': f'Teacher is already scheduled for another class on {day} at this time'
            }), 400

        # Get teacher name safely
        teacher = users_collection.find_one({'registration_number': course.get('teacher_registration')})
        teacher_name = teacher.get('username', 'Unknown') if teacher else 'Unknown'

        # Create scheduled class document
        scheduled_class = {
            'course_id': str(course_id),
            'course_name': course.get('course_name'),
            'section_code': section_code,
            'teacher_registration': course.get('teacher_registration'),
            'teacher_name': teacher_name,
            'course_type': course.get('course_type'),
            'credit_hour': course.get('credit_hour'),
            'shift': course.get('shift'),
            'day': day,
            'start_time': start_time,
            'end_time': end_time,
            'room_number': room_number,
            'floor': room.get('floor'),
            'created_at': datetime.now(),
            'created_by': session.get('username')
        }

        # Insert into database
        scheduled_classes_collection.insert_one(scheduled_class)

        return jsonify({
            'success': True,
            'message': 'Class scheduled successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Route for Teacher View
@app.route("/teacher")
@login_required
def teacher_view():
    # Get teacher's registration number from session
    teacher_reg = session.get('registration_number')

    return render_template(
        "timetables/timetable_base.html",
        active_page="teacher",
        page_title="Timetable",
        hide_top_bar=False,
        show_back_button=False,
        show_teacher_header=True,
        show_page_title=False,
        username=session.get('username'),
        teacher_filter=teacher_reg,
        room_filter=None,
        floor_filter=None
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

@app.route("/teacher/send_password_reset_otp", methods=["POST"])
def teacher_send_password_reset_otp():
    """Send OTP to teacher's email for password reset"""
    try:
        data = request.get_json()
        registration_number = data.get('registration_number', '').strip()

        if not registration_number:
            return jsonify({'success': False, 'error': 'Registration number is required'}), 400

        # Find teacher by registration number
        teacher = users_collection.find_one({'registration_number': registration_number})
        if not teacher:
            return jsonify({'success': False, 'error': 'No user found with this registration number'}), 404

        teacher_email = teacher.get('email')
        teacher_name = teacher.get('username')

        if not teacher_email:
            return jsonify({'success': False, 'error': 'No email address found for this user'}), 400

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP in session with timestamp
        session[f'password_reset_otp_{registration_number}'] = otp
        session[f'password_reset_otp_timestamp_{registration_number}'] = time.time()

        # Send OTP email
        send_otp_email(teacher_email, otp)

        return jsonify({
            'success': True,
            'message': f'OTP has been sent to {teacher_email}',
            'email': teacher_email
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/teacher/verify_password_reset_otp", methods=["POST"])
def teacher_verify_password_reset_otp():
    """Verify OTP for password reset"""
    try:
        data = request.get_json()
        registration_number = data.get('registration_number', '').strip()
        entered_otp = data.get('otp', '').strip()

        if not registration_number or not entered_otp:
            return jsonify({'success': False, 'error': 'Registration number and OTP are required'}), 400

        # Check if OTP exists in session
        otp_key = f'password_reset_otp_{registration_number}'
        timestamp_key = f'password_reset_otp_timestamp_{registration_number}'

        if otp_key not in session or timestamp_key not in session:
            return jsonify({'success': False, 'error': 'No OTP request found. Please request OTP first.'}), 400

        # Check if OTP is expired (10 minutes = 600 seconds)
        otp_age = time.time() - session[timestamp_key]
        if otp_age > 600:
            # Clear expired OTP
            session.pop(otp_key, None)
            session.pop(timestamp_key, None)
            return jsonify({'success': False, 'error': 'OTP has expired. Please request a new one.'}), 400

        # Verify OTP
        if entered_otp != session[otp_key]:
            return jsonify({'success': False, 'error': 'Invalid OTP. Please try again.'}), 400

        # OTP is valid, mark as verified
        session[f'password_reset_verified_{registration_number}'] = True

        return jsonify({
            'success': True,
            'message': 'OTP verified successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/teacher/reset_password", methods=["POST"])
def teacher_reset_password():
    """Reset teacher password after OTP verification"""
    try:
        data = request.get_json()
        registration_number = data.get('registration_number', '').strip()
        new_password = data.get('new_password', '').strip()

        if not registration_number or not new_password:
            return jsonify({'success': False, 'error': 'Registration number and new password are required'}), 400

        # Check if OTP was verified
        verified_key = f'password_reset_verified_{registration_number}'
        if not session.get(verified_key):
            return jsonify({'success': False, 'error': 'OTP verification required. Please verify OTP first.'}), 400

        # Find teacher
        teacher = users_collection.find_one({'registration_number': registration_number})
        if not teacher:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Update password in database
        users_collection.update_one(
            {'registration_number': registration_number},
            {'$set': {'password': new_password}}
        )

        # Clear all session data related to password reset
        session.pop(f'password_reset_otp_{registration_number}', None)
        session.pop(f'password_reset_otp_timestamp_{registration_number}', None)
        session.pop(verified_key, None)

        return jsonify({
            'success': True,
            'message': 'Password has been reset successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Route for Admin Panel
@app.route("/admin")
@login_required
def admin_panel():
    return render_template("pages/adminPanel.html", active_page="admin")

@app.route("/import_data")
@login_required
def import_data():
    """Import data page for importing courses and faculty via CSV"""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template("pages/import_data.html", active_page="admin")

@app.route("/import_csv", methods=["POST"])
@login_required
def import_csv_data():
    """Import courses or faculty from CSV file"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized. Admin access required.'}), 403

    try:
        # Get file and type from request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['file']
        import_type = request.form.get('type')

        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not import_type or import_type not in ['courses', 'faculty']:
            return jsonify({'success': False, 'error': 'Invalid import type'}), 400

        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)

        if import_type == 'courses':
            return import_courses_from_csv(csv_reader)
        elif import_type == 'faculty':
            return import_faculty_from_csv(csv_reader)

    except Exception as e:
        return jsonify({'success': False, 'error': f'Error processing file: {str(e)}'}), 500

def import_courses_from_csv(csv_reader):
    """Import courses from CSV data"""
    required_columns = ['course_name', 'credit_hour', 'course_type', 'shift', 'teacher_registration']

    try:
        rows = list(csv_reader)

        # Validate columns
        if not rows:
            return jsonify({'success': False, 'error': 'CSV file is empty'}), 400

        # Check required columns
        first_row_keys = list(rows[0].keys())
        missing_columns = [col for col in required_columns if col not in first_row_keys]
        if missing_columns:
            return jsonify({'success': False, 'error': f'Missing required columns: {", ".join(missing_columns)}'}), 400

        imported_count = 0
        errors = []

        for idx, row in enumerate(rows, start=2):  # Start at 2 because row 1 is header
            try:
                # Validate data
                course_name = row.get('course_name', '').strip()
                credit_hour = row.get('credit_hour', '').strip()
                course_type = row.get('course_type', '').strip()
                shift = row.get('shift', '').strip()
                teacher_registration = row.get('teacher_registration', '').strip()

                # Validations
                if not all([course_name, credit_hour, course_type, shift, teacher_registration]):
                    errors.append(f"Row {idx}: Missing required data")
                    continue

                if credit_hour not in ['1', '3']:
                    errors.append(f"Row {idx}: credit_hour must be '1' or '3'")
                    continue

                if course_type not in ['Lab', 'Lecture']:
                    errors.append(f"Row {idx}: course_type must be 'Lab' or 'Lecture'")
                    continue

                if shift not in ['Morning', 'Evening']:
                    errors.append(f"Row {idx}: shift must be 'Morning' or 'Evening'")
                    continue

                # Check if teacher exists
                teacher = users_collection.find_one({'registration_number': teacher_registration})
                if not teacher:
                    errors.append(f"Row {idx}: Teacher with registration {teacher_registration} not found")
                    continue

                # Auto-generate section code
                prefix = 'MOR' if shift == 'Morning' else 'EVE'
                existing_courses = list(courses_collection.find({"section_code": {"$regex": f"^{prefix}"}}))
                max_num = 0
                for course in existing_courses:
                    code = course.get('section_code', '')
                    if len(code) == 6:
                        try:
                            num = int(code[3:])
                            if num > max_num:
                                max_num = num
                        except ValueError:
                            pass
                new_num = max_num + 1
                section_code = f"{prefix}{new_num:03d}"

                # Create course data
                course_data = {
                    'course_name': course_name,
                    'credit_hour': credit_hour,
                    'course_type': course_type,
                    'shift': shift,
                    'section_code': section_code,
                    'teacher_registration': teacher_registration,
                    'teacher_name': teacher.get('username')
                }

                # Insert course
                courses_collection.insert_one(course_data)
                imported_count += 1

                # Send email to teacher (non-blocking)
                try:
                    teacher_email = teacher.get('email')
                    if teacher_email:
                        course_details = {
                            'course_name': course_name,
                            'section_code': section_code,
                            'course_type': course_type,
                            'credit_hour': credit_hour,
                            'shift': shift
                        }
                        send_course_assignment_email(teacher_email, teacher.get('username'), course_details)
                except Exception as e:
                    print(f"Warning: Failed to send email for course {course_name}: {str(e)}")

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        # Return result
        if imported_count > 0:
            message = f'Successfully imported {imported_count} course(s)'
            if errors:
                message += f'. {len(errors)} row(s) had errors: {"; ".join(errors[:5])}'
            return jsonify({'success': True, 'message': message, 'count': imported_count})
        else:
            return jsonify({'success': False, 'error': f'No courses imported. Errors: {"; ".join(errors[:5])}'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': f'Error importing courses: {str(e)}'}), 500

def import_faculty_from_csv(csv_reader):
    """Import faculty from CSV data"""
    required_columns = ['username', 'registration_number', 'email']

    try:
        rows = list(csv_reader)

        # Validate columns
        if not rows:
            return jsonify({'success': False, 'error': 'CSV file is empty'}), 400

        # Check required columns
        first_row_keys = list(rows[0].keys())
        missing_columns = [col for col in required_columns if col not in first_row_keys]
        if missing_columns:
            return jsonify({'success': False, 'error': f'Missing required columns: {", ".join(missing_columns)}'}), 400

        imported_count = 0
        errors = []

        for idx, row in enumerate(rows, start=2):  # Start at 2 because row 1 is header
            try:
                # Validate data
                username = row.get('username', '').strip()
                registration_number = row.get('registration_number', '').strip()
                email = row.get('email', '').strip()

                # Validations
                if not all([username, registration_number, email]):
                    errors.append(f"Row {idx}: Missing required data")
                    continue

                # Check for duplicates in database
                if users_collection.find_one({'registration_number': registration_number}):
                    errors.append(f"Row {idx}: Registration number {registration_number} already exists")
                    continue

                if users_collection.find_one({'email': email}):
                    errors.append(f"Row {idx}: Email {email} already exists")
                    continue

                # Auto-generate password
                password = generate_password(10)

                # Try to send email first
                try:
                    send_user_email(email, username, password)
                except Exception as e:
                    errors.append(f"Row {idx}: Failed to send email to {email}: {str(e)}")
                    continue

                # Create user data
                user_data = {
                    'username': username,
                    'registration_number': registration_number,
                    'email': email,
                    'password': password
                }

                # Insert user
                users_collection.insert_one(user_data)
                imported_count += 1

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        # Return result
        if imported_count > 0:
            message = f'Successfully imported {imported_count} faculty member(s)'
            if errors:
                message += f'. {len(errors)} row(s) had errors: {"; ".join(errors[:5])}'
            return jsonify({'success': True, 'message': message, 'count': imported_count})
        else:
            return jsonify({'success': False, 'error': f'No faculty imported. Errors: {"; ".join(errors[:5])}'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': f'Error importing faculty: {str(e)}'}), 500

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
    email = data.get('email')
    registration_number = data.get('registration_number')

    # Auto-generate password
    password = generate_password(10)

    # Validate required fields
    if not username:
        return {"success": False, "error": "Username is required"}, 400
    if not registration_number:
        return {"success": False, "error": "Registration number is required"}, 400
    if not email:
        return {"success": False, "error": "Email address is required"}, 400

    # Check if username already exists
    if users_collection.find_one({'username': username}):
        return {"success": False, "error": "Username already exists"}, 400

    # Check if registration number already exists
    if users_collection.find_one({'registration_number': registration_number}):
        return {"success": False, "error": "Registration number already exists. Each registration number can only be used once."}, 400

    # Check if email already exists
    if users_collection.find_one({'email': email}):
        return {"success": False, "error": "Email address already exists. Each email can only be used once."}, 400

    # Try to send email first
    try:
        send_user_email(email, username, password)
    except Exception as e:
        return {"success": False, "error": f"Failed to send email: {str(e)}"}, 500

    # Save user to database
    user_data = {
        'username': username,
        'registration_number': registration_number,
        'email': email,
        'password': password
    }

    # If email sent successfully, add user to MongoDB
    users_collection.insert_one(user_data)

    # Return success with generated password so admin can view it
    return {"success": True, "password": password, "username": username}

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
            {"name": "room_number", "label": "Room Number", "type": "text", "table_display": True, "form_display": True, "readonly": True},
            {"name": "type", "label": "Type", "type": "select", "options": ["Lab", "Lecture Hall"], "table_display": True, "form_display": True},
            {"name": "floor_number", "label": "Floor Number", "table_display": True, "form_display": False, "type": "text"},
            {"name": "availability", "label": "Room Availability", "type": "select", "options": ["Available", "Not Available"], "table_display": True, "form_display": True},
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
            {"name": "room_number", "label": "Room Number", "type": "text", "table_display": True, "form_display": True, "readonly": True},
            {"name": "type", "label": "Type", "type": "select", "options": ["Lab", "Lecture Hall"], "table_display": True, "form_display": True},
            {"name": "floor_number", "label": "Floor Number", "table_display": True, "form_display": False, "type": "text"},
            {"name": "availability", "label": "Room Availability", "type": "select", "options": ["Available", "Not Available"], "table_display": True, "form_display": True},
        ],
        from_dashboard=False,
        show_back_button=True,
        back_url="/manage_rooms",
        current_floor=floor_number
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
        # Ensure availability field exists with default value
        if 'availability' not in room_data or not room_data['availability']:
            room_data['availability'] = 'Available'
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

    # Get all existing rooms
    all_rooms = list(rooms_collection.find({}))

    # For each floor, find the highest room number and continue from there
    rooms_to_create = []

    for floor in floors:
        # Find all rooms on this floor
        floor_rooms = []
        for room in all_rooms:
            room_num_str = str(room.get('room_number', ''))
            if len(room_num_str) >= 3 and room_num_str[:-2] == str(floor):
                floor_rooms.append(room_num_str)

        # Find the highest room number on this floor
        max_room_on_floor = 0
        for room_num_str in floor_rooms:
            # Extract the last 2 digits (the room part)
            room_part = int(room_num_str[-2:])
            if room_part > max_room_on_floor:
                max_room_on_floor = room_part

        # Start creating rooms from (max + 1)
        start_room_num = max_room_on_floor + 1

        for i in range(rooms_per_floor):
            room_num = start_room_num + i
            room_number = f"{floor}{room_num:02d}"  # Format: 101, 102, etc.
            rooms_to_create.append({
                "room_number": room_number,
                "type": room_type,
                "floor": floor
            })

    # Create the rooms
    created_count = 0
    for room_data in rooms_to_create:
        rooms_collection.insert_one({
            "room_number": room_data["room_number"],
            "type": room_data["type"],
            "availability": "Available"  # Default availability
        })
        created_count += 1

    # Determine which floors were affected
    floors_affected = set(room_data["floor"] for room_data in rooms_to_create)

    return {
        "success": True,
        "message": f"Successfully created {created_count} room(s) on {len(floors_affected)} floor(s)"
    }

@app.route("/add_floor", methods=["POST"])
@login_required
def add_floor():
    """Add a new floor - rooms can be added separately later"""
    data = request.get_json()
    floor_number = data.get('floor_number', '').strip()

    # Validate input
    if not floor_number:
        return {"success": False, "error": "Floor number is required"}, 400

    try:
        floor_number = int(floor_number)
        if floor_number < 1:
            return {"success": False, "error": "Floor number must be at least 1"}, 400
    except ValueError:
        return {"success": False, "error": "Floor number must be a number"}, 400

    # Check if floor already exists in floors collection
    existing_floor = floors_collection.find_one({"floor_number": floor_number})
    if existing_floor:
        return {"success": False, "error": f"Floor {floor_number} already exists."}, 400

    # Check if floor already has rooms (check both string and integer formats)
    all_rooms = list(rooms_collection.find({}))
    for room in all_rooms:
        room_num_str = str(room.get('room_number', ''))
        if len(room_num_str) >= 3 and room_num_str[:-2] == str(floor_number):
            return {"success": False, "error": f"Floor {floor_number} already has rooms."}, 400

    # Add floor to floors collection
    floors_collection.insert_one({
        "floor_number": floor_number,
        "created_at": datetime.now()
    })

    return {
        "success": True,
        "message": f"Successfully added Floor {floor_number}. You can now add rooms to this floor."
    }

@app.route("/get_floors", methods=["GET"])
@login_required
def get_floors():
    """Get all floors with room counts - includes both floors from floors collection and floors with rooms"""
    all_rooms = list(rooms_collection.find({}))

    # Group rooms by floor
    floors = {}
    for room in all_rooms:
        room_number = room.get('room_number', '')

        # Convert to string if it's a number
        room_number_str = str(room_number)

        # Extract floor number - handle different formats
        if len(room_number_str) >= 3:
            # Format: 101, 102, 201, etc. -> floor is first digit(s), last 2 are room number
            floor = room_number_str[:-2]
        elif len(room_number_str) == 2:
            # Format: 01, 02, etc. -> floor is 0 or first digit
            floor = room_number_str[0] if room_number_str[0] != '0' else '0'
        elif len(room_number_str) == 1:
            # Single digit room, assume floor 0
            floor = '0'
        else:
            continue  # Skip invalid room numbers

        # Store floor
        if floor and floor.isdigit():
            if floor not in floors:
                floors[floor] = 0
            floors[floor] += 1

    # Add floors from floors_collection (floors without rooms yet)
    all_floors_db = list(floors_collection.find({}))
    for floor_doc in all_floors_db:
        floor_num = str(floor_doc.get('floor_number', ''))
        if floor_num not in floors:
            floors[floor_num] = 0

    # Convert to list format and sort
    floor_list = []
    for floor, count in floors.items():
        try:
            floor_list.append({"floor": int(floor), "count": count})
        except (ValueError, TypeError):
            # Skip floors that can't be converted to int
            print(f"Warning: Could not convert floor '{floor}' to integer")
            continue

    # Sort by floor number
    floor_list.sort(key=lambda x: x['floor'])

    return {"floors": floor_list}

@app.route("/get_rooms_by_floor/<int:floor_number>", methods=["GET"])
@login_required
def get_rooms_by_floor(floor_number):
    """Get all rooms on a specific floor"""
    # Get all rooms and filter by floor (handles both string and integer room_number)
    all_rooms = list(rooms_collection.find({}))

    rooms_with_floor = []
    for room in all_rooms:
        room_number_str = str(room.get("room_number", ""))

        # Extract floor from room number
        if len(room_number_str) >= 3:
            room_floor = room_number_str[:-2]
        else:
            continue  # Skip invalid room numbers

        # Only include rooms from the requested floor
        if room_floor == str(floor_number):
            room_data = room.copy()
            room_data['_id'] = str(room_data['_id'])
            room_data["floor_number"] = _extract_floor_from_room_number(room_number_str)
            # Ensure availability field exists with default value
            if 'availability' not in room_data or not room_data['availability']:
                room_data['availability'] = 'Available'
            rooms_with_floor.append(room_data)

    # Sort by room number
    rooms_with_floor.sort(key=lambda x: int(x.get('room_number', 0)))

    return jsonify({
        "success": True,
        "rooms": rooms_with_floor
    })

@app.route("/delete_floor/<int:floor_number>", methods=["DELETE"])
@login_required
def delete_floor(floor_number):
    """Delete an entire floor and all its rooms"""
    try:
        # Get all rooms and find rooms on this floor
        all_rooms = list(rooms_collection.find({}))
        rooms_to_delete = []

        for room in all_rooms:
            room_number_str = str(room.get("room_number", ""))
            if len(room_number_str) >= 3:
                room_floor = room_number_str[:-2]
                if room_floor == str(floor_number):
                    rooms_to_delete.append(room['_id'])

        # Delete the identified rooms
        rooms_deleted_count = 0
        if rooms_to_delete:
            rooms_result = rooms_collection.delete_many({"_id": {"$in": rooms_to_delete}})
            rooms_deleted_count = rooms_result.deleted_count

        # Delete floor from floors collection
        floor_result = floors_collection.delete_one({
            "floor_number": floor_number
        })

        total_deleted = rooms_deleted_count + floor_result.deleted_count

        if total_deleted > 0:
            if rooms_deleted_count > 0:
                return {
                    "success": True,
                    "message": f"Deleted floor {floor_number} ({rooms_deleted_count} rooms)"
                }
            else:
                return {
                    "success": True,
                    "message": f"Deleted floor {floor_number} (no rooms)"
                }
        else:
            return {
                "success": False,
                "error": f"Floor {floor_number} not found"
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
            {"name": "course_type", "label": "Course Type", "type": "select", "options": ["Lab", "Lecture"], "table_display": True, "form_display": True},
            {"name": "shift", "label": "Shift Time", "type": "select", "options": ["Morning", "Evening"], "table_display": True, "form_display": True},
            {"name": "section_code", "label": "Section Code", "type": "text", "table_display": True, "form_display": False},
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

    # Auto-generate section code from shift
    shift = data.get('shift', 'Morning')
    prefix = 'MOR' if shift == 'Morning' else 'EVE'

    # Find existing courses with this prefix to determine next number
    existing_courses = list(courses_collection.find({"section_code": {"$regex": f"^{prefix}"}}))

    # Find the highest number used
    max_num = 0
    for course in existing_courses:
        code = course.get('section_code', '')
        if len(code) == 6:  # MOR/EVE + 3 digits
            try:
                num = int(code[3:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass

    # Generate new section code
    new_num = max_num + 1
    section_code = f"{prefix}{new_num:03d}"

    # Store as array for consistency with multiple sections feature
    data['section_codes'] = [section_code]
    # Keep section_code for backward compatibility
    data['section_code'] = section_code

    # Double-check for duplicate (safety check)
    if courses_collection.find_one({"section_code": section_code}):
        return {"success": False, "error": "Section code already exists. Please try again."}, 400

    # Look up teacher by registration number to get email
    teacher_registration = data.get('teacher_registration')
    teacher = users_collection.find_one({'registration_number': teacher_registration})

    if not teacher:
        return {"success": False, "error": "Teacher not found with this registration number"}, 404

    teacher_email = teacher.get('email')
    teacher_name = teacher.get('username')

    # Insert course into database
    courses_collection.insert_one(data)

    # Send email notification to teacher (non-blocking - don't fail if email fails)
    try:
        if teacher_email:
            course_details = {
                'course_name': data.get('course_name'),
                'section_code': section_code,
                'course_type': data.get('course_type'),
                'credit_hour': data.get('credit_hour'),
                'shift': shift
            }
            send_course_assignment_email(teacher_email, teacher_name, course_details)
            print(f"Course assignment email sent to {teacher_email}")
    except Exception as e:
        # Log the error but don't fail the course creation
        print(f"Warning: Failed to send course assignment email: {str(e)}")

    return {"success": True, "section_code": section_code}

@app.route("/view_timetable")
@login_required
def view_timetable():
    """View timetable with optional room/teacher/floor filters"""
    room_number = request.args.get('room')
    teacher_reg = request.args.get('teacher')
    floor_number = request.args.get('floor')

    # If no filters provided, show filter selection page
    if not room_number and not teacher_reg and not floor_number:
        return render_template("pages/selectFloor.html", active_page="view_timetable")

    # Build title based on filters
    title_parts = []
    if room_number:
        title_parts.append(f"Room {room_number}")
    if teacher_reg:
        teacher = users_collection.find_one({'registration_number': teacher_reg})
        if teacher:
            title_parts.append(f"Teacher: {teacher.get('username')}")
    if floor_number:
        title_parts.append(f"Floor {floor_number}")

    page_title = f"Timetable - {' & '.join(title_parts)}" if title_parts else "Timetable"

    return render_template(
        "timetables/timetable_base.html",
        active_page="view_timetable",
        page_title="View Timetable",
        hide_top_bar=True,
        show_back_button=True,
        show_teacher_header=False,
        show_page_title=True,
        page_title_text=page_title,
        room_filter=room_number,
        teacher_filter=teacher_reg,
        floor_filter=floor_number
    )

@app.route("/get_all_rooms", methods=["GET"])
@login_required
def get_all_rooms():
    """Get all rooms for filter dropdown"""
    try:
        rooms_list = list(rooms_collection.find({}))
        rooms_data = []

        for room in rooms_list:
            rooms_data.append({
                'room_number': str(room.get('room_number', '')),
                'type': room.get('type', ''),
                'floor': room.get('floor', '')
            })

        # Sort by room number
        rooms_data.sort(key=lambda x: x['room_number'])

        return jsonify({
            'success': True,
            'rooms': rooms_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/get_all_teachers", methods=["GET"])
@login_required
def get_all_teachers():
    """Get all teachers for filter dropdown"""
    try:
        teachers_list = list(users_collection.find({}))
        teachers_data = []

        for teacher in teachers_list:
            teachers_data.append({
                'username': teacher.get('username', ''),
                'registration_number': teacher.get('registration_number', ''),
                'email': teacher.get('email', '')
            })

        # Sort by username
        teachers_data.sort(key=lambda x: x['username'])

        return jsonify({
            'success': True,
            'teachers': teachers_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/get_scheduled_classes", methods=["GET"])
@login_required
def get_scheduled_classes():
    """Get scheduled classes filtered by room, teacher, or floor"""
    try:
        room_number = request.args.get('room')
        teacher_reg = request.args.get('teacher')
        floor_number = request.args.get('floor')

        # Build query based on filters
        query = {}
        if room_number:
            query['room_number'] = room_number
        if teacher_reg:
            query['teacher_registration'] = teacher_reg
        if floor_number:
            query['floor'] = int(floor_number)

        # Get scheduled classes
        scheduled_classes = list(scheduled_classes_collection.find(query))

        # Format the data
        classes_data = []
        for cls in scheduled_classes:
            classes_data.append({
                '_id': str(cls.get('_id')),
                'course_name': cls.get('course_name'),
                'section_code': cls.get('section_code'),
                'teacher_name': cls.get('teacher_name'),
                'teacher_registration': cls.get('teacher_registration'),
                'course_type': cls.get('course_type'),
                'credit_hour': cls.get('credit_hour'),
                'shift': cls.get('shift'),
                'day': cls.get('day'),
                'start_time': cls.get('start_time'),
                'end_time': cls.get('end_time'),
                'room_number': cls.get('room_number'),
                'floor': cls.get('floor')
            })

        return jsonify({
            'success': True,
            'classes': classes_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route("/get_user_password/<int:user_id>", methods=["GET"])
@login_required
def get_user_password(user_id):
    """Admin endpoint to view a user's password"""
    # Only allow admin to view passwords
    if session.get('role') != 'admin':
        return jsonify({"error": "Unauthorized. Admin access required."}), 403

    users_list = list(users_collection.find({}))
    if 0 <= user_id < len(users_list):
        user = users_list[user_id]
        return jsonify({
            "success": True,
            "username": user.get('username'),
            "password": user.get('password'),
            "email": user.get('email'),
            "registration_number": user.get('registration_number')
        })
    return jsonify({"error": "User not found"}), 404

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

            # If updating a user, validate but keep existing password
            if item_type == "user":
                username = data.get('username')
                email = data.get('email')
                registration_number = data.get('registration_number')

                # Validate required fields
                if not username:
                    return {"success": False, "error": "Username is required"}, 400
                if not registration_number:
                    return {"success": False, "error": "Registration number is required"}, 400
                if not email:
                    return {"success": False, "error": "Email address is required"}, 400

                # Check if registration number is being changed to one that already exists
                existing_user_with_reg = users_collection.find_one({'registration_number': registration_number})
                if existing_user_with_reg and existing_user_with_reg['_id'] != item_to_update['_id']:
                    return {"success": False, "error": "Registration number already exists. Each registration number can only be used once."}, 400

                # Check if email is being changed to one that already exists
                existing_user_with_email = users_collection.find_one({'email': email})
                if existing_user_with_email and existing_user_with_email['_id'] != item_to_update['_id']:
                    return {"success": False, "error": "Email address already exists. Each email can only be used once."}, 400

                # Keep existing password (admin cannot manually change it)
                existing_password = item_to_update.get('password', '')

                # Update user data (password remains unchanged)
                update_data = {
                    'username': username,
                    'registration_number': registration_number,
                    'email': email,
                    'password': existing_password
                }
            elif item_type == "room":
                # Explicitly handle room updates to ensure all fields are updated
                update_data = {
                    'room_number': data.get('room_number'),
                    'type': data.get('type'),
                    'availability': data.get('availability', 'Available')
                }
                print(f"Updating room with data: {update_data}")  # Debug logging
            elif item_type == "course":
                # Ensure section_codes array exists for courses
                update_data = data

                # If section_code exists but not section_codes, create section_codes array
                if 'section_code' in update_data and 'section_codes' not in update_data:
                    update_data['section_codes'] = [update_data['section_code']]

                # If neither exists, generate section code
                if 'section_code' not in update_data:
                    shift = update_data.get('shift', 'Morning')
                    prefix = 'MOR' if shift == 'Morning' else 'EVE'

                    # Find existing courses with this prefix
                    existing_courses = list(courses_collection.find({"section_code": {"$regex": f"^{prefix}"}}))
                    max_num = 0
                    for course in existing_courses:
                        code = course.get('section_code', '')
                        if len(code) == 6:
                            try:
                                num = int(code[3:])
                                if num > max_num:
                                    max_num = num
                            except ValueError:
                                pass

                    new_num = max_num + 1
                    section_code = f"{prefix}{new_num:03d}"
                    update_data['section_code'] = section_code
                    update_data['section_codes'] = [section_code]
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

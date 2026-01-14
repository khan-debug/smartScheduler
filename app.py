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
# Use environment variable for secret key, fallback to random for development
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# MongoDB Connection - Use environment variables
MONGO_URI = os.environ.get('MONGODB_URI', "mongodb+srv://aarij:aarij0990@smartscheduler.tqtyuhp.mongodb.net/?retryWrites=true&w=majority&appName=smartscheduler")
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'smartscheduler_db')

# Try to connect to MongoDB
try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000
    )
    # Test connection
    client.admin.command('ping')
    db = client[MONGODB_DATABASE]

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
        email_config_path = os.environ.get('EMAIL_CONFIG_PATH', 'config/email_settings.txt')
        with open(email_config_path, 'r') as f:
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

# Timetable scheduling constants
SCHEDULE_START_TIME = '8:30 AM'
SCHEDULE_END_TIME = '10:00 PM'
HOURS_PER_DAY = 13.5  # 8:30 AM to 10:00 PM
DAYS_PER_WEEK = 6  # Monday to Saturday
LECTURE_DURATION_HOURS = 3
LAB_DURATION_HOURS = 1

# Helper functions for floor management
def extract_floor_number_from_room(room_number):
    """Extract floor number from room number (legacy support)"""
    room_number_str = str(room_number)
    if len(room_number_str) >= 3:
        return room_number_str[:-2]
    elif len(room_number_str) == 2:
        return room_number_str[0] if room_number_str[0] != '0' else '0'
    elif len(room_number_str) == 1:
        return '0'
    return None

def calculate_floor_capacity(lecture_halls, labs):
    """Calculate weekly class capacity for a floor based on room counts"""
    lectures_per_day = int(HOURS_PER_DAY / LECTURE_DURATION_HOURS)
    labs_per_day = int(HOURS_PER_DAY / LAB_DURATION_HOURS)

    lecture_capacity = lecture_halls * lectures_per_day * DAYS_PER_WEEK
    lab_capacity = labs * labs_per_day * DAYS_PER_WEEK

    return {
        'lecture_capacity': lecture_capacity,
        'lab_capacity': lab_capacity,
        'total_capacity': lecture_capacity + lab_capacity
    }

# Time slot configurations for scheduling
TIME_SLOTS = {
    'lecture': {
        'morning': [
            ('8:30 AM', '11:20 AM'),
            ('11:30 AM', '2:20 PM'),
            ('2:30 PM', '5:20 PM')
        ],
        'evening': [
            ('5:00 PM', '7:50 PM')
        ]
    },
    'lab': {
        'morning': [
            ('8:30 AM', '9:20 AM'), ('9:30 AM', '10:20 AM'), ('10:30 AM', '11:20 AM'),
            ('11:30 AM', '12:20 PM'), ('12:30 PM', '1:20 PM'), ('1:30 PM', '2:20 PM'),
            ('2:30 PM', '3:20 PM'), ('3:30 PM', '4:20 PM')
        ],
        'evening': [
            ('5:00 PM', '5:50 PM'), ('6:00 PM', '6:50 PM'), ('7:00 PM', '7:50 PM'),
            ('8:00 PM', '8:50 PM'), ('9:00 PM', '9:50 PM')
        ]
    }
}

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

def get_time_slots_for_course(course):
    """Get appropriate time slots for a course based on type and shift"""
    course_type = course.get('course_type', 'Lecture')
    shift_field = course.get('shift', '')
    section_code = course.get('section_code', '')

    slot_type = 'lab' if course_type == 'Lab' else 'lecture'

    # Determine shift from shift field or section_code
    is_morning = shift_field == 'Morning' or section_code.startswith('MOR')
    shift = 'morning' if is_morning else 'evening'

    return TIME_SLOTS[slot_type][shift]

# Genetic Algorithm for Timetable Scheduling
import random
import copy

class TimetableScheduler:
    def __init__(self, courses, rooms, floor_number):
        self.courses = courses
        self.rooms = rooms  # List of room dictionaries with room_number and type
        self.floor_number = floor_number
        self.population_size = 200
        self.generations = 1000
        self.mutation_rate = 0.15
        self.crossover_rate = 0.85
        self.elite_size = int(0.1 * self.population_size)
        self.existing_schedules = []  # Will be set externally if needed

    def create_chromosome(self):
        """Create a random schedule (chromosome)"""
        schedule = []
        for course in self.courses:
            # Get credit hours and course type
            credit_hour = course.get('credit_hour', '3')
            course_type = course.get('course_type', 'Lecture')

            # ENFORCE RULE: 3ch must be in Lecture Hall, 1ch must be in Lab
            if credit_hour == '3' or credit_hour == 3:
                valid_rooms = [r for r in self.rooms if r.get('type') == 'Lecture Hall']
            elif credit_hour == '1' or credit_hour == 1:
                valid_rooms = [r for r in self.rooms if r.get('type') == 'Lab']
            else:
                # Fallback to old logic for any other credit hours
                valid_rooms = [r for r in self.rooms if r.get('type') == ('Lab' if course_type == 'Lab' else 'Lecture Hall')]

            if not valid_rooms:
                continue

            # Get valid time slots for this course
            time_slots = get_time_slots_for_course(course)

            # Randomly assign day, time slot, and room
            gene = {
                'course_id': str(course['_id']),
                'course_code': course.get('section_code', ''),  # Use section_code as course identifier
                'course_name': course.get('course_name', ''),
                'teacher_name': course.get('teacher_name', ''),
                'shift': course.get('shift', ''),
                'section_code': course.get('section_code', ''),
                'day': random.choice(DAYS_OF_WEEK),
                'time_slot': random.choice(time_slots),
                'room': random.choice(valid_rooms)
            }
            schedule.append(gene)

        return schedule

    def calculate_fitness(self, chromosome):
        """Calculate fitness score for a schedule"""
        score = 1000  # Start with base score

        # Track conflicts
        teacher_schedule = {}  # {(teacher, day, time): count}
        room_schedule = {}  # {(room, day, time): count}
        day_counts = {day: 0 for day in DAYS_OF_WEEK}

        # Pre-populate with existing schedules to avoid conflicts
        if self.existing_schedules:
            for existing in self.existing_schedules:
                teacher = existing.get('teacher_name')
                day = existing.get('day')
                start_time = existing.get('start_time')
                end_time = existing.get('end_time')
                room = existing.get('room_number')

                # Mark these slots as occupied
                time_slot = (start_time, end_time)
                teacher_key = (teacher, day, time_slot)
                room_key = (room, day, time_slot)

                teacher_schedule[teacher_key] = 1
                room_schedule[room_key] = 1

        for gene in chromosome:
            teacher = gene['teacher_name']
            day = gene['day']
            time_slot = gene['time_slot']
            room = gene['room']['room_number']
            room_type = gene['room'].get('type', '')
            shift = gene.get('shift', '')
            section_code = gene.get('section_code', '')
            course_id = gene.get('course_id', '')

            # Count classes per day
            day_counts[day] += 1

            # Check credit hour and room type matching (HARD CONSTRAINT)
            # Find the course to get credit hours
            course = next((c for c in self.courses if str(c['_id']) == course_id and c.get('section_code') == section_code), None)
            if course:
                credit_hour = course.get('credit_hour', '3')
                # ENFORCE RULE: 3ch must be in Lecture Hall, 1ch must be in Lab
                if (credit_hour == '3' or credit_hour == 3) and room_type != 'Lecture Hall':
                    score -= 1000  # Severe penalty for wrong room type
                elif (credit_hour == '1' or credit_hour == 1) and room_type != 'Lab':
                    score -= 1000  # Severe penalty for wrong room type

            # Check teacher conflicts (HARD CONSTRAINT)
            teacher_key = (teacher, day, time_slot)
            teacher_schedule[teacher_key] = teacher_schedule.get(teacher_key, 0) + 1
            if teacher_schedule[teacher_key] > 1:
                score -= 1000  # Severe penalty

            # Check room conflicts (HARD CONSTRAINT)
            room_key = (room, day, time_slot)
            room_schedule[room_key] = room_schedule.get(room_key, 0) + 1
            if room_schedule[room_key] > 1:
                score -= 1000  # Severe penalty

            # Check shift consistency (HARD CONSTRAINT)
            start_time = time_slot[0]
            is_morning_slot = 'AM' in start_time and not start_time.startswith('5:')
            is_morning_course = shift == 'Morning' or section_code.startswith('MOR')

            if (is_morning_slot and not is_morning_course) or (not is_morning_slot and is_morning_course):
                score -= 800  # Wrong shift

        # Penalize using more rooms to encourage concentration (SOFT CONSTRAINT)
        # The goal is to use as few rooms as possible. A penalty is applied for each room used beyond the first one.
        unique_rooms_used = len(set(g['room']['room_number'] for g in chromosome))
        room_utilization_penalty = (unique_rooms_used - 1) * 50 if unique_rooms_used > 0 else 0
        score -= room_utilization_penalty

        # Reward balanced day distribution
        avg_per_day = len(chromosome) / len(DAYS_OF_WEEK)
        balance_penalty = sum(abs(count - avg_per_day) for count in day_counts.values())
        score -= balance_penalty * 10

        # Bonus for scheduling all courses
        if len(chromosome) == len(self.courses):
            score += 500

        return max(score, 0)  # Ensure non-negative

    def crossover(self, parent1, parent2):
        """Combine two schedules to create offspring"""
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1)

        # Handle edge cases where parents are too small
        min_len = min(len(parent1), len(parent2))
        if min_len <= 1:
            # If parents are too small, just return a copy of parent1
            return copy.deepcopy(parent1)

        # Single-point crossover
        point = random.randint(1, min_len - 1)
        child = parent1[:point] + parent2[point:]

        # Remove duplicate courses by checking both course_id and section_code
        seen = set()
        unique_child = []
        for gene in child:
            class_identifier = (gene['course_id'], gene['section_code'])
            if class_identifier not in seen:
                seen.add(class_identifier)
                unique_child.append(gene)

        return unique_child

    def mutate(self, chromosome):
        """Randomly modify a schedule"""
        if random.random() > self.mutation_rate:
            return chromosome

        mutated = copy.deepcopy(chromosome)

        if not mutated:
            return mutated

        # Pick random gene to mutate
        gene = random.choice(mutated)

        # Randomly mutate day, time, or room
        mutation_type = random.choice(['day', 'time', 'room'])

        if mutation_type == 'day':
            gene['day'] = random.choice(DAYS_OF_WEEK)
        elif mutation_type == 'time':
            course = next((c for c in self.courses if str(c['_id']) == gene['course_id'] and c['section_code'] == gene['section_code']), None)
            if course:
                time_slots = get_time_slots_for_course(course)
                gene['time_slot'] = random.choice(time_slots)
        elif mutation_type == 'room':
            course = next((c for c in self.courses if str(c['_id']) == gene['course_id'] and c['section_code'] == gene['section_code']), None)
            if course:
                credit_hour = course.get('credit_hour', '3')
                course_type = course.get('course_type', 'Lecture')

                # ENFORCE RULE: 3ch must be in Lecture Hall, 1ch must be in Lab
                if credit_hour == '3' or credit_hour == 3:
                    valid_rooms = [r for r in self.rooms if r.get('type') == 'Lecture Hall']
                elif credit_hour == '1' or credit_hour == 1:
                    valid_rooms = [r for r in self.rooms if r.get('type') == 'Lab']
                else:
                    # Fallback to old logic
                    valid_rooms = [r for r in self.rooms if r.get('type') == ('Lab' if course_type == 'Lab' else 'Lecture Hall')]

                if valid_rooms:
                    gene['room'] = random.choice(valid_rooms)

        return mutated

    def evolve(self):
        """Run the genetic algorithm"""
        # Initialize population
        population = [self.create_chromosome() for _ in range(self.population_size)]

        best_fitness = 0
        best_schedule = None

        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = [(chromo, self.calculate_fitness(chromo)) for chromo in population]
            fitness_scores.sort(key=lambda x: x[1], reverse=True)

            # Track best
            if fitness_scores[0][1] > best_fitness:
                best_fitness = fitness_scores[0][1]
                best_schedule = copy.deepcopy(fitness_scores[0][0])
                print(f"Generation {generation}: Best fitness = {best_fitness}")

            # Check for perfect solution
            if best_fitness >= 1000 + 500:  # Base score + all courses scheduled
                print(f"Perfect solution found at generation {generation}!")
                break

            # Selection: Keep elite
            new_population = [chromo for chromo, _ in fitness_scores[:self.elite_size]]

            # Crossover and mutation
            while len(new_population) < self.population_size:
                # Tournament selection
                parent1 = random.choice(fitness_scores[:50])[0]
                parent2 = random.choice(fitness_scores[:50])[0]

                child = self.crossover(parent1, parent2)
                child = self.mutate(child)

                new_population.append(child)

            population = new_population

        return best_schedule, best_fitness

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

        return render_template("auth/login_v2.html", error="Invalid credentials")
    return render_template("auth/login_v2.html")

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
    return render_template("pages/dashboard_v2.html", active_page="dashboard", teacher_count=teacher_count, course_count=course_count, room_count=room_count)

# Route for Generate Timetable
@app.route("/generate")
@login_required
def generate():
    return redirect(url_for('autogenerate_select_floor'))

@app.route("/generate_select_floor")
@login_required
def generate_select_floor():
    """Show floor selection page for timetable generation"""
    floors = get_floors_with_capacity_details()
    return render_template("pages/select_floor_for_generation.html", active_page="generate", floors=floors)

def get_floors_with_capacity_details():
    """Helper function to get all floors with their capacity details"""
    all_rooms = list(rooms_collection.find({}))
    all_scheduled_classes = list(scheduled_classes_collection.find({}))

    floors = {}

    # Initialize floors from rooms
    for room in all_rooms:
        floor_num = extract_floor_number_from_room(room.get('room_number', ''))

        if floor_num and floor_num.isdigit():
            if floor_num not in floors:
                floors[floor_num] = {'total_rooms': 0, 'lecture_halls': 0, 'labs': 0, 'scheduled_classes': 0}
            floors[floor_num]['total_rooms'] += 1
            if room.get('type') == 'Lecture Hall':
                floors[floor_num]['lecture_halls'] += 1
            elif room.get('type') == 'Lab':
                floors[floor_num]['labs'] += 1

    # Add floors from the floors collection that might not have rooms yet
    all_floors_db = list(floors_collection.find({}))
    for floor_doc in all_floors_db:
        floor_num = str(floor_doc.get('floor_number', ''))
        if floor_num and floor_num not in floors:
            floors[floor_num] = {'total_rooms': 0, 'lecture_halls': 0, 'labs': 0, 'scheduled_classes': 0}

    # Count scheduled classes for each floor
    for s_class in all_scheduled_classes:
        floor_num = str(s_class.get('floor', ''))
        if floor_num and floor_num in floors:
            floors[floor_num]['scheduled_classes'] += 1

    # Calculate capacity and format the output
    floor_list = []
    for floor_num, data in floors.items():
        try:
            capacity = calculate_floor_capacity(data['lecture_halls'], data['labs'])
            schedulable_classes = capacity['total_capacity'] - data['scheduled_classes']

            floor_list.append({
                "floor": int(floor_num),
                "total_rooms": data['total_rooms'],
                "schedulable_classes": schedulable_classes
            })
        except (ValueError, TypeError):
            print(f"Warning: Could not process floor '{floor_num}'")
            continue

    floor_list.sort(key=lambda x: x['floor'])
    return floor_list

@app.route("/autogenerate_select_floor")
@login_required
def autogenerate_select_floor():
    """Show floor selection page with capacity calculation"""
    return render_template("pages/autogenerate_select_floor.html", active_page="generate")

@app.route("/autogenerate_configure")
@login_required
def autogenerate_configure():
    """Show course selection options for a specific floor"""
    floor_number = request.args.get('floor', type=int)
    if not floor_number:
        return redirect(url_for('autogenerate_select_floor'))

    # Get all rooms and filter by floor number (extracted from room_number)
    all_rooms = list(rooms_collection.find({}))
    floor_rooms = []

    for room in all_rooms:
        room_floor = extract_floor_number_from_room(room.get('room_number', ''))
        if room_floor and room_floor.isdigit() and int(room_floor) == floor_number:
            floor_rooms.append(room)

    # Count rooms by type
    lecture_halls = sum(1 for room in floor_rooms if room.get('type') == 'Lecture Hall')
    labs = sum(1 for room in floor_rooms if room.get('type') == 'Lab')

    capacity_info = calculate_floor_capacity(lecture_halls, labs)
    capacity_info['lecture_halls'] = lecture_halls
    capacity_info['labs'] = labs

    return render_template(
        "pages/autogenerate_course_selection.html",
        active_page="generate",
        floor_number=floor_number,
        capacity=capacity_info
    )

@app.route("/autogenerate_autopick")
@login_required
def autogenerate_autopick():
    """Automatically pick unscheduled courses based on floor capacity"""
    floor_number = request.args.get('floor', type=int)
    if not floor_number:
        return redirect(url_for('autogenerate_select_floor'))

    # Get all rooms and filter by floor number (extracted from room_number)
    all_rooms = list(rooms_collection.find({}))
    floor_rooms = []

    for room in all_rooms:
        room_floor = extract_floor_number_from_room(room.get('room_number', ''))
        if room_floor and room_floor.isdigit() and int(room_floor) == floor_number:
            floor_rooms.append(room)

    # Count rooms by type
    lecture_halls = sum(1 for room in floor_rooms if room.get('type') == 'Lecture Hall')
    labs = sum(1 for room in floor_rooms if room.get('type') == 'Lab')

    # Get ALL already scheduled sections from all floors
    all_scheduled_classes = list(scheduled_classes_collection.find({}))
    scheduled_sections_set = set()
    for sc in all_scheduled_classes:
        course_id = sc.get('course_id')
        section_code = sc.get('section_code')
        if course_id and section_code:
            scheduled_sections_set.add((str(course_id), section_code))

    print(f"\n{'='*60}")
    print(f"AUTOPICK FOR FLOOR {floor_number}")
    print(f"{'='*60}")
    print(f"Total scheduled sections across all floors: {len(scheduled_sections_set)}")

    # Prepare a list of all schedulable units (course sections that are not yet scheduled)
    all_schedulable_units = []
    total_sections_in_db = 0
    for course in list(courses_collection.find({})): # Get all courses from DB
        course_id_str = str(course['_id'])

        # Handle both old (section_code) and new (section_codes) format
        sections_in_course = course.get('section_codes', [])
        if not sections_in_course and course.get('section_code'):
            sections_in_course = [course.get('section_code')]

        total_sections_in_db += len(sections_in_course)

        for section_code in sections_in_course:
            if (course_id_str, section_code) not in scheduled_sections_set:
                # This section is unscheduled, create a unique schedulable unit for it
                schedulable_unit = course.copy()
                schedulable_unit['section_code'] = section_code # Ensure this unit represents this specific section
                all_schedulable_units.append(schedulable_unit)

    print(f"Total course sections in database: {total_sections_in_db}")
    print(f"Available unscheduled sections: {len(all_schedulable_units)}")
    print(f"{'='*60}\n")

    # Separate unscheduled schedulable units by credit hour (which determines room type) and shift
    unscheduled_lectures_morning = []  # 3ch courses for Lecture Halls
    unscheduled_lectures_evening = []  # 3ch courses for Lecture Halls
    unscheduled_labs_morning = []      # 1ch courses for Labs
    unscheduled_labs_evening = []      # 1ch courses for Labs

    for unit in all_schedulable_units:
        credit_hour = unit.get('credit_hour', '3')
        shift = unit.get('shift', '')
        section_code_for_unit = unit.get('section_code', '')

        is_morning = shift == 'Morning' or section_code_for_unit.startswith('MOR')
        is_evening = shift == 'Evening' or section_code_for_unit.startswith('EVE')

        # ENFORCE RULE: 3ch must be in Lecture Hall, 1ch must be in Lab
        # Categorize based on credit hours (which determines room type requirement)
        # Convert to string for consistent comparison
        credit_hour_str = str(credit_hour)

        if credit_hour_str == '1':
            # 1ch courses need Labs
            if is_morning:
                unscheduled_labs_morning.append(unit)
            elif is_evening:
                unscheduled_labs_evening.append(unit)
        elif credit_hour_str == '3':
            # 3ch courses need Lecture Halls
            if is_morning:
                unscheduled_lectures_morning.append(unit)
            elif is_evening:
                unscheduled_lectures_evening.append(unit)
        else:
            # Unknown credit hour - log warning and skip
            print(f"WARNING: Course '{unit.get('course_name')}' has unexpected credit_hour: {credit_hour} (type: {type(credit_hour).__name__})")

    # Log categorization results
    print(f"Categorization by credit hours:")
    print(f"  3ch Lectures (Morning): {len(unscheduled_lectures_morning)}")
    print(f"  3ch Lectures (Evening): {len(unscheduled_lectures_evening)}")
    print(f"  1ch Labs (Morning): {len(unscheduled_labs_morning)}")
    print(f"  1ch Labs (Evening): {len(unscheduled_labs_evening)}")
    print()

    # Calculate shift-specific capacity
    morning_lecture_capacity = lecture_halls * 3 * DAYS_PER_WEEK
    evening_lecture_capacity = lecture_halls * 1 * DAYS_PER_WEEK
    morning_lab_capacity = labs * 8 * DAYS_PER_WEEK
    evening_lab_capacity = labs * 5 * DAYS_PER_WEEK

    # Randomly shuffle the lists to ensure fairness in selection up to capacity
    random.shuffle(unscheduled_lectures_morning)
    random.shuffle(unscheduled_lectures_evening)
    random.shuffle(unscheduled_labs_morning)
    random.shuffle(unscheduled_labs_evening)

    # Pick units based on shift-specific capacity
    selected_lectures_morning = unscheduled_lectures_morning[:morning_lecture_capacity]
    selected_lectures_evening = unscheduled_lectures_evening[:evening_lecture_capacity]
    selected_labs_morning = unscheduled_labs_morning[:morning_lab_capacity]
    selected_labs_evening = unscheduled_labs_evening[:evening_lab_capacity]

    selected_schedulable_units = (selected_lectures_morning + selected_lectures_evening +
                                  selected_labs_morning + selected_labs_evening)

    # Store selected sections (course_id, section_code) in session for the next step
    session['autopicked_sections'] = [(str(unit['_id']), unit['section_code']) for unit in selected_schedulable_units]
    session['autogenerate_floor'] = floor_number

    # Redirect to confirmation/scheduling page
    return redirect(url_for('autogenerate_confirm_autopick', floor=floor_number))

@app.route("/autogenerate_confirm_autopick")
@login_required
def autogenerate_confirm_autopick():
    """Show confirmation page for autopicked course sections"""
    floor_number = request.args.get('floor', type=int)
    if not floor_number or 'autopicked_sections' not in session: # Check new session key
        return redirect(url_for('autogenerate_select_floor'))

    # Get selected sections (course_id, section_code) from session
    selected_sections_from_session = session.get('autopicked_sections', [])
    
    # Reconstruct full course objects for each selected section for display
    displayed_courses = []
    if selected_sections_from_session:
        course_ids_to_fetch = list(set([cid for cid, _ in selected_sections_from_session]))
        
        # Fetch actual course documents from DB once
        db_courses_map = {str(c['_id']): c for c in courses_collection.find({'_id': {'$in': [ObjectId(cid) for cid in course_ids_to_fetch]}})}

        for course_id_str, section_code_to_display in selected_sections_from_session:
            original_course = db_courses_map.get(course_id_str)
            if original_course:
                display_unit = original_course.copy()
                display_unit['section_code'] = section_code_to_display # Ensure this unit represents this specific section
                displayed_courses.append(display_unit)
            else:
                print(f"Warning: Original course {course_id_str} not found for section {section_code_to_display}")

    # Separate by credit hour for display (which determines room type)
    # 3ch courses → Lecture Halls, 1ch courses → Labs
    lecture_courses = [c for c in displayed_courses if str(c.get('credit_hour', '3')) == '3']
    lab_courses = [c for c in displayed_courses if str(c.get('credit_hour', '3')) == '1']

    return render_template(
        "pages/autogenerate_confirm_autopick.html",
        active_page="generate",
        floor_number=floor_number,
        lecture_courses=lecture_courses,
        lab_courses=lab_courses,
        total_courses=len(displayed_courses) # Use the new list length
    )

@app.route("/autogenerate_pick_courses")
@login_required
def autogenerate_pick_courses():
    """Show manual course selection page"""
    floor_number = request.args.get('floor', type=int)
    if not floor_number:
        return redirect(url_for('autogenerate_select_floor'))

    # TODO: Implement manual course selection
    return "Manual course selection - Coming soon!", 200

@app.route("/execute_autogenerate_scheduling")
@login_required
def execute_autogenerate_scheduling():
    """Execute the genetic algorithm and create the timetable"""
    floor_number = request.args.get('floor', type=int)

    if not floor_number or 'autopicked_sections' not in session: # Check new session key
        return redirect(url_for('autogenerate_select_floor'))

    try:
        # Get selected sections (course_id, section_code) from session
        selected_sections_from_session = session.get('autopicked_sections', [])
        
        if not selected_sections_from_session:
            return jsonify({'success': False, 'error': 'No course sections selected for scheduling'}), 400

        # Reconstruct full course objects for each selected section
        selected_schedulable_units = []
        course_ids_to_fetch = list(set([cid for cid, _ in selected_sections_from_session]))
        
        db_courses_map = {str(c['_id']): c for c in courses_collection.find({'_id': {'$in': [ObjectId(cid) for cid in course_ids_to_fetch]}})}

        for course_id_str, section_code_to_schedule in selected_sections_from_session:
            original_course = db_courses_map.get(course_id_str)
            if original_course:
                schedulable_unit = original_course.copy()
                schedulable_unit['_id'] = original_course['_id'] # Ensure _id remains ObjectId
                schedulable_unit['section_code'] = section_code_to_schedule
                selected_schedulable_units.append(schedulable_unit)
        
        if not selected_schedulable_units:
            print("ERROR: No schedulable units prepared")
            return jsonify({'success': False, 'error': 'Failed to prepare courses for scheduling'}), 400

        print(f"Schedulable units prepared: {len(selected_schedulable_units)}")

        # Get floor rooms
        all_rooms = list(rooms_collection.find({}))
        floor_rooms = []
        for room in all_rooms:
            room_floor = extract_floor_number_from_room(room.get('room_number', ''))
            if room_floor and room_floor.isdigit() and int(room_floor) == floor_number:
                floor_rooms.append(room)

        if not floor_rooms:
            print(f"ERROR: No rooms found on floor {floor_number}")
            return jsonify({'success': False, 'error': 'No rooms found on this floor'}), 400

        print(f"Floor rooms found: {len(floor_rooms)}")

        print(f"\n{'='*60}")
        print(f"STARTING GENETIC ALGORITHM SCHEDULING")
        print(f"Floor: {floor_number}")
        print(f"Courses to schedule: {len(selected_schedulable_units)}")
        print(f"Available rooms: {len(floor_rooms)}")

        # Check if we need to preserve existing schedules
        autogenerate_mode = session.get('autogenerate_mode', 'replace')
        if autogenerate_mode == 'add':
            # Get existing schedules on this floor to avoid conflicts
            existing_schedules = list(scheduled_classes_collection.find({'floor': floor_number}))
            print(f"Existing classes to preserve: {len(existing_schedules)}")
        else:
            existing_schedules = []

        print(f"{'='*60}\n")

        # Run genetic algorithm
        try:
            scheduler = TimetableScheduler(selected_schedulable_units, floor_rooms, floor_number)

            # Pass existing schedules if in "add mode"
            if existing_schedules:
                scheduler.existing_schedules = existing_schedules

            best_schedule, fitness_score = scheduler.evolve()
        except Exception as ga_error:
            print(f"ERROR in genetic algorithm: {str(ga_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Scheduling failed: {str(ga_error)}'}), 500

        print(f"\n{'='*60}")
        print(f"SCHEDULING COMPLETE")
        print(f"Final fitness score: {fitness_score}")
        print(f"Courses scheduled: {len(best_schedule)}/{len(selected_schedulable_units)}")
        print(f"{'='*60}\n")

        # Check if we're in "add mode" (preserve existing) or "replace mode" (delete existing)
        autogenerate_mode = session.get('autogenerate_mode', 'replace')

        if autogenerate_mode == 'replace':
            # Delete all existing classes on the floor before adding new ones
            result = scheduled_classes_collection.delete_many({'floor': floor_number})
            print(f"✓ Deleted {result.deleted_count} existing classes from floor {floor_number}")
        else:
            # In "add mode", keep existing classes
            existing_count = scheduled_classes_collection.count_documents({'floor': floor_number})
            print(f"✓ Preserving {existing_count} existing classes on floor {floor_number}")

        # Save schedule to database
        scheduled_count = 0
        for gene in best_schedule:
            original_course_for_db = db_courses_map.get(gene['course_id'])
            if not original_course_for_db:
                print(f"Warning: could not find original course for gene {gene}")
                continue
                
            scheduled_class = {
                'course_id': ObjectId(gene['course_id']),
                'course_name': gene['course_name'],
                'section_code': gene['section_code'],
                'teacher_registration': original_course_for_db.get('teacher_registration'),
                'teacher_name': gene['teacher_name'],
                'course_type': original_course_for_db.get('course_type'),
                'credit_hour': original_course_for_db.get('credit_hour'),
                'shift': original_course_for_db.get('shift'),
                'floor': floor_number,
                'room_number': int(gene['room']['room_number']),
                'day': gene['day'],
                'start_time': gene['time_slot'][0],
                'end_time': gene['time_slot'][1]
            }
            scheduled_classes_collection.insert_one(scheduled_class)
            scheduled_count += 1

        # Clear session data
        session.pop('autopicked_sections', None)
        session.pop('autogenerate_floor', None)
        session.pop('autogenerate_mode', None)  # Clear the mode flag

        print(f"✓ Saved {scheduled_count} classes to database")

        # Redirect to timetable view
        return redirect(url_for('view_autogenerated_timetable', floor=floor_number,
                               scheduled=scheduled_count, total=len(selected_schedulable_units)))

    except Exception as e:
        print(f"Error during scheduling: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/view_autogenerated_timetable")
@login_required
def view_autogenerated_timetable():
    """View the generated timetable for a floor"""
    floor_number = request.args.get('floor', type=int)
    scheduled = request.args.get('scheduled', type=int, default=0)
    total = request.args.get('total', type=int, default=0)

    if not floor_number:
        return redirect(url_for('autogenerate_select_floor'))

    # Get all scheduled classes for this floor
    scheduled_classes_raw = list(scheduled_classes_collection.find({'floor': floor_number}))

    # Convert ObjectId to string for JSON serialization
    scheduled_classes = []
    for sc in scheduled_classes_raw:
        scheduled_classes.append({
            'course_id': str(sc.get('course_id', '')),
            'course_code': sc.get('course_code', ''),
            'course_name': sc.get('course_name', ''),
            'teacher_name': sc.get('teacher_name', ''),
            'floor': sc.get('floor'),
            'room_number': sc.get('room_number'),
            'day': sc.get('day', ''),
            'start_time': sc.get('start_time', ''),
            'end_time': sc.get('end_time', '')
        })

    # Get all rooms on this floor
    all_rooms = list(rooms_collection.find({}))
    floor_rooms = []

    for room in all_rooms:
        room_floor = extract_floor_number_from_room(room.get('room_number', ''))
        if room_floor and room_floor.isdigit() and int(room_floor) == floor_number:
            floor_rooms.append({
                'room_number': room.get('room_number'),
                'type': room.get('type', ''),
                'capacity': room.get('capacity', 0)
            })

    # Sort rooms by room number
    floor_rooms.sort(key=lambda r: r.get('room_number', 0))

    return render_template(
        "pages/view_autogenerated_timetable.html",
        active_page="generate",
        floor_number=floor_number,
        scheduled_classes=scheduled_classes,
        rooms=floor_rooms,
        scheduled_count=scheduled,
        total_count=total,
        days=DAYS_OF_WEEK
    )

@app.route("/regenerate_floor")
@login_required
def regenerate_floor():
    """Delete existing schedule for a floor and redirect to course selection"""
    floor_number = request.args.get('floor', type=int)

    if not floor_number:
        return redirect(url_for('autogenerate_select_floor'))

    print(f"\n{'='*60}")
    print(f"REGENERATING FLOOR {floor_number}")
    print(f"{'='*60}")

    # Check current scheduled classes before deletion
    before_count = scheduled_classes_collection.count_documents({'floor': floor_number})
    print(f"Classes on floor {floor_number} before deletion: {before_count}")

    # Delete all scheduled classes for this floor
    result = scheduled_classes_collection.delete_many({'floor': floor_number})
    deleted_count = result.deleted_count

    # Verify deletion
    after_count = scheduled_classes_collection.count_documents({'floor': floor_number})
    print(f"Classes deleted: {deleted_count}")
    print(f"Classes remaining on floor {floor_number}: {after_count}")

    # Check total scheduled classes across all floors
    total_scheduled = scheduled_classes_collection.count_documents({})
    print(f"Total scheduled classes across all floors: {total_scheduled}")
    print(f"{'='*60}\n")

    # Redirect to course selection page (autopick or manual pick)
    return redirect(url_for('autogenerate_configure', floor=floor_number))

@app.route("/autogenerate_all_three")
@login_required
def autogenerate_all_three():
    """Autogenerate schedule for a floor WITHOUT deleting existing classes"""
    floor_number = request.args.get('floor', type=int)

    if not floor_number:
        return redirect(url_for('autogenerate_select_floor'))

    print(f"\n{'='*60}")
    print(f"AUTOGENERATE FOR FLOOR {floor_number} (WITHOUT DELETING)")
    print(f"{'='*60}")

    # Set a session flag to indicate we're in "add mode" (don't delete existing)
    session['autogenerate_mode'] = 'add'  # 'add' mode preserves existing schedules

    # Redirect to course selection page (same as regenerate, but without deletion)
    return redirect(url_for('autogenerate_configure', floor=floor_number))

@app.route("/get_floors_with_capacity")
@login_required
def get_floors_with_capacity():
    """Get all floors with scheduling capacity calculation"""
    try:
        # Get all rooms and extract unique floor numbers
        all_rooms = list(rooms_collection.find({}))
        floors_dict = {}

        # Extract floors from room numbers
        for room in all_rooms:
            floor_num = extract_floor_number_from_room(room.get('room_number', ''))
            if floor_num and floor_num.isdigit():
                if floor_num not in floors_dict:
                    floors_dict[floor_num] = {'lecture_halls': 0, 'labs': 0}

                if room.get('type') == 'Lecture Hall':
                    floors_dict[floor_num]['lecture_halls'] += 1
                elif room.get('type') == 'Lab':
                    floors_dict[floor_num]['labs'] += 1

        # Also check floors collection for floors without rooms
        floors_from_db = list(floors_collection.find({}))
        for floor_doc in floors_from_db:
            floor_num = str(floor_doc.get('floor_number', ''))
            if floor_num and floor_num.isdigit() and floor_num not in floors_dict:
                floors_dict[floor_num] = {'lecture_halls': 0, 'labs': 0}

        # Build floors data with capacity
        floors_data = []
        for floor_num, counts in floors_dict.items():
            lecture_halls = counts['lecture_halls']
            labs = counts['labs']
            capacity = calculate_floor_capacity(lecture_halls, labs)

            # Check if floor has existing schedule
            scheduled_count = scheduled_classes_collection.count_documents({'floor': int(floor_num)})
            has_schedule = scheduled_count > 0

            floors_data.append({
                'floor_number': int(floor_num),
                'total_rooms': lecture_halls + labs,
                'lecture_halls': lecture_halls,
                'labs': labs,
                'lecture_capacity': capacity['lecture_capacity'],
                'lab_capacity': capacity['lab_capacity'],
                'total_capacity': capacity['total_capacity'],
                'has_schedule': has_schedule,
                'scheduled_count': scheduled_count
            })

        # Sort by floor number
        floors_data.sort(key=lambda x: x['floor_number'])

        return jsonify({
            'success': True,
            'floors': floors_data,
            'config': {
                'hours_per_day': HOURS_PER_DAY,
                'days_per_week': DAYS_PER_WEEK,
                'start_time': SCHEDULE_START_TIME,
                'end_time': SCHEDULE_END_TIME
            }
        })
    except Exception as e:
        print(f"Error getting floors with capacity: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/view_generated_timetable")
@login_required
def view_generated_timetable():
    return render_template(
        "timetables/timetable_base_v2.html",
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
    return render_template("pages/selectFloorEdit_v2.html", active_page="manual_edit")

@app.route("/edit_timetable/<int:floor_number>")
@login_required
def edit_timetable_floor(floor_number):
    return render_template(
        "timetables/timetable_base_v2.html",
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
    return render_template("pages/editByCourse_v2.html", active_page="manual_edit")

@app.route("/manual_edit_by_room")
@login_required
def manual_edit_by_room():
    """Show room list for manual scheduling"""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template("pages/editByRoom_v2.html", active_page="manual_edit")

@app.route("/get_all_courses_with_sections", methods=["GET"])
@login_required
def get_all_courses_with_sections():
    """Get all courses with ONLY their unscheduled sections (for scheduling mode)"""
    try:
        # Get all scheduled classes to identify what's already scheduled
        all_scheduled_classes = list(scheduled_classes_collection.find({}))

        # Build a set of scheduled course_id + section combinations
        scheduled_sections = set()
        for cls in all_scheduled_classes:
            course_id = cls.get('course_id')
            section_code = cls.get('section_code')
            if course_id and section_code:
                scheduled_sections.add(f"{course_id}_{section_code}")

        print(f"DEBUG: Found {len(scheduled_sections)} already scheduled sections")

        courses_list = list(courses_collection.find({}))
        courses_data = []

        for course in courses_list:
            course_id = str(course.get('_id'))

            # Get teacher name
            teacher = users_collection.find_one({'registration_number': course.get('teacher_registration')})
            teacher_name = teacher.get('username', 'Unknown') if teacher else 'Unknown'

            # Handle both old (section_code) and new (section_codes) format
            all_sections = course.get('section_codes', [])
            if not all_sections and course.get('section_code'):
                # Old format - convert to array
                all_sections = [course.get('section_code')]

            # Filter out already scheduled sections
            unscheduled_sections = [
                section for section in all_sections
                if f"{course_id}_{section}" not in scheduled_sections
            ]

            # Only include course if it has unscheduled sections
            if unscheduled_sections:
                courses_data.append({
                    '_id': course_id,
                    'course_name': course.get('course_name', ''),
                    'credit_hour': course.get('credit_hour', 0),
                    'course_type': course.get('course_type', ''),
                    'shift': course.get('shift', ''),
                    'teacher_name': teacher_name,
                    'teacher_registration': course.get('teacher_registration', ''),
                    'sections': unscheduled_sections  # Only unscheduled sections
                })

        # Sort by course name
        courses_data.sort(key=lambda x: x['course_name'])

        print(f"DEBUG: Returning {len(courses_data)} courses with unscheduled sections")

        return jsonify({
            'success': True,
            'courses': courses_data
        })
    except Exception as e:
        print(f"DEBUG: Error in get_all_courses_with_sections: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/get_scheduled_courses_with_sections", methods=["GET"])
@login_required
def get_scheduled_courses_with_sections():
    """Get only courses that have scheduled classes, with their scheduled sections"""
    try:
        # Get all scheduled classes
        all_scheduled_classes = list(scheduled_classes_collection.find({}))

        # Group by course_id and section_code
        scheduled_courses_map = {}
        for cls in all_scheduled_classes:
            course_id = cls.get('course_id')
            section_code = cls.get('section_code')
            if course_id and section_code:
                if course_id not in scheduled_courses_map:
                    scheduled_courses_map[course_id] = set()
                scheduled_courses_map[course_id].add(section_code)

        print(f"DEBUG: Found {len(scheduled_courses_map)} courses with scheduled classes")

        # Get course details for scheduled courses
        courses_data = []
        for course_id, sections_set in scheduled_courses_map.items():
            try:
                from bson.objectid import ObjectId
                course = courses_collection.find_one({'_id': ObjectId(course_id)})

                if course:
                    # Get teacher name
                    teacher = users_collection.find_one({'registration_number': course.get('teacher_registration')})
                    teacher_name = teacher.get('username', 'Unknown') if teacher else 'Unknown'

                    courses_data.append({
                        '_id': str(course.get('_id')),
                        'course_name': course.get('course_name', ''),
                        'credit_hour': course.get('credit_hour', 0),
                        'course_type': course.get('course_type', ''),
                        'shift': course.get('shift', ''),
                        'teacher_name': teacher_name,
                        'teacher_registration': course.get('teacher_registration', ''),
                        'sections': sorted(list(sections_set))  # Only scheduled sections
                    })
            except Exception as e:
                print(f"DEBUG: Error processing course {course_id}: {str(e)}")
                continue

        # Sort by course name
        courses_data.sort(key=lambda x: x.get('course_name', ''))

        print(f"DEBUG: Returning {len(courses_data)} courses")

        return jsonify({
            'success': True,
            'courses': courses_data
        })
    except Exception as e:
        print(f"DEBUG: Error in get_scheduled_courses_with_sections: {str(e)}")
        import traceback
        traceback.print_exc()
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

@app.route("/edit_scheduled_classes")
@login_required
def edit_scheduled_classes_page():
    """Show page to edit scheduled classes for a course section"""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template("pages/editScheduledClasses_v2.html", active_page="generate")

@app.route("/edit_scheduled_classes_by_room")
@login_required
def edit_scheduled_classes_by_room_page():
    """Show page to edit scheduled classes for a specific room"""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template("pages/editScheduledClassesByRoom_v2.html", active_page="generate")

@app.route("/design_system_demo")
@login_required
def design_system_demo():
    """Show the new design system demo page"""
    return render_template("pages/design_system_demo.html", active_page="demo")

@app.route("/save_scheduled_class", methods=["POST"])
@login_required
def save_scheduled_class():
    """Save a scheduled class to the database"""
    print("=== Save Scheduled Class Request Started ===")
    print(f"Session: {session.get('username')}, Role: {session.get('role')}")

    if session.get('role') != 'admin':
        print("ERROR: Unauthorized access attempt")
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        from bson.objectid import ObjectId

        data = request.get_json()
        print(f"Request data: {data}")

        course_id = data.get('course_id')
        section_code = data.get('section_code')
        day = data.get('day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        room_number = data.get('room_number')

        print(f"Parsed fields - Course ID: {course_id}, Section: {section_code}, Day: {day}, Time: {start_time}-{end_time}, Room: {room_number}")

        # Validation
        if not all([course_id, section_code, day, start_time, end_time, room_number]):
            missing_fields = []
            if not course_id: missing_fields.append('course_id')
            if not section_code: missing_fields.append('section_code')
            if not day: missing_fields.append('day')
            if not start_time: missing_fields.append('start_time')
            if not end_time: missing_fields.append('end_time')
            if not room_number: missing_fields.append('room_number')

            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            print(f"ERROR: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400

        # Get course details
        print(f"Looking up course with ID: {course_id}")
        try:
            course = courses_collection.find_one({'_id': ObjectId(course_id)})
        except Exception as e:
            print(f"ERROR: Invalid course ID format: {e}")
            return jsonify({'success': False, 'error': 'Invalid course ID. Please refresh the page and try again.'}), 400

        if not course:
            print(f"ERROR: Course not found with ID: {course_id}")
            return jsonify({'success': False, 'error': 'Course not found'}), 404

        print(f"Found course: {course.get('course_name')}")

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

        # Extract floor from room number (e.g., room 201 -> floor 2)
        floor_number = None
        try:
            room_num_str = str(room_number)
            if len(room_num_str) >= 3:
                floor_number = int(room_num_str[:-2])  # Extract floor from room number
        except (ValueError, TypeError):
            floor_number = room.get('floor')  # Fallback to room's floor field if extraction fails

        print(f"DEBUG: Scheduling class in room {room_number}, extracted floor: {floor_number}")

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
            'floor': floor_number,
            'created_at': datetime.now(),
            'created_by': session.get('username')
        }

        # Insert into database
        print(f"Inserting scheduled class: {scheduled_class}")
        result = scheduled_classes_collection.insert_one(scheduled_class)
        print(f"Successfully inserted scheduled class with ID: {result.inserted_id}")

        return jsonify({
            'success': True,
            'message': 'Class scheduled successfully'
        })

    except Exception as e:
        print(f"ERROR in save_scheduled_class: {str(e)}")
        import traceback
        traceback.print_exc()

        # Return detailed error message
        error_message = str(e)
        if "ObjectId" in error_message:
            error_message = "Invalid course ID format. Please refresh the page and try again."
        elif "duplicate" in error_message.lower():
            error_message = "This class schedule already exists."
        elif "room_number" in error_message.lower():
            error_message = "Invalid room number. Please select a valid room."

        return jsonify({'success': False, 'error': f'Error scheduling class: {error_message}'}), 500

# Route for Teacher View
@app.route("/teacher")
@login_required
def teacher_view():
    # Get teacher's registration number from session
    teacher_reg = session.get('registration_number')

    return render_template(
        "timetables/timetable_base_v2.html",
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
        "pages/teacher_about_v2.html",
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
    return render_template("pages/adminPanel_v2.html", active_page="admin")

@app.route("/import_data")
@login_required
def import_data():
    """Import data page for importing courses and faculty via CSV"""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template("pages/import_data_v2.html", active_page="import")

@app.route("/import_csv", methods=["POST"])
@login_required
def import_csv_data():
    """Import courses or faculty from CSV file"""
    print("=== CSV Import Request Started ===")
    print(f"Session: {session.get('username')}, Role: {session.get('role')}")
    print(f"Files in request: {list(request.files.keys())}")
    print(f"Form data: {dict(request.form)}")

    if session.get('role') != 'admin':
        print("ERROR: Unauthorized access attempt")
        return jsonify({'success': False, 'error': 'Unauthorized. Admin access required.'}), 403

    try:
        # Get file and type from request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded. Please select a CSV file.'}), 400

        file = request.files['file']
        import_type = request.form.get('type')

        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected. Please choose a CSV file to upload.'}), 400

        # Validate file extension
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': f'Invalid file type. Expected .csv file but got: {file.filename}'}), 400

        if not import_type or import_type not in ['courses', 'faculty']:
            return jsonify({'success': False, 'error': f'Invalid import type: "{import_type}". Must be either "courses" or "faculty".'}), 400

        # Read CSV file
        try:
            # Read and decode file, removing BOM if present
            file_content = file.stream.read().decode("utf-8-sig")  # utf-8-sig automatically removes BOM
            stream = io.StringIO(file_content, newline=None)
            csv_reader = csv.DictReader(stream)
        except UnicodeDecodeError:
            return jsonify({'success': False, 'error': 'File encoding error. Please ensure your CSV file is UTF-8 encoded.'}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to read CSV file: {str(e)}'}), 400

        if import_type == 'courses':
            print(f"Importing courses...")
            result = import_courses_from_csv(csv_reader)
            print(f"Course import result: {result}")
            return result
        elif import_type == 'faculty':
            print(f"Importing faculty...")
            result = import_faculty_from_csv(csv_reader)
            print(f"Faculty import result: {result}")
            return result

    except Exception as e:
        print(f"Error in import_csv_data: {str(e)}")  # Log to console for admin debugging
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Unexpected error processing file: {str(e)}'}), 500

def import_courses_from_csv(csv_reader):
    """Import courses from CSV data"""
    required_columns = ['course_name', 'credit_hour', 'course_type', 'shift', 'teacher_registration']

    try:
        rows = list(csv_reader)

        # Validate columns
        if not rows:
            return jsonify({'success': False, 'error': 'CSV file is empty. Please add at least one course row with headers.'}), 400

        # Check required columns
        first_row_keys = list(rows[0].keys())
        missing_columns = [col for col in required_columns if col not in first_row_keys]
        if missing_columns:
            return jsonify({
                'success': False,
                'error': f'Missing required columns: {", ".join(missing_columns)}. Found columns: {", ".join(first_row_keys)}'
            }), 400

        imported_count = 0
        errors = []
        missing_teachers = []  # Track missing teacher registrations

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
                    errors.append(f"Row {idx}: Teacher with registration number '{teacher_registration}' not found. Please first enroll this user in faculty before assigning courses")
                    # Add to missing teachers list (avoid duplicates)
                    if teacher_registration not in missing_teachers:
                        missing_teachers.append(teacher_registration)
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
            if missing_teachers:
                message = f'Successfully imported {imported_count} course(s). {len(errors)} row(s) could not be imported. Please download the text file to see unsuccessful imports.'
            else:
                message = f'Successfully imported {imported_count} course(s). All courses imported successfully!'
            response_data = {'success': True, 'message': message, 'count': imported_count}
            # Include missing teachers if any
            if missing_teachers:
                response_data['missing_teachers'] = missing_teachers
                response_data['failed_count'] = len(errors)
            return jsonify(response_data)
        else:
            if missing_teachers:
                error_message = f'No courses imported. All {len(errors)} row(s) failed due to missing teachers. Please download the text file for details.'
            else:
                error_message = f'No courses imported. {len(errors)} row(s) had errors. Please check your CSV file and try again.'
            print(f"Course import failed - All errors: {errors}")  # Log all errors to console for debugging
            response_data = {'success': False, 'error': error_message}
            # Include missing teachers if any
            if missing_teachers:
                response_data['missing_teachers'] = missing_teachers
            return jsonify(response_data), 400

    except Exception as e:
        print(f"Error importing courses: {str(e)}")  # Log to console
        import traceback
        traceback.print_exc()  # Print full stack trace to console
        return jsonify({'success': False, 'error': f'Error importing courses: {str(e)}'}), 500

def import_faculty_from_csv(csv_reader):
    """Import faculty from CSV data"""
    required_columns = ['username', 'registration_number', 'email']

    try:
        rows = list(csv_reader)

        # Validate columns
        if not rows:
            return jsonify({'success': False, 'error': 'CSV file is empty. Please add at least one faculty row with headers.'}), 400

        # Check required columns
        first_row_keys = list(rows[0].keys())
        missing_columns = [col for col in required_columns if col not in first_row_keys]
        if missing_columns:
            return jsonify({
                'success': False,
                'error': f'Missing required columns: {", ".join(missing_columns)}. Found columns: {", ".join(first_row_keys)}'
            }), 400

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
                if len(errors) > 5:
                    message += f' (and {len(errors) - 5} more...)'
            return jsonify({'success': True, 'message': message, 'count': imported_count})
        else:
            error_details = "; ".join(errors[:10])
            if len(errors) > 10:
                error_details += f' (and {len(errors) - 10} more errors...)'
            error_message = f'No faculty imported. Total errors: {len(errors)}. Details: {error_details}'
            print(f"Faculty import failed - All errors: {errors}")  # Log all errors to console
            return jsonify({'success': False, 'error': error_message}), 400

    except Exception as e:
        print(f"Error importing faculty: {str(e)}")  # Log to console
        import traceback
        traceback.print_exc()  # Print full stack trace to console
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
        "management/management_v2.html",
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
    return render_template("management/room_floor_selection_v2.html", active_page="rooms")

@app.route("/manage_rooms/all")
@login_required
def manage_rooms_all():
    # View all rooms in one table
    from_dashboard = request.args.get('from_dashboard', 'false').lower() == 'true'
    return render_template(
        "management/management_v2.html",
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
        "management/management_v2.html",
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
    """Get all rooms on a specific floor with scheduled class counts"""
    # Get all rooms and filter by floor (handles both string and integer room_number)
    all_rooms = list(rooms_collection.find({}))

    # Get all scheduled classes to count classes per room
    all_scheduled_classes = list(scheduled_classes_collection.find({}))

    # Count scheduled classes per room
    room_class_count = {}
    for cls in all_scheduled_classes:
        room_num = str(cls.get('room_number', ''))
        if room_num:
            room_class_count[room_num] = room_class_count.get(room_num, 0) + 1

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
            # Add scheduled class count
            room_data['scheduled_classes_count'] = room_class_count.get(room_number_str, 0)
            rooms_with_floor.append(room_data)

    # Sort by room number
    rooms_with_floor.sort(key=lambda x: int(x.get('room_number', 0)))

    return {"items": rooms_with_floor}

@app.route("/get_rooms_with_classes_by_floor/<int:floor_number>", methods=["GET"])
@login_required
def get_rooms_with_classes_by_floor(floor_number):
    """Get only rooms on a specific floor that have scheduled classes"""
    try:
        # Get all scheduled classes
        all_scheduled_classes = list(scheduled_classes_collection.find({}))

        # Count scheduled classes per room and track which rooms have classes
        room_class_count = {}
        rooms_with_classes = set()

        for cls in all_scheduled_classes:
            room_num = cls.get('room_number')
            if room_num:
                room_num_str = str(room_num)
                # Extract floor from room number
                if len(room_num_str) >= 3:
                    room_floor = room_num_str[:-2]
                    # Only include if on the requested floor
                    if room_floor == str(floor_number):
                        rooms_with_classes.add(room_num_str)
                        room_class_count[room_num_str] = room_class_count.get(room_num_str, 0) + 1

        print(f"DEBUG: Found {len(rooms_with_classes)} rooms with classes on floor {floor_number}: {rooms_with_classes}")

        # Get all rooms on this floor
        all_rooms = list(rooms_collection.find({}))

        rooms_with_floor = []
        for room in all_rooms:
            room_number_str = str(room.get("room_number", ""))

            # Only include rooms that have scheduled classes
            if room_number_str in rooms_with_classes:
                room_data = room.copy()
                room_data['_id'] = str(room_data['_id'])
                room_data["floor_number"] = _extract_floor_from_room_number(room_number_str)
                # Ensure availability field exists with default value
                if 'availability' not in room_data or not room_data['availability']:
                    room_data['availability'] = 'Available'
                # Add scheduled class count
                room_data['scheduled_classes_count'] = room_class_count.get(room_number_str, 0)
                rooms_with_floor.append(room_data)

        # Sort by room number
        rooms_with_floor.sort(key=lambda x: int(x.get('room_number', 0)))

        print(f"DEBUG: Returning {len(rooms_with_floor)} rooms")

        return {"items": rooms_with_floor}

    except Exception as e:
        print(f"DEBUG: Error in get_rooms_with_classes_by_floor: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"items": []}

@app.route("/delete_floor/<int:floor_number>", methods=["DELETE"])
@login_required
def delete_floor(floor_number):
    """Delete an entire floor and all its rooms"""
    try:
        # Get all rooms and find rooms on this floor
        all_rooms = list(rooms_collection.find({}))
        rooms_to_delete = []
        rooms_with_classes = []

        for room in all_rooms:
            room_number_str = str(room.get("room_number", ""))
            if len(room_number_str) >= 3:
                room_floor = room_number_str[:-2]
                if room_floor == str(floor_number):
                    room_number = room.get('room_number')
                    # Check if this room has any scheduled classes
                    scheduled_class = scheduled_classes_collection.find_one({'room': room_number})
                    if scheduled_class:
                        rooms_with_classes.append(room_number)
                    else:
                        rooms_to_delete.append(room['_id'])

        # If any rooms have scheduled classes, prevent deletion
        if rooms_with_classes:
            return {
                "success": False,
                "error": f"Cannot delete floor {floor_number}. The following room(s) have scheduled classes: {', '.join(map(str, rooms_with_classes))}. Please reschedule all classes from these rooms before deleting the floor."
            }, 400

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
        "management/management_v2.html",
        header_title="Manage Courses",
        item_name="Course",
        add_url="/add_course",
        get_url="/get_courses",
        form_fields=[
            {"name": "course_name", "label": "Course Name", "type": "text", "table_display": True, "form_display": True},
            {"name": "course_type", "label": "Course Type", "type": "select", "options": ["Lecture", "Lab"], "table_display": True, "form_display": True},
            {"name": "credit_hour", "label": "Credit Hour (Auto-set)", "type": "select", "options": ["3", "1"], "table_display": True, "form_display": True},
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

@app.route("/get_courses_by_shift/<shift>", methods=["GET"])
@login_required
def get_courses_by_shift(shift):
    """Get all courses for a specific shift"""
    try:
        # Get courses for the specified shift
        courses_list = list(courses_collection.find({'shift': shift}))

        courses_data = []
        for course in courses_list:
            # Get section codes (handle both old and new format)
            sections = course.get('section_codes', [])
            if not sections and course.get('section_code'):
                sections = [course.get('section_code')]

            courses_data.append({
                '_id': str(course.get('_id')),
                'course_name': course.get('course_name'),
                'credit_hour': course.get('credit_hour'),
                'course_type': course.get('course_type'),
                'shift': course.get('shift'),
                'teacher_name': course.get('teacher_name'),
                'teacher_registration': course.get('teacher_registration'),
                'sections': sections
            })

        return jsonify({
            'success': True,
            'courses': courses_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/add_course", methods=["POST"])
@login_required
def add_course():
    data = request.get_json()

    # ENFORCE RULE: Auto-set credit hours based on course type
    course_type = data.get('course_type', 'Lecture')
    if course_type == 'Lecture':
        data['credit_hour'] = '3'
    elif course_type == 'Lab':
        data['credit_hour'] = '1'

    # Validate that credit hours match course type
    credit_hour = data.get('credit_hour', '3')
    if course_type == 'Lecture' and str(credit_hour) != '3':
        return {"success": False, "error": "Lecture courses must have 3 credit hours"}, 400
    if course_type == 'Lab' and str(credit_hour) != '1':
        return {"success": False, "error": "Lab courses must have 1 credit hour"}, 400

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
    """View timetable with optional room/teacher filters"""
    room_number = request.args.get('room')
    teacher_reg = request.args.get('teacher')

    # If no filters provided, show filter selection page
    if not room_number and not teacher_reg:
        return render_template("pages/selectFloor_v2.html", active_page="view_timetable")

    # Build title based on filters
    title_parts = []
    if room_number:
        title_parts.append(f"Room {room_number}")
    if teacher_reg:
        teacher = users_collection.find_one({'registration_number': teacher_reg})
        if teacher:
            title_parts.append(f"Teacher: {teacher.get('username')}")

    page_title = f"Timetable - {' & '.join(title_parts)}" if title_parts else "Timetable"

    return render_template(
        "timetables/timetable_base_v2.html",
        active_page="view_timetable",
        page_title="View Timetable",
        hide_top_bar=True,
        show_back_button=True,
        show_teacher_header=False,
        show_page_title=True,
        page_title_text=page_title,
        room_filter=room_number,
        teacher_filter=teacher_reg
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

        print(f"DEBUG: get_scheduled_classes called with room={room_number}, teacher={teacher_reg}, floor={floor_number}")

        # Build query based on filters
        query = {}
        if room_number:
            # Convert to int for consistent querying (room_numbers are now stored as int)
            query['room_number'] = int(room_number) if str(room_number).isdigit() else room_number

        if teacher_reg:
            query['teacher_registration'] = teacher_reg

        if floor_number:
            query['floor'] = int(floor_number)

        print(f"DEBUG: MongoDB query: {query}")

        # Get scheduled classes
        scheduled_classes = list(scheduled_classes_collection.find(query))

        print(f"DEBUG: Found {len(scheduled_classes)} classes")

        # Format the data
        classes_data = []
        for cls in scheduled_classes:
            classes_data.append({
                '_id': str(cls.get('_id')),
                'course_id': str(cls.get('course_id')),  # Convert ObjectId to string for JSON serialization
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
                'room_number': cls.get('room_number'),  # Already an int
                'floor': cls.get('floor')
            })

        return jsonify({
            'success': True,
            'classes': classes_data
        })
    except Exception as e:
        print(f"DEBUG: Error in get_scheduled_classes: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/get_scheduled_classes_by_course", methods=["GET"])
@login_required
def get_scheduled_classes_by_course():
    """Get scheduled classes for a specific course and section"""
    try:
        course_id = request.args.get('course_id')
        section_code = request.args.get('section_code')

        if not course_id or not section_code:
            return jsonify({'success': False, 'error': 'Missing course_id or section_code'}), 400

        # Get scheduled classes for this course and section
        scheduled_classes = list(scheduled_classes_collection.find({
            'course_id': course_id,
            'section_code': section_code
        }))

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

@app.route("/update_scheduled_class/<class_id>", methods=["PUT"])
@login_required
def update_scheduled_class(class_id):
    """Update an existing scheduled class"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        from bson.objectid import ObjectId

        data = request.get_json()
        day = data.get('day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        room_number = data.get('room_number')

        # Validation
        if not all([day, start_time, end_time, room_number]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Get the existing scheduled class
        existing_class = scheduled_classes_collection.find_one({'_id': ObjectId(class_id)})
        if not existing_class:
            return jsonify({'success': False, 'error': 'Scheduled class not found'}), 404

        # Get room details
        room = rooms_collection.find_one({'room_number': room_number})
        if not room:
            return jsonify({'success': False, 'error': 'Room not found'}), 404

        # Check for conflicts (exclude current class from conflict check)
        # 1. Check if room is already occupied at this time
        room_conflict = scheduled_classes_collection.find_one({
            '_id': {'$ne': ObjectId(class_id)},
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

        if room_conflict:
            return jsonify({
                'success': False,
                'error': f'Room {room_number} is already occupied on {day} at this time'
            }), 400

        # 2. Check if teacher is already teaching at this time
        teacher_conflict = scheduled_classes_collection.find_one({
            '_id': {'$ne': ObjectId(class_id)},
            'teacher_registration': existing_class.get('teacher_registration'),
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

        if teacher_conflict:
            return jsonify({
                'success': False,
                'error': f'Teacher is already scheduled for another class on {day} at this time'
            }), 400

        # Extract floor from room number (e.g., room 201 -> floor 2)
        floor_number = None
        try:
            room_num_str = str(room_number)
            if len(room_num_str) >= 3:
                floor_number = int(room_num_str[:-2])  # Extract floor from room number
        except (ValueError, TypeError):
            floor_number = room.get('floor')  # Fallback to room's floor field if extraction fails

        print(f"DEBUG: Updating class to room {room_number}, extracted floor: {floor_number}")

        # Update the scheduled class
        update_data = {
            'day': day,
            'start_time': start_time,
            'end_time': end_time,
            'room_number': room_number,
            'floor': floor_number
        }

        scheduled_classes_collection.update_one(
            {'_id': ObjectId(class_id)},
            {'$set': update_data}
        )

        return jsonify({
            'success': True,
            'message': 'Class updated successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/delete_scheduled_class/<class_id>", methods=["DELETE"])
@login_required
def delete_scheduled_class(class_id):
    """Delete a scheduled class"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        from bson.objectid import ObjectId

        result = scheduled_classes_collection.delete_one({'_id': ObjectId(class_id)})

        if result.deleted_count > 0:
            return jsonify({
                'success': True,
                'message': 'Class deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Class not found'}), 404

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
                # Check if availability is being changed to "Not Available"
                new_availability = data.get('availability', 'Available')
                current_room = item_to_update
                room_number = current_room.get('room_number')

                # If changing to "Not Available", check for scheduled classes
                if new_availability == "Not Available" and current_room.get('availability') == 'Available':
                    # Find all scheduled classes in this room
                    scheduled_classes = list(scheduled_classes_collection.find({'room_number': room_number}))
                    if scheduled_classes:
                        # Build a detailed error message with class information
                        class_details = []
                        for cls in scheduled_classes:
                            class_details.append({
                                'course_name': cls.get('course_name', 'Unknown'),
                                'section': cls.get('section_code', 'N/A'),
                                'day': cls.get('day', 'N/A'),
                                'time': f"{cls.get('start_time', 'N/A')} - {cls.get('end_time', 'N/A')}"
                            })

                        return {
                            "success": False,
                            "error": f"Cannot mark room {room_number} as unavailable. There are {len(scheduled_classes)} class(es) scheduled in this room.",
                            "scheduled_classes": class_details
                        }, 400

                # Explicitly handle room updates to ensure all fields are updated
                update_data = {
                    'room_number': data.get('room_number'),
                    'type': data.get('type'),
                    'availability': new_availability
                }
                print(f"Updating room with data: {update_data}")  # Debug logging
            elif item_type == "course":
                # ENFORCE RULE: Auto-set credit hours based on course type
                course_type = data.get('course_type', 'Lecture')
                if course_type == 'Lecture':
                    data['credit_hour'] = '3'
                elif course_type == 'Lab':
                    data['credit_hour'] = '1'

                # Validate that credit hours match course type
                credit_hour = data.get('credit_hour', '3')
                if course_type == 'Lecture' and str(credit_hour) != '3':
                    return {"success": False, "error": "Lecture courses must have 3 credit hours"}, 400
                if course_type == 'Lab' and str(credit_hour) != '1':
                    return {"success": False, "error": "Lab courses must have 1 credit hour"}, 400

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

            # Special validation for room deletion
            if item_type == "room":
                room_number = item_to_delete.get('room_number')
                # Check if there are any scheduled classes in this room
                scheduled_classes = list(scheduled_classes_collection.find({'room_number': room_number}))
                if scheduled_classes:
                    # Build detailed error message
                    class_details = []
                    for cls in scheduled_classes:
                        class_details.append({
                            'course_name': cls.get('course_name', 'Unknown'),
                            'section': cls.get('section_code', 'N/A'),
                            'day': cls.get('day', 'N/A'),
                            'time': f"{cls.get('start_time', 'N/A')} - {cls.get('end_time', 'N/A')}"
                        })

                    return {
                        "success": False,
                        "error": f"Cannot delete room {room_number}. There are {len(scheduled_classes)} class(es) scheduled in this room.",
                        "scheduled_classes": class_details
                    }, 400

            collection.delete_one({"_id": item_to_delete["_id"]})
            return {"success": True}
    return {"error": "Item not found"}, 404

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Smart Scheduler')
    parser.add_argument('--port', type=int, default=None, help='Port to run the application on.')
    args = parser.parse_args()

    # Use Railway's PORT environment variable, or command line arg, or default to 5000
    port = int(os.environ.get('PORT', args.port or 5000))

    # Bind to 0.0.0.0 for cloud deployments (Railway, Render, etc.)
    # Debug mode is automatically disabled when not running locally
    app.run(host='0.0.0.0', port=port, debug=False)

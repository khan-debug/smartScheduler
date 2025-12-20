from flask import Flask, render_template, request, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
import os
from database import (
    get_db,
    teachers_collection,
    courses_collection,
    rooms_collection,
    time_slots_collection,
    schedule_entries_collection,
    serialize_doc,
    serialize_docs,
    create_indexes
)

app = Flask(__name__)

# Configuration
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


# Input validation helpers
def validate_teacher_data(data):
    """Validate teacher input data"""
    errors = []
    if not data:
        return ["Request body is required"]

    if 'name' not in data or not data['name'].strip():
        errors.append("Teacher name is required")
    elif len(data['name']) > 100:
        errors.append("Teacher name must be less than 100 characters")

    if 'email' not in data or not data['email'].strip():
        errors.append("Email is required")
    elif '@' not in data['email'] or '.' not in data['email']:
        errors.append("Invalid email format")
    elif len(data['email']) > 150:
        errors.append("Email must be less than 150 characters")

    return errors


def validate_course_data(data):
    """Validate course input data"""
    errors = []
    if not data:
        return ["Request body is required"]

    if 'name' not in data or not data['name'].strip():
        errors.append("Course name is required")
    elif len(data['name']) > 150:
        errors.append("Course name must be less than 150 characters")

    if 'code' not in data or not data['code'].strip():
        errors.append("Course code is required")
    elif len(data['code']) > 20:
        errors.append("Course code must be less than 20 characters")

    if 'department' not in data or not data['department'].strip():
        errors.append("Department is required")
    elif len(data['department']) > 100:
        errors.append("Department must be less than 100 characters")

    return errors


def validate_room_data(data):
    """Validate room input data"""
    errors = []
    if not data:
        return ["Request body is required"]

    if 'name' not in data or not data['name'].strip():
        errors.append("Room name is required")
    elif len(data['name']) > 50:
        errors.append("Room name must be less than 50 characters")

    if 'capacity' not in data:
        errors.append("Room capacity is required")
    elif not isinstance(data['capacity'], int) or data['capacity'] < 1:
        errors.append("Room capacity must be a positive integer")
    elif data['capacity'] > 1000:
        errors.append("Room capacity must be less than 1000")

    if 'room_type' not in data or not data['room_type'].strip():
        errors.append("Room type is required")
    elif data['room_type'] not in ['lecture', 'lab', 'seminar']:
        errors.append("Room type must be one of: lecture, lab, seminar")

    return errors


# API Routes for Teachers
@app.route("/api/teachers", methods=["POST"])
def create_teacher():
    try:
        teacher_data = request.get_json()

        # Validate input
        validation_errors = validate_teacher_data(teacher_data)
        if validation_errors:
            return jsonify({"message": "Validation failed", "errors": validation_errors}), 400

        # Create teacher document
        new_teacher = {
            "name": teacher_data["name"].strip(),
            "email": teacher_data["email"].strip().lower()
        }

        result = teachers_collection.insert_one(new_teacher)
        new_teacher["id"] = str(result.inserted_id)

        return jsonify({
            "message": "Teacher created successfully",
            "teacher": {
                "id": new_teacher["id"],
                "name": new_teacher["name"],
                "email": new_teacher["email"]
            }
        }), 201

    except DuplicateKeyError:
        return jsonify({"message": "A teacher with this email already exists"}), 409
    except Exception as e:
        app.logger.error(f"Error creating teacher: {str(e)}")
        return jsonify({"message": "An error occurred while creating the teacher"}), 500


@app.route("/api/teachers", methods=["GET"])
def get_teachers():
    try:
        teachers = list(teachers_collection.find())
        return jsonify(serialize_docs(teachers))
    except Exception as e:
        app.logger.error(f"Error fetching teachers: {str(e)}")
        return jsonify({"message": "An error occurred while fetching teachers"}), 500


@app.route("/api/teachers/<teacher_id>", methods=["GET"])
def get_teacher(teacher_id):
    try:
        teacher = teachers_collection.find_one({"_id": ObjectId(teacher_id)})
        if not teacher:
            return jsonify({"message": "Teacher not found"}), 404
        return jsonify(serialize_doc(teacher))
    except InvalidId:
        return jsonify({"message": "Invalid teacher ID"}), 400
    except Exception as e:
        app.logger.error(f"Error fetching teacher: {str(e)}")
        return jsonify({"message": "An error occurred while fetching the teacher"}), 500


@app.route("/api/teachers/<teacher_id>", methods=["PUT"])
def update_teacher(teacher_id):
    try:
        teacher_data = request.get_json()

        # Validate input
        validation_errors = validate_teacher_data(teacher_data)
        if validation_errors:
            return jsonify({"message": "Validation failed", "errors": validation_errors}), 400

        # Check if teacher exists
        teacher = teachers_collection.find_one({"_id": ObjectId(teacher_id)})
        if not teacher:
            return jsonify({"message": "Teacher not found"}), 404

        # Update teacher
        update_data = {
            "name": teacher_data["name"].strip(),
            "email": teacher_data["email"].strip().lower()
        }

        teachers_collection.update_one(
            {"_id": ObjectId(teacher_id)},
            {"$set": update_data}
        )

        updated_teacher = teachers_collection.find_one({"_id": ObjectId(teacher_id)})
        return jsonify({
            "message": "Teacher updated successfully",
            "teacher": serialize_doc(updated_teacher)
        })

    except InvalidId:
        return jsonify({"message": "Invalid teacher ID"}), 400
    except DuplicateKeyError:
        return jsonify({"message": "A teacher with this email already exists"}), 409
    except Exception as e:
        app.logger.error(f"Error updating teacher: {str(e)}")
        return jsonify({"message": "An error occurred while updating the teacher"}), 500


@app.route("/api/teachers/<teacher_id>", methods=["DELETE"])
def delete_teacher(teacher_id):
    try:
        teacher = teachers_collection.find_one({"_id": ObjectId(teacher_id)})
        if not teacher:
            return jsonify({"message": "Teacher not found"}), 404

        # Delete associated schedule entries
        schedule_entries_collection.delete_many({"teacher_id": teacher_id})

        # Delete teacher
        teachers_collection.delete_one({"_id": ObjectId(teacher_id)})

        return jsonify({"message": "Teacher deleted successfully"})
    except InvalidId:
        return jsonify({"message": "Invalid teacher ID"}), 400
    except Exception as e:
        app.logger.error(f"Error deleting teacher: {str(e)}")
        return jsonify({"message": "An error occurred while deleting the teacher"}), 500


# API Routes for Courses
@app.route("/api/courses", methods=["POST"])
def create_course():
    try:
        course_data = request.get_json()

        # Validate input
        validation_errors = validate_course_data(course_data)
        if validation_errors:
            return jsonify({"message": "Validation failed", "errors": validation_errors}), 400

        # Create course document
        new_course = {
            "name": course_data["name"].strip(),
            "code": course_data["code"].strip().upper(),
            "department": course_data["department"].strip()
        }

        result = courses_collection.insert_one(new_course)
        new_course["id"] = str(result.inserted_id)

        return jsonify({
            "message": "Course created successfully",
            "course": {
                "id": new_course["id"],
                "name": new_course["name"],
                "code": new_course["code"],
                "department": new_course["department"]
            }
        }), 201

    except DuplicateKeyError:
        return jsonify({"message": "A course with this code already exists"}), 409
    except Exception as e:
        app.logger.error(f"Error creating course: {str(e)}")
        return jsonify({"message": "An error occurred while creating the course"}), 500


@app.route("/api/courses", methods=["GET"])
def get_courses():
    try:
        courses = list(courses_collection.find())
        return jsonify(serialize_docs(courses))
    except Exception as e:
        app.logger.error(f"Error fetching courses: {str(e)}")
        return jsonify({"message": "An error occurred while fetching courses"}), 500


@app.route("/api/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    try:
        course = courses_collection.find_one({"_id": ObjectId(course_id)})
        if not course:
            return jsonify({"message": "Course not found"}), 404
        return jsonify(serialize_doc(course))
    except InvalidId:
        return jsonify({"message": "Invalid course ID"}), 400
    except Exception as e:
        app.logger.error(f"Error fetching course: {str(e)}")
        return jsonify({"message": "An error occurred while fetching the course"}), 500


@app.route("/api/courses/<course_id>", methods=["PUT"])
def update_course(course_id):
    try:
        course_data = request.get_json()

        # Validate input
        validation_errors = validate_course_data(course_data)
        if validation_errors:
            return jsonify({"message": "Validation failed", "errors": validation_errors}), 400

        # Check if course exists
        course = courses_collection.find_one({"_id": ObjectId(course_id)})
        if not course:
            return jsonify({"message": "Course not found"}), 404

        # Update course
        update_data = {
            "name": course_data["name"].strip(),
            "code": course_data["code"].strip().upper(),
            "department": course_data["department"].strip()
        }

        courses_collection.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": update_data}
        )

        updated_course = courses_collection.find_one({"_id": ObjectId(course_id)})
        return jsonify({
            "message": "Course updated successfully",
            "course": serialize_doc(updated_course)
        })

    except InvalidId:
        return jsonify({"message": "Invalid course ID"}), 400
    except DuplicateKeyError:
        return jsonify({"message": "A course with this code already exists"}), 409
    except Exception as e:
        app.logger.error(f"Error updating course: {str(e)}")
        return jsonify({"message": "An error occurred while updating the course"}), 500


@app.route("/api/courses/<course_id>", methods=["DELETE"])
def delete_course(course_id):
    try:
        course = courses_collection.find_one({"_id": ObjectId(course_id)})
        if not course:
            return jsonify({"message": "Course not found"}), 404

        # Delete associated schedule entries
        schedule_entries_collection.delete_many({"course_id": course_id})

        # Delete course
        courses_collection.delete_one({"_id": ObjectId(course_id)})

        return jsonify({"message": "Course deleted successfully"})
    except InvalidId:
        return jsonify({"message": "Invalid course ID"}), 400
    except Exception as e:
        app.logger.error(f"Error deleting course: {str(e)}")
        return jsonify({"message": "An error occurred while deleting the course"}), 500


# API Routes for Rooms
@app.route("/api/rooms", methods=["POST"])
def create_room():
    try:
        room_data = request.get_json()

        # Validate input
        validation_errors = validate_room_data(room_data)
        if validation_errors:
            return jsonify({"message": "Validation failed", "errors": validation_errors}), 400

        # Create room document
        new_room = {
            "name": room_data["name"].strip(),
            "capacity": room_data["capacity"],
            "room_type": room_data["room_type"].strip().lower()
        }

        result = rooms_collection.insert_one(new_room)
        new_room["id"] = str(result.inserted_id)

        return jsonify({
            "message": "Room created successfully",
            "room": {
                "id": new_room["id"],
                "name": new_room["name"],
                "capacity": new_room["capacity"],
                "room_type": new_room["room_type"]
            }
        }), 201

    except DuplicateKeyError:
        return jsonify({"message": "A room with this name already exists"}), 409
    except Exception as e:
        app.logger.error(f"Error creating room: {str(e)}")
        return jsonify({"message": "An error occurred while creating the room"}), 500


@app.route("/api/rooms", methods=["GET"])
def get_rooms():
    try:
        rooms = list(rooms_collection.find())
        return jsonify(serialize_docs(rooms))
    except Exception as e:
        app.logger.error(f"Error fetching rooms: {str(e)}")
        return jsonify({"message": "An error occurred while fetching rooms"}), 500


@app.route("/api/rooms/<room_id>", methods=["GET"])
def get_room(room_id):
    try:
        room = rooms_collection.find_one({"_id": ObjectId(room_id)})
        if not room:
            return jsonify({"message": "Room not found"}), 404
        return jsonify(serialize_doc(room))
    except InvalidId:
        return jsonify({"message": "Invalid room ID"}), 400
    except Exception as e:
        app.logger.error(f"Error fetching room: {str(e)}")
        return jsonify({"message": "An error occurred while fetching the room"}), 500


@app.route("/api/rooms/<room_id>", methods=["PUT"])
def update_room(room_id):
    try:
        room_data = request.get_json()

        # Validate input
        validation_errors = validate_room_data(room_data)
        if validation_errors:
            return jsonify({"message": "Validation failed", "errors": validation_errors}), 400

        # Check if room exists
        room = rooms_collection.find_one({"_id": ObjectId(room_id)})
        if not room:
            return jsonify({"message": "Room not found"}), 404

        # Update room
        update_data = {
            "name": room_data["name"].strip(),
            "capacity": room_data["capacity"],
            "room_type": room_data["room_type"].strip().lower()
        }

        rooms_collection.update_one(
            {"_id": ObjectId(room_id)},
            {"$set": update_data}
        )

        updated_room = rooms_collection.find_one({"_id": ObjectId(room_id)})
        return jsonify({
            "message": "Room updated successfully",
            "room": serialize_doc(updated_room)
        })

    except InvalidId:
        return jsonify({"message": "Invalid room ID"}), 400
    except DuplicateKeyError:
        return jsonify({"message": "A room with this name already exists"}), 409
    except Exception as e:
        app.logger.error(f"Error updating room: {str(e)}")
        return jsonify({"message": "An error occurred while updating the room"}), 500


@app.route("/api/rooms/<room_id>", methods=["DELETE"])
def delete_room(room_id):
    try:
        room = rooms_collection.find_one({"_id": ObjectId(room_id)})
        if not room:
            return jsonify({"message": "Room not found"}), 404

        # Delete associated schedule entries
        schedule_entries_collection.delete_many({"room_id": room_id})

        # Delete room
        rooms_collection.delete_one({"_id": ObjectId(room_id)})

        return jsonify({"message": "Room deleted successfully"})
    except InvalidId:
        return jsonify({"message": "Invalid room ID"}), 400
    except Exception as e:
        app.logger.error(f"Error deleting room: {str(e)}")
        return jsonify({"message": "An error occurred while deleting the room"}), 500


# API Route for Timetable Generation
@app.route("/api/generate-timetable", methods=["POST"])
def generate_timetable():
    try:
        # 1. Clear existing schedule
        schedule_entries_collection.delete_many({})

        # 2. Fetch all entities
        teachers = list(teachers_collection.find())
        courses = list(courses_collection.find())
        rooms = list(rooms_collection.find())
        time_slots = list(time_slots_collection.find())

        if not teachers or not courses or not rooms or not time_slots:
            return jsonify({
                "message": "Not enough data to generate timetable. Ensure teachers, courses, rooms, and time slots are populated."
            }), 400

        # 3. Initialize availability tracking
        teacher_occupied_slots = set()  # (teacher_id, time_slot_id)
        room_occupied_slots = set()     # (room_id, time_slot_id)

        generated_schedule = []
        unassigned_courses = []

        # 4. Iterate through courses and try to assign
        for course in courses:
            assigned = False
            course_id = str(course["_id"])

            for time_slot in time_slots:
                time_slot_id = str(time_slot["_id"])

                for room in rooms:
                    room_id = str(room["_id"])

                    for teacher in teachers:
                        teacher_id = str(teacher["_id"])

                        # Check for conflicts
                        teacher_conflict = (teacher_id, time_slot_id) in teacher_occupied_slots
                        room_conflict = (room_id, time_slot_id) in room_occupied_slots

                        if not teacher_conflict and not room_conflict:
                            # Assign the course
                            new_entry = {
                                "teacher_id": teacher_id,
                                "course_id": course_id,
                                "room_id": room_id,
                                "time_slot_id": time_slot_id
                            }
                            result = schedule_entries_collection.insert_one(new_entry)
                            new_entry["id"] = str(result.inserted_id)

                            # Mark as occupied
                            teacher_occupied_slots.add((teacher_id, time_slot_id))
                            room_occupied_slots.add((room_id, time_slot_id))

                            generated_schedule.append(new_entry)
                            assigned = True
                            break  # Break from teacher loop
                    if assigned:
                        break  # Break from room loop
                if assigned:
                    break  # Break from time_slot loop

            if not assigned:
                unassigned_courses.append(course["name"])

        if unassigned_courses:
            return jsonify({
                "message": "Timetable generated with some unassigned courses.",
                "unassigned_courses": unassigned_courses,
                "generated_entries_count": len(generated_schedule)
            }), 200
        else:
            return jsonify({
                "message": "Timetable generated successfully.",
                "generated_entries_count": len(generated_schedule)
            }), 200

    except Exception as e:
        app.logger.error(f"Error generating timetable: {str(e)}")
        return jsonify({"message": "An error occurred while generating the timetable"}), 500


# API Route for retrieving the complete timetable
@app.route("/api/timetable", methods=["GET"])
def get_full_timetable():
    try:
        schedule_entries = list(schedule_entries_collection.find())
        result = []

        for entry in schedule_entries:
            teacher = teachers_collection.find_one({"_id": ObjectId(entry["teacher_id"])})
            course = courses_collection.find_one({"_id": ObjectId(entry["course_id"])})
            room = rooms_collection.find_one({"_id": ObjectId(entry["room_id"])})
            time_slot = time_slots_collection.find_one({"_id": ObjectId(entry["time_slot_id"])})

            result.append({
                "id": str(entry["_id"]),
                "teacher": {
                    "id": str(teacher["_id"]),
                    "name": teacher["name"]
                } if teacher else None,
                "course": {
                    "id": str(course["_id"]),
                    "name": course["name"],
                    "code": course["code"]
                } if course else None,
                "room": {
                    "id": str(room["_id"]),
                    "name": room["name"]
                } if room else None,
                "time_slot": {
                    "id": str(time_slot["_id"]),
                    "day_of_week": time_slot["day_of_week"],
                    "start_time": time_slot["start_time"],
                    "end_time": time_slot["end_time"]
                } if time_slot else None,
            })

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching timetable: {str(e)}")
        return jsonify({"message": "An error occurred while fetching the timetable"}), 500


# API Route for retrieving a specific teacher's timetable
@app.route("/api/teachers/<teacher_id>/timetable", methods=["GET"])
def get_teacher_timetable(teacher_id):
    try:
        teacher = teachers_collection.find_one({"_id": ObjectId(teacher_id)})
        if not teacher:
            return jsonify({"message": "Teacher not found"}), 404

        schedule_entries = list(schedule_entries_collection.find({"teacher_id": teacher_id}))
        result = []

        for entry in schedule_entries:
            course = courses_collection.find_one({"_id": ObjectId(entry["course_id"])})
            room = rooms_collection.find_one({"_id": ObjectId(entry["room_id"])})
            time_slot = time_slots_collection.find_one({"_id": ObjectId(entry["time_slot_id"])})

            result.append({
                "id": str(entry["_id"]),
                "course": {
                    "id": str(course["_id"]),
                    "name": course["name"],
                    "code": course["code"]
                } if course else None,
                "room": {
                    "id": str(room["_id"]),
                    "name": room["name"]
                } if room else None,
                "time_slot": {
                    "id": str(time_slot["_id"]),
                    "day_of_week": time_slot["day_of_week"],
                    "start_time": time_slot["start_time"],
                    "end_time": time_slot["end_time"]
                } if time_slot else None,
            })

        return jsonify({
            "teacher_id": str(teacher["_id"]),
            "teacher_name": teacher["name"],
            "timetable": result
        })
    except InvalidId:
        return jsonify({"message": "Invalid teacher ID"}), 400
    except Exception as e:
        app.logger.error(f"Error fetching teacher timetable: {str(e)}")
        return jsonify({"message": "An error occurred while fetching the teacher's timetable"}), 500


# Route for the Dashboard (main page)
@app.route("/")
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


@app.before_request
def before_request():
    if get_db() is None:
        return jsonify({"message": "Database not available"}), 503

if __name__ == "__main__":
    try:
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(debug=debug, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"An error occurred while running the app: {e}")

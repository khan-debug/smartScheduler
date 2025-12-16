from flask import Flask, render_template, request, jsonify
from sqlalchemy.orm import Session
from database import SessionLocal, Teacher, Course, Room, TimeSlot, ScheduleEntry, create_db_tables


app = Flask(__name__)

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Routes for Teachers
@app.route("/api/teachers", methods=["POST"])
def create_teacher():
    db = next(get_db())
    teacher_data = request.json
    new_teacher = Teacher(name=teacher_data["name"], email=teacher_data["email"])
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    return jsonify({"message": "Teacher created successfully", "teacher": {"id": new_teacher.id, "name": new_teacher.name, "email": new_teacher.email}}), 201

@app.route("/api/teachers", methods=["GET"])
def get_teachers():
    db = next(get_db())
    teachers = db.query(Teacher).all()
    return jsonify([{"id": t.id, "name": t.name, "email": t.email} for t in teachers])

@app.route("/api/teachers/<int:teacher_id>", methods=["GET"])
def get_teacher(teacher_id):
    db = next(get_db())
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        return jsonify({"message": "Teacher not found"}), 404
    return jsonify({"id": teacher.id, "name": teacher.name, "email": teacher.email})

@app.route("/api/teachers/<int:teacher_id>", methods=["PUT"])
def update_teacher(teacher_id):
    db = next(get_db())
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        return jsonify({"message": "Teacher not found"}), 404
    teacher_data = request.json
    teacher.name = teacher_data["name"]
    teacher.email = teacher_data["email"]
    db.commit()
    db.refresh(teacher)
    return jsonify({"message": "Teacher updated successfully", "teacher": {"id": teacher.id, "name": teacher.name, "email": teacher.email}})

@app.route("/api/teachers/<int:teacher_id>", methods=["DELETE"])
def delete_teacher(teacher_id):
    db = next(get_db())
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        return jsonify({"message": "Teacher not found"}), 404
    db.delete(teacher)
    db.commit()
    return jsonify({"message": "Teacher deleted successfully"})

# API Routes for Courses
@app.route("/api/courses", methods=["POST"])
def create_course():
    db = next(get_db())
    course_data = request.json
    new_course = Course(name=course_data["name"], code=course_data["code"], department=course_data["department"])
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return jsonify({"message": "Course created successfully", "course": {"id": new_course.id, "name": new_course.name, "code": new_course.code, "department": new_course.department}}), 201

@app.route("/api/courses", methods=["GET"])
def get_courses():
    db = next(get_db())
    courses = db.query(Course).all()
    return jsonify([{"id": c.id, "name": c.name, "code": c.code, "department": c.department} for c in courses])

@app.route("/api/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    db = next(get_db())
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return jsonify({"message": "Course not found"}), 404
    return jsonify({"id": course.id, "name": course.name, "code": course.code, "department": course.department})

@app.route("/api/courses/<int:course_id>", methods=["PUT"])
def update_course(course_id):
    db = next(get_db())
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return jsonify({"message": "Course not found"}), 404
    course_data = request.json
    course.name = course_data["name"]
    course.code = course_data["code"]
    course.department = course_data["department"]
    db.commit()
    db.refresh(course)
    return jsonify({"message": "Course updated successfully", "course": {"id": course.id, "name": course.name, "code": course.code, "department": course.department}})

@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
def delete_course(course_id):
    db = next(get_db())
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return jsonify({"message": "Course not found"}), 404
    db.delete(course)
    db.commit()
    return jsonify({"message": "Course deleted successfully"})

# API Routes for Rooms
@app.route("/api/rooms", methods=["POST"])
def create_room():
    db = next(get_db())
    room_data = request.json
    new_room = Room(name=room_data["name"], capacity=room_data["capacity"], room_type=room_data["room_type"])
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return jsonify({"message": "Room created successfully", "room": {"id": new_room.id, "name": new_room.name, "capacity": new_room.capacity, "room_type": new_room.room_type}}), 201

@app.route("/api/rooms", methods=["GET"])
def get_rooms():
    db = next(get_db())
    rooms = db.query(Room).all()
    return jsonify([{"id": r.id, "name": r.name, "capacity": r.capacity, "room_type": r.room_type} for r in rooms])

@app.route("/api/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id):
    db = next(get_db())
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return jsonify({"message": "Room not found"}), 404
    return jsonify({"id": room.id, "name": room.name, "capacity": room.capacity, "room_type": room.room_type})

@app.route("/api/rooms/<int:room_id>", methods=["PUT"])
def update_room(room_id):
    db = next(get_db())
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return jsonify({"message": "Room not found"}), 404
    room_data = request.json
    room.name = room_data["name"]
    room.capacity = room_data["capacity"]
    room.room_type = room_data["room_type"]
    db.commit()
    db.refresh(room)
    return jsonify({"message": "Room updated successfully", "room": {"id": room.id, "name": room.name, "capacity": room.capacity, "room_type": room.room_type}})

@app.route("/api/rooms/<int:room_id>", methods=["DELETE"])
def delete_room(room_id):
    db = next(get_db())
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return jsonify({"message": "Room not found"}), 404
    db.delete(room)
    db.commit()
    return jsonify({"message": "Room deleted successfully"})



# API Route for Timetable Generation
@app.route("/api/generate-timetable", methods=["POST"])
def generate_timetable():
    db = next(get_db())
    
    # 1. Clear existing schedule
    db.query(ScheduleEntry).delete()
    db.commit()

    # 2. Fetch all entities
    teachers = db.query(Teacher).all()
    courses = db.query(Course).all()
    rooms = db.query(Room).all()
    time_slots = db.query(TimeSlot).all()

    if not teachers or not courses or not rooms or not time_slots:
        return jsonify({"message": "Not enough data to generate timetable. Ensure teachers, courses, rooms, and time slots are populated."}), 400

    # 3. Initialize availability tracking
    teacher_occupied_slots = set() # (teacher_id, time_slot_id)
    room_occupied_slots = set()    # (room_id, time_slot_id)
    
    generated_schedule = []
    unassigned_courses = []

    # 4. Iterate through courses and try to assign
    for course in courses:
        assigned = False
        for time_slot in time_slots:
            for room in rooms:
                for teacher in teachers:
                    # Check for conflicts
                    teacher_conflict = (teacher.id, time_slot.id) in teacher_occupied_slots
                    room_conflict = (room.id, time_slot.id) in room_occupied_slots

                    if not teacher_conflict and not room_conflict:
                        # Assign the course
                        new_entry = ScheduleEntry(
                            teacher_id=teacher.id,
                            course_id=course.id,
                            room_id=room.id,
                            time_slot_id=time_slot.id
                        )
                        db.add(new_entry)
                        
                        # Mark as occupied
                        teacher_occupied_slots.add((teacher.id, time_slot.id))
                        room_occupied_slots.add((room.id, time_slot.id))
                        
                        generated_schedule.append(new_entry)
                        assigned = True
                        break # Break from teacher loop, assigned this course
                if assigned:
                    break # Break from room loop
            if assigned:
                break # Break from time_slot loop
        
        if not assigned:
            unassigned_courses.append(course.name)

    db.commit()

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


# API Route for retrieving the complete timetable
@app.route("/api/timetable", methods=["GET"])
def get_full_timetable():
    db = next(get_db())
    schedule_entries = db.query(ScheduleEntry).all()
    result = []
    for entry in schedule_entries:
        teacher = db.query(Teacher).filter(Teacher.id == entry.teacher_id).first()
        course = db.query(Course).filter(Course.id == entry.course_id).first()
        room = db.query(Room).filter(Room.id == entry.room_id).first()
        time_slot = db.query(TimeSlot).filter(TimeSlot.id == entry.time_slot_id).first()

        result.append({
            "id": entry.id,
            "teacher": {"id": teacher.id, "name": teacher.name} if teacher else None,
            "course": {"id": course.id, "name": course.name, "code": course.code} if course else None,
            "room": {"id": room.id, "name": room.name} if room else None,
            "time_slot": {
                "id": time_slot.id,
                "day_of_week": time_slot.day_of_week,
                "start_time": str(time_slot.start_time),
                "end_time": str(time_slot.end_time),
            } if time_slot else None,
        })
    return jsonify(result)

# API Route for retrieving a specific teacher's timetable
@app.route("/api/teachers/<int:teacher_id>/timetable", methods=["GET"])
def get_teacher_timetable(teacher_id):
    db = next(get_db())
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        return jsonify({"message": "Teacher not found"}), 404

    schedule_entries = db.query(ScheduleEntry).filter(ScheduleEntry.teacher_id == teacher_id).all()
    result = []
    for entry in schedule_entries:
        course = db.query(Course).filter(Course.id == entry.course_id).first()
        room = db.query(Room).filter(Room.id == entry.room_id).first()
        time_slot = db.query(TimeSlot).filter(TimeSlot.id == entry.time_slot_id).first()

        result.append({
            "id": entry.id,
            "course": {"id": course.id, "name": course.name, "code": course.code} if course else None,
            "room": {"id": room.id, "name": room.name} if room else None,
            "time_slot": {
                "id": time_slot.id,
                "day_of_week": time_slot.day_of_week,
                "start_time": str(time_slot.start_time),
                "end_time": str(time_slot.end_time),
            } if time_slot else None,
        })
    return jsonify({"teacher_id": teacher.id, "teacher_name": teacher.name, "timetable": result})


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

if __name__ == "__main__":
    create_db_tables()
    app.run(debug=True, port=5000)

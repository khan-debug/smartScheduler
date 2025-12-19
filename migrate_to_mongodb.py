"""
Migration script to migrate data from SQLite to MongoDB

This script will:
1. Read data from the existing SQLite database
2. Migrate all teachers, courses, rooms, time slots, and schedule entries to MongoDB
3. Preserve all existing data

Usage:
    python migrate_to_mongodb.py
"""

import sqlite3
from database import (
    teachers_collection,
    courses_collection,
    rooms_collection,
    time_slots_collection,
    schedule_entries_collection,
    create_indexes
)

def migrate_sqlite_to_mongodb():
    # Connect to SQLite database
    try:
        conn = sqlite3.connect('smart_scheduler.db')
        cursor = conn.cursor()
        print("Connected to SQLite database")
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite: {e}")
        return

    # Create MongoDB indexes
    print("Creating MongoDB indexes...")
    create_indexes()

    # Migrate Teachers
    print("\nMigrating teachers...")
    cursor.execute("SELECT id, name, email FROM teachers")
    teachers = cursor.fetchall()
    teacher_id_map = {}  # SQLite ID -> MongoDB ID mapping

    for sqlite_id, name, email in teachers:
        teacher_doc = {
            "name": name,
            "email": email.lower() if email else ""
        }
        try:
            result = teachers_collection.insert_one(teacher_doc)
            teacher_id_map[sqlite_id] = str(result.inserted_id)
            print(f"  ✓ Migrated teacher: {name}")
        except Exception as e:
            print(f"  ✗ Error migrating teacher {name}: {e}")

    # Migrate Courses
    print("\nMigrating courses...")
    cursor.execute("SELECT id, name, code, department FROM courses")
    courses = cursor.fetchall()
    course_id_map = {}  # SQLite ID -> MongoDB ID mapping

    for sqlite_id, name, code, department in courses:
        course_doc = {
            "name": name,
            "code": code.upper() if code else "",
            "department": department or ""
        }
        try:
            result = courses_collection.insert_one(course_doc)
            course_id_map[sqlite_id] = str(result.inserted_id)
            print(f"  ✓ Migrated course: {name} ({code})")
        except Exception as e:
            print(f"  ✗ Error migrating course {name}: {e}")

    # Migrate Rooms
    print("\nMigrating rooms...")
    cursor.execute("SELECT id, name, capacity, room_type FROM rooms")
    rooms = cursor.fetchall()
    room_id_map = {}  # SQLite ID -> MongoDB ID mapping

    for sqlite_id, name, capacity, room_type in rooms:
        room_doc = {
            "name": name,
            "capacity": capacity or 0,
            "room_type": room_type.lower() if room_type else "lecture"
        }
        try:
            result = rooms_collection.insert_one(room_doc)
            room_id_map[sqlite_id] = str(result.inserted_id)
            print(f"  ✓ Migrated room: {name}")
        except Exception as e:
            print(f"  ✗ Error migrating room {name}: {e}")

    # Migrate Time Slots
    print("\nMigrating time slots...")
    cursor.execute("SELECT id, day_of_week, start_time, end_time FROM time_slots")
    time_slots = cursor.fetchall()
    time_slot_id_map = {}  # SQLite ID -> MongoDB ID mapping

    for sqlite_id, day_of_week, start_time, end_time in time_slots:
        time_slot_doc = {
            "day_of_week": day_of_week,
            "start_time": start_time,
            "end_time": end_time
        }
        try:
            result = time_slots_collection.insert_one(time_slot_doc)
            time_slot_id_map[sqlite_id] = str(result.inserted_id)
            print(f"  ✓ Migrated time slot: {day_of_week} {start_time}-{end_time}")
        except Exception as e:
            print(f"  ✗ Error migrating time slot {day_of_week}: {e}")

    # Migrate Schedule Entries
    print("\nMigrating schedule entries...")
    cursor.execute("""
        SELECT id, teacher_id, course_id, room_id, time_slot_id
        FROM schedule_entries
    """)
    schedule_entries = cursor.fetchall()

    for sqlite_id, teacher_id, course_id, room_id, time_slot_id in schedule_entries:
        # Map SQLite IDs to MongoDB IDs
        mongo_teacher_id = teacher_id_map.get(teacher_id)
        mongo_course_id = course_id_map.get(course_id)
        mongo_room_id = room_id_map.get(room_id)
        mongo_time_slot_id = time_slot_id_map.get(time_slot_id)

        if all([mongo_teacher_id, mongo_course_id, mongo_room_id, mongo_time_slot_id]):
            entry_doc = {
                "teacher_id": mongo_teacher_id,
                "course_id": mongo_course_id,
                "room_id": mongo_room_id,
                "time_slot_id": mongo_time_slot_id
            }
            try:
                schedule_entries_collection.insert_one(entry_doc)
                print(f"  ✓ Migrated schedule entry #{sqlite_id}")
            except Exception as e:
                print(f"  ✗ Error migrating schedule entry #{sqlite_id}: {e}")
        else:
            print(f"  ✗ Skipped schedule entry #{sqlite_id} due to missing references")

    # Close SQLite connection
    conn.close()

    # Print summary
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Teachers migrated:        {teachers_collection.count_documents({})}")
    print(f"Courses migrated:         {courses_collection.count_documents({})}")
    print(f"Rooms migrated:           {rooms_collection.count_documents({})}")
    print(f"Time slots migrated:      {time_slots_collection.count_documents({})}")
    print(f"Schedule entries migrated: {schedule_entries_collection.count_documents({})}")
    print("="*60)
    print("\n✓ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Verify the data in MongoDB")
    print("2. Test the application with MongoDB")
    print("3. Once verified, you can rename or backup the SQLite database")
    print("4. Update your .env file if needed")


if __name__ == "__main__":
    print("SQLite to MongoDB Migration Tool")
    print("="*60)
    print("\nWARNING: This will migrate data from smart_scheduler.db to MongoDB")
    print("Make sure MongoDB is running before proceeding.")

    response = input("\nDo you want to continue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        # Clear existing MongoDB data
        clear_response = input("\nClear existing MongoDB data first? (yes/no): ")
        if clear_response.lower() in ['yes', 'y']:
            print("\nClearing existing MongoDB collections...")
            teachers_collection.delete_many({})
            courses_collection.delete_many({})
            rooms_collection.delete_many({})
            time_slots_collection.delete_many({})
            schedule_entries_collection.delete_many({})
            print("✓ Cleared all collections")

        migrate_sqlite_to_mongodb()
    else:
        print("\nMigration cancelled.")

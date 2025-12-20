from pymongo import MongoClient, ASCENDING
from bson import ObjectId
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "smart_scheduler")

# Create MongoDB client
client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
teachers_collection = db["teachers"]
courses_collection = db["courses"]
rooms_collection = db["rooms"]
time_slots_collection = db["time_slots"]
schedule_entries_collection = db["schedule_entries"]


def create_indexes():
    """Create indexes for better query performance"""
    try:
        # Check if the database is available
        client.admin.command('ping')

        # Teachers indexes
        teachers_collection.create_index([("name", ASCENDING)])
        teachers_collection.create_index([("email", ASCENDING)], unique=True)

        # Courses indexes
        courses_collection.create_index([("name", ASCENDING)])
        courses_collection.create_index([("code", ASCENDING)], unique=True)

        # Rooms indexes
        rooms_collection.create_index([("name", ASCENDING)], unique=True)

        # Time Slots indexes
        time_slots_collection.create_index([("day_of_week", ASCENDING)])
        time_slots_collection.create_index([("start_time", ASCENDING)])

        # Schedule Entries indexes
        schedule_entries_collection.create_index([("teacher_id", ASCENDING)])
        schedule_entries_collection.create_index([("course_id", ASCENDING)])
        schedule_entries_collection.create_index([("room_id", ASCENDING)])
        schedule_entries_collection.create_index([("time_slot_id", ASCENDING)])

        print("MongoDB indexes created successfully!")
    except Exception as e:
        print(f"Could not connect to MongoDB. Please ensure that the database is running and accessible. Error: {e}")


def get_db():
    """Returns the database instance"""
    try:
        # Check if the database is available
        client.admin.command('ping')
        return db
    except Exception:
        return None


# Helper functions for data serialization
def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, dict):
        doc = doc.copy()
        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
        return doc
    return doc


def serialize_docs(docs):
    """Convert list of MongoDB documents to JSON-serializable format"""
    return [serialize_doc(doc) for doc in docs]


if __name__ == "__main__":
    create_indexes()
    print("Database setup complete!")

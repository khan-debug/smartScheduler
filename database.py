from sqlalchemy import create_engine, Column, Integer, String, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

# SQLite database URL
DATABASE_URL = "sqlite:///./smart_scheduler.db"

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# Define database models
class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

    # Relationships
    schedule_entries = relationship("ScheduleEntry", back_populates="teacher")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True) # e.g., CS101, MATH203
    department = Column(String)

    # Relationships
    schedule_entries = relationship("ScheduleEntry", back_populates="course")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capacity = Column(Integer)
    room_type = Column(String) # e.g., 'lecture', 'lab', 'seminar'

    # Relationships
    schedule_entries = relationship("ScheduleEntry", back_populates="room")

class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(String, index=True) # e.g., 'Monday', 'Tuesday'
    start_time = Column(Time)
    end_time = Column(Time)

    # Relationships
    schedule_entries = relationship("ScheduleEntry", back_populates="time_slot")

class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"))

    # Relationships
    teacher = relationship("Teacher", back_populates="schedule_entries")
    course = relationship("Course", back_populates="schedule_entries")
    room = relationship("Room", back_populates="schedule_entries")
    time_slot = relationship("TimeSlot", back_populates="schedule_entries")

# Function to create all tables
def create_db_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_db_tables()
    print("Database tables created successfully!")

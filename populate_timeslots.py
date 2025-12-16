from datetime import time
from database import SessionLocal, TimeSlot, create_db_tables

def populate_time_slots():
    db = SessionLocal()
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    start_hours = range(9, 17) # 9 AM to 4 PM (inclusive)

    for day in days_of_week:
        for hour in start_hours:
            start_time = time(hour=hour, minute=0)
            end_time = time(hour=hour + 1, minute=0)
            
            # Check if time slot already exists
            existing_slot = db.query(TimeSlot).filter_by(
                day_of_week=day,
                start_time=start_time,
                end_time=end_time
            ).first()

            if not existing_slot:
                time_slot = TimeSlot(
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time
                )
                db.add(time_slot)
                print(f"Added TimeSlot: {day} {start_time}-{end_time}")
            else:
                print(f"TimeSlot already exists: {day} {start_time}-{end_time}")
    
    db.commit()
    db.close()
    print("Time slots population complete.")

if __name__ == "__main__":
    # Ensure tables are created before populating time slots
    create_db_tables() 
    populate_time_slots()

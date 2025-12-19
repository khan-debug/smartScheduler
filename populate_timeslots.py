from database import time_slots_collection, create_indexes

def populate_time_slots():
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    start_hours = range(9, 17)  # 9 AM to 4 PM (inclusive)

    for day in days_of_week:
        for hour in start_hours:
            start_time = f"{hour:02d}:00"
            end_time = f"{hour + 1:02d}:00"

            # Check if time slot already exists
            existing_slot = time_slots_collection.find_one({
                "day_of_week": day,
                "start_time": start_time,
                "end_time": end_time
            })

            if not existing_slot:
                time_slot = {
                    "day_of_week": day,
                    "start_time": start_time,
                    "end_time": end_time
                }
                time_slots_collection.insert_one(time_slot)
                print(f"Added TimeSlot: {day} {start_time}-{end_time}")
            else:
                print(f"TimeSlot already exists: {day} {start_time}-{end_time}")

    print("Time slots population complete.")


if __name__ == "__main__":
    # Ensure indexes are created before populating time slots
    create_indexes()
    populate_time_slots()

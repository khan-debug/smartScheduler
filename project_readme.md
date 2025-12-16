# Project: Smart Scheduler

## 1. Project Overview

**Project Name:** Smart Scheduler

**Purpose:** A web application for educational institutions to automate the generation and management of academic timetables. The application is designed to be a "smart" scheduler that can handle various constraints and provide an intuitive user interface for managing schedules.

**Key Features:**
*   **Dashboard:** A landing page that provides an at-a-glance overview of the current state of the schedule, including key statistics like the number of scheduled classes, conflicts, room utilization, and faculty load balancing.
*   **Timetable Generation:** A dedicated page for generating new timetables. The generation can be triggered with a single click, and there is also a provision for uploading a `.csv` file for more complex scenarios.
*   **Teacher View:** A page where individual teachers can view their personalized schedules.
*   **Admin Panel:** A comprehensive management area for administrators to perform CRUD (Create, Read, Update, Delete) operations on core entities like Teachers, Courses, and Rooms.

## 2. Project Structure

The project is organized as follows:

*   `app.py`: The main Flask application file. It contains all the backend logic, including API endpoints and rendering of HTML templates.
*   `database.py`: Defines the database schema using SQLAlchemy ORM. It includes models for `Teacher`, `Course`, `Room`, `TimeSlot`, and `ScheduleEntry`.
*   `smart_scheduler.db`: The SQLite database file where all the data is stored.
*   `static/style.css`: The main stylesheet for the application. It provides a dark theme with blue accents.
*   `templates/`: This directory contains all the HTML templates.
    *   `base.html`: The base template that all other pages extend. It includes the sidebar navigation and the main content area structure.
    *   `dashboard.html`: The template for the dashboard page.
    *   `generate.html`: The template for the timetable generation page.
    *   `teacherView.html`: The template for the teacher view page.
    *   `adminPanel.html`: The template for the admin panel.

## 3. Backend Details

*   **Framework:** Flask
*   **Database:** SQLite (`smart_scheduler.db`)
*   **ORM:** SQLAlchemy

### Database Models (in `database.py`)

*   `Teacher`: `id`, `name`, `email`
*   `Course`: `id`, `name`, `code`, `department`
*   `Room`: `id`, `name`, `capacity`, `room_type`
*   `TimeSlot`: `id`, `day_of_week`, `start_time`, `end_time`
*   `ScheduleEntry`: `id`, `teacher_id`, `course_id`, `room_id`, `time_slot_id`

### API Endpoints (in `app.py`)

*   **Teachers:**
    *   `GET /api/teachers`: Get all teachers.
    *   `POST /api/teachers`: Create a new teacher.
    *   `GET /api/teachers/<id>`: Get a specific teacher.
    *   `PUT /api/teachers/<id>`: Update a teacher.
    *   `DELETE /api/teachers/<id>`: Delete a teacher.
*   **Courses:**
    *   `GET /api/courses`: Get all courses.
    *   `POST /api/courses`: Create a new course.
    *   `GET /api/courses/<id>`: Get a specific course.
    *   `PUT /api/courses/<id>`: Update a course.
    *   `DELETE /api/courses/<id>`: Delete a course.
*   **Rooms:**
    *   `GET /api/rooms`: Get all rooms.
    *   `POST /api/rooms`: Create a new room.
    *   `GET /api/rooms/<id>`: Get a specific room.
    *   `PUT /api/rooms/<id>`: Update a room.
    *   `DELETE /api/rooms/<id>`: Delete a room.
*   **Timetable:**
    *   `POST /api/generate-timetable`: Trigger the timetable generation process. It uses a greedy algorithm to create a new schedule.
    *   `GET /api/timetable`: Get the complete generated timetable.
    *   `GET /api/teachers/<id>/timetable`: Get the timetable for a specific teacher.

## 4. Frontend Details

*   **Templating:** Jinja2
*   **Styling:** A custom dark theme is defined in `static/style.css`.
*   **Dynamic Functionality:** JavaScript is embedded in the HTML templates to make them interactive.
    *   **`adminPanel.html`:** Uses JavaScript to create a tabbed interface for managing entities. It dynamically populates tables with data from the backend and uses a modal dialog for adding/editing entities.
    *   **`generate.html`:** The "Auto Generate" button triggers a JavaScript function that calls the `/api/generate-timetable` endpoint and then fetches and displays the generated timetable in a grid.
    *   **`dashboard.html`:** The statistics on this page are dynamically loaded by fetching data from the `/api/timetable`, `/api/teachers`, and `/api/rooms` endpoints.
    *   **`teacherView.html`:** This page fetches and displays a specific teacher's schedule based on the `id` parameter in the URL (e.g., `/teacher?id=1`).

## 5. Current Status

*   **The application is fully functional.**
*   The backend has been implemented with all the core features, including database setup, models, and APIs for CRUD operations and timetable generation.
*   The frontend has been fully integrated with the backend APIs. All the pages are now dynamic and display data from the database.
*   The UI has been fixed to match the original dark theme and layout, ensuring a consistent user experience.

## 6. How to Run the Application

1.  **Install Dependencies:**
    *   `pip install Flask SQLAlchemy`
2.  **Initialize the Database:**
    *   Run `python database.py` to create the database tables.
    *   Run `python populate_timeslots.py` to populate the `TimeSlot` table with default time slots.
3.  **Run the Application:**
    *   `python app.py`
4.  **Access in Browser:**
    *   `http://127.0.0.1:5000`

# Smart Scheduler

A web-based academic timetable management system for educational institutions that automates schedule generation and provides intuitive management interfaces.

## Quick Reference

**Start Everything:**
```bash
# 1. Start MongoDB container
podman start smartscheduler-mongodb

# 2. Activate conda environment
source ~/miniconda3/bin/activate smartscheduler

# 3. Navigate to project
cd ~/Dev/python/smartScheduler

# 4. Run application
python app.py
```

**Access Application:**
- Dashboard: http://127.0.0.1:5000/
- Admin Panel: http://127.0.0.1:5000/admin
- Generate Timetable: http://127.0.0.1:5000/generate

**Stop Everything:**
```bash
# Stop application (Ctrl+C in terminal)
# Or kill process: ps aux | grep "python app.py" | kill <PID>

# Stop MongoDB
podman stop smartscheduler-mongodb
```

---

## Table of Contents

- [Quick Reference](#quick-reference)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Quick Start Workflow](#quick-start-workflow) ⭐ **Start Here**
- [Managing the Application](#managing-the-application)
- [Installation (Alternative Methods)](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Security Improvements](#security-improvements)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Dashboard**: View statistics including total classes, conflicts, room utilization, and faculty load
- **Timetable Generation**: Automatically generate schedules with conflict detection
- **Teacher View**: Personalized schedule views for individual teachers
- **Admin Panel**: Full CRUD operations for teachers, courses, and rooms

## Technology Stack

- **Backend**: Flask 3.0 (Python web framework)
- **Database**: MongoDB (NoSQL database)
- **Frontend**: Vanilla JavaScript with custom CSS
- **UI**: Dark theme with responsive design

## Prerequisites

- Python 3.8 or higher (or Conda/Miniconda)
- MongoDB 4.4 or higher (or Podman/Docker)
- Internet connection for downloading dependencies

## Quick Start Workflow

This is the complete workflow to get the application running from scratch.

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     SETUP WORKFLOW                              │
└─────────────────────────────────────────────────────────────────┘

    1. Clone Repository
           ↓
    2. Create Conda Environment (smartscheduler)
           ↓
    3. Install Python Dependencies (Flask, PyMongo, etc.)
           ↓
    4. Start MongoDB Container (Podman)
           ↓
    5. Configure .env File (SECRET_KEY, MongoDB URL)
           ↓
    6. Initialize Database (populate_timeslots.py)
           ↓
    7. Run Application (python app.py)
           ↓
    8. Access in Browser (http://127.0.0.1:5000)
           ↓
    9. Add Data (Admin Panel)
           ↓
   10. Generate Timetable

┌─────────────────────────────────────────────────────────────────┐
│                     DAILY USAGE                                 │
└─────────────────────────────────────────────────────────────────┘

    podman start smartscheduler-mongodb
           ↓
    source ~/miniconda3/bin/activate smartscheduler
           ↓
    cd ~/Dev/python/smartScheduler
           ↓
    python app.py
           ↓
    Open http://127.0.0.1:5000 in browser
```

### Step 1: Clone the Repository

```bash
git clone https://github.com/khan-debug/smartScheduler.git
cd smartScheduler
```

### Step 2: Set Up Python Environment with Conda

**Check if Conda is installed:**
```bash
conda --version
# or
~/miniconda3/bin/conda --version
```

**Create a new Conda environment:**
```bash
# Using conda directly (if in PATH)
conda create -n smartscheduler python=3.11 -y

# Or using full path
~/miniconda3/bin/conda create -n smartscheduler python=3.11 -y
```

**Activate the environment:**
```bash
# Using conda directly
conda activate smartscheduler

# Or using source
source ~/miniconda3/bin/activate smartscheduler
```

### Step 3: Install Python Dependencies

```bash
# Make sure you're in the smartscheduler conda environment
pip install Flask==3.0.0 pymongo==4.6.1 python-dotenv==1.0.0

# Or install from requirements.txt
pip install -r requirements.txt
```

### Step 4: Set Up MongoDB with Podman

**Check if Podman is available:**
```bash
podman --version
```

**Start MongoDB container:**
```bash
podman run -d \
  --name smartscheduler-mongodb \
  -p 27017:27017 \
  docker.io/library/mongo:latest
```

**Verify MongoDB is running:**
```bash
podman ps
# Should show smartscheduler-mongodb container running on port 27017
```

### Step 5: Configure Environment Variables

**Copy the example .env file:**
```bash
cp .env.example .env
```

**Generate a secure secret key:**
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

**Edit `.env` file with your generated secret key:**
```env
FLASK_DEBUG=False
SECRET_KEY=your-generated-secret-key-here
PORT=5000
MONGODB_URL=mongodb://localhost:27017/
DATABASE_NAME=smart_scheduler
```

### Step 6: Initialize Database with Time Slots

```bash
# Make sure you're in the smartscheduler conda environment
python populate_timeslots.py
```

Expected output:
```
MongoDB indexes created successfully!
Added TimeSlot: Monday 09:00-10:00
Added TimeSlot: Monday 10:00-11:00
...
Time slots population complete.
```

### Step 7: Run the Application

```bash
python app.py
```

Expected output:
```
MongoDB indexes created successfully!
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

### Step 8: Access the Application

Open your browser and navigate to:
- **Local:** http://127.0.0.1:5000
- **Network:** http://192.168.x.x:5000 (check console output for exact IP)

### Step 9: Add Initial Data

1. Go to **Admin Panel**: http://127.0.0.1:5000/admin
2. Add at least one teacher:
   - Name: "Dr. John Smith"
   - Email: "john.smith@example.com"
3. Add at least one course:
   - Name: "Introduction to Computer Science"
   - Code: "CS101"
   - Department: "Computer Science"
4. Add at least one room:
   - Name: "Room A101"
   - Capacity: 30
   - Type: "lecture"

### Step 10: Generate Your First Timetable

1. Go to **Generate**: http://127.0.0.1:5000/generate
2. Click the "Generate Schedule" button
3. View the automatically generated timetable

---

## Managing the Application

### Stop the Application
```bash
# Press Ctrl+C in the terminal where app.py is running
# Or kill the process:
ps aux | grep "python app.py"
kill <process_id>
```

### Stop MongoDB Container
```bash
podman stop smartscheduler-mongodb
```

### Start MongoDB Container (after stopping)
```bash
podman start smartscheduler-mongodb
```

### Restart the Application
```bash
# Activate conda environment
source ~/miniconda3/bin/activate smartscheduler

# Navigate to project directory
cd ~/Dev/python/smartScheduler

# Run the app
python app.py
```

### Check MongoDB Container Status
```bash
podman ps -a | grep smartscheduler-mongodb
```

### View Application Logs
```bash
# If running in background, check the output file
tail -f /tmp/claude/-home-aarijkhan-Dev-python-smartScheduler/tasks/<task_id>.output
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/khan-debug/smartScheduler.git
cd smartScheduler
```

### 2. Create a virtual environment

```bash
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and Start MongoDB

**On Linux (Ubuntu/Debian):**
```bash
sudo apt-get install mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

**On Mac (using Homebrew):**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**On Windows:**
- Download MongoDB from [mongodb.com](https://www.mongodb.com/try/download/community)
- Follow the installation wizard
- Start MongoDB service from Services

**Using Docker:**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Using Podman (Fedora/RHEL):**
```bash
podman run -d \
  --name smartscheduler-mongodb \
  -p 27017:27017 \
  docker.io/library/mongo:latest
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and update the configuration:
```
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here
PORT=5000
MONGODB_URL=mongodb://localhost:27017/
DATABASE_NAME=smart_scheduler
```

**Generate a secure secret key:**
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

### 6. Initialize the database

Create indexes and populate time slots:

```bash
python populate_timeslots.py
```

This will:
- Create MongoDB indexes for better performance
- Populate 40 time slots (Monday-Friday, 9 AM - 5 PM)

### 7. Run the application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Initial Setup

1. Navigate to the **Admin Panel** (`/admin`)
2. Add teachers, courses, and rooms
3. Go to **Generate Timetable** (`/generate`)
4. Click "Generate Schedule" to create the timetable

### Managing Entities

**Teachers:**
- Name (required)
- Email (required, must be unique)

**Courses:**
- Name (required)
- Code (required, must be unique, e.g., CS101)
- Department (required)

**Rooms:**
- Name (required, must be unique)
- Capacity (required, 1-1000)
- Type (lecture, lab, or seminar)

### Viewing Schedules

- **Full Timetable**: Go to `/generate` to see the complete schedule
- **Teacher Schedule**: Go to `/teacher?id=<teacher_id>` to view a specific teacher's schedule
- **Dashboard**: Go to `/` to see statistics and metrics

## API Endpoints

### Teachers
- `GET /api/teachers` - List all teachers
- `POST /api/teachers` - Create a teacher
- `GET /api/teachers/<id>` - Get a teacher
- `PUT /api/teachers/<id>` - Update a teacher
- `DELETE /api/teachers/<id>` - Delete a teacher
- `GET /api/teachers/<id>/timetable` - Get teacher's schedule

### Courses
- `GET /api/courses` - List all courses
- `POST /api/courses` - Create a course
- `GET /api/courses/<id>` - Get a course
- `PUT /api/courses/<id>` - Update a course
- `DELETE /api/courses/<id>` - Delete a course

### Rooms
- `GET /api/rooms` - List all rooms
- `POST /api/rooms` - Create a room
- `GET /api/rooms/<id>` - Get a room
- `PUT /api/rooms/<id>` - Update a room
- `DELETE /api/rooms/<id>` - Delete a room

### Timetable
- `POST /api/generate-timetable` - Generate timetable
- `GET /api/timetable` - Get full timetable

## Project Structure

```
smartScheduler/
├── app.py                    # Main Flask application
├── database.py              # MongoDB connection and helpers
├── populate_timeslots.py    # Database seeding script
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── static/
│   └── style.css          # Stylesheet
└── templates/             # Jinja2 templates
    ├── base.html          # Base template
    ├── dashboard.html     # Dashboard
    ├── generate.html      # Timetable generation
    ├── teacherView.html   # Teacher schedule
    └── adminPanel.html    # Admin panel
```

## Security Improvements

The application now includes:

✅ **Fixed database session management** - No more memory leaks
✅ **Comprehensive error handling** - All endpoints handle exceptions gracefully
✅ **Input validation** - Server-side validation for all user inputs
✅ **Environment-based configuration** - Debug mode disabled by default
✅ **Duplicate prevention** - Unique constraints on emails and codes
✅ **Proper error messages** - Clear, user-friendly error responses

## Development

To run in development mode:

```bash
# Set debug mode in .env
FLASK_DEBUG=True

# Run the app
python app.py
```

## Production Deployment

1. Set `FLASK_DEBUG=False` in `.env`
2. Generate a strong `SECRET_KEY`
3. Use a production WSGI server (Gunicorn or uWSGI):

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

4. Set up a reverse proxy (Nginx or Apache)
5. Use a production MongoDB instance
6. Enable HTTPS/SSL

## Known Limitations

- Timetable generation uses a simple greedy algorithm
- No authentication or authorization system
- No CSRF protection
- Limited to 5-day weeks (Monday-Friday)
- Time slots are 1 hour each (9 AM - 5 PM)

## Future Improvements

- [ ] Add user authentication and authorization
- [ ] Implement CSRF protection
- [ ] Improve timetable algorithm (backtracking, optimization)
- [ ] Add CSV import/export functionality
- [ ] Implement responsive design for mobile
- [ ] Add audit logging
- [ ] Support custom time slots
- [ ] Add teacher preferences
- [ ] Implement conflict resolution
- [ ] Add email notifications

## Troubleshooting

**MongoDB Connection Error:**
```
pymongo.errors.ServerSelectionTimeoutError
```
- Ensure MongoDB is running: `sudo systemctl status mongodb`
- Or check Podman container: `podman ps | grep mongodb`
- Check MongoDB URL in `.env` file
- Verify MongoDB port (default: 27017)

**Podman MongoDB Container Not Starting:**
```bash
# Check container status
podman ps -a | grep smartscheduler-mongodb

# View container logs
podman logs smartscheduler-mongodb

# Remove and recreate container if needed
podman rm -f smartscheduler-mongodb
podman run -d --name smartscheduler-mongodb -p 27017:27017 docker.io/library/mongo:latest
```

**Conda Environment Issues:**
```bash
# List all conda environments
conda env list

# If environment doesn't exist, create it
conda create -n smartscheduler python=3.11 -y

# If activation fails, use full path
source ~/miniconda3/bin/activate smartscheduler

# Verify you're in the correct environment
which python
# Should show: /home/yourusername/miniconda3/envs/smartscheduler/bin/python
```

**Import Errors:**
```
ModuleNotFoundError: No module named 'flask'
```
- Activate conda environment: `source ~/miniconda3/bin/activate smartscheduler`
- Or virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Verify installation: `pip list | grep -i flask`

**Port Already in Use:**
```
OSError: [Errno 98] Address already in use
```
- Change port in `.env` file
- Or find and kill the process:
  ```bash
  # Find process using port 5000
  lsof -i :5000

  # Kill the process
  kill -9 <PID>

  # Or use one command
  lsof -t -i:5000 | xargs kill -9
  ```

**Podman Permission Denied:**
```
Error: permission denied
```
- Run podman as regular user (should work on Fedora by default)
- Or add user to podman group:
  ```bash
  sudo usermod -aG podman $USER
  newgrp podman
  ```

**Cannot Find Conda Command:**
```bash
# Add conda to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/miniconda3/bin:$PATH"

# Or initialize conda
~/miniconda3/bin/conda init bash  # or zsh
source ~/.bashrc  # or ~/.zshrc

# Or always use full path
~/miniconda3/bin/conda activate smartscheduler
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Author

Aarij Khan
- GitHub: [@khan-debug](https://github.com/khan-debug)

## Acknowledgments

- Flask web framework
- MongoDB database
- Font Awesome icons

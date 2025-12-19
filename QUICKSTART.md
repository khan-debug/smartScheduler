# Smart Scheduler - Quick Start Guide

## One-Page Setup & Run Instructions

### Initial Setup (Do Once)

```bash
# 1. Clone & Navigate
git clone https://github.com/khan-debug/smartScheduler.git
cd smartScheduler

# 2. Create Conda Environment
~/miniconda3/bin/conda create -n smartscheduler python=3.11 -y

# 3. Activate Environment
source ~/miniconda3/bin/activate smartscheduler

# 4. Install Dependencies
pip install Flask==3.0.0 pymongo==4.6.1 python-dotenv==1.0.0

# 5. Start MongoDB
podman run -d --name smartscheduler-mongodb -p 27017:27017 docker.io/library/mongo:latest

# 6. Setup Environment
cp .env.example .env
# Edit .env and add a secure SECRET_KEY (generate with: python -c 'import secrets; print(secrets.token_hex(32))')

# 7. Initialize Database
python populate_timeslots.py

# 8. Run Application
python app.py
```

---

### Daily Usage (Every Time)

```bash
# 1. Start MongoDB (if not running)
podman start smartscheduler-mongodb

# 2. Activate Environment
source ~/miniconda3/bin/activate smartscheduler

# 3. Navigate to Project
cd ~/Dev/python/smartScheduler

# 4. Run Application
python app.py
```

**Access:** http://127.0.0.1:5000

---

### Stop Everything

```bash
# Press Ctrl+C in the terminal running app.py
# Then stop MongoDB:
podman stop smartscheduler-mongodb
```

---

### First Time Using the App

1. **Add Data** → http://127.0.0.1:5000/admin
   - Add 1+ teachers (name, email)
   - Add 1+ courses (name, code, department)
   - Add 1+ rooms (name, capacity, type)

2. **Generate Timetable** → http://127.0.0.1:5000/generate
   - Click "Generate Schedule" button

3. **View Dashboard** → http://127.0.0.1:5000
   - See statistics and metrics

---

### Common Commands

**Check MongoDB Status:**
```bash
podman ps | grep smartscheduler-mongodb
```

**Check Application Status:**
```bash
ps aux | grep "python app.py"
```

**View Application Logs:**
```bash
tail -f /tmp/claude/-home-aarijkhan-Dev-python-smartScheduler/tasks/*.output
```

**Verify Conda Environment:**
```bash
which python
# Should show: /home/yourusername/miniconda3/envs/smartscheduler/bin/python
```

---

### Troubleshooting Quick Fixes

**Can't connect to MongoDB?**
```bash
podman ps | grep mongodb  # Check if running
podman start smartscheduler-mongodb  # Start if stopped
```

**Import errors?**
```bash
source ~/miniconda3/bin/activate smartscheduler  # Activate environment
pip install -r requirements.txt  # Reinstall dependencies
```

**Port 5000 already in use?**
```bash
lsof -t -i:5000 | xargs kill -9  # Kill process on port 5000
# Or change PORT in .env file
```

**Conda not found?**
```bash
~/miniconda3/bin/conda activate smartscheduler  # Use full path
```

---

### Key URLs

- **Dashboard:** http://127.0.0.1:5000/
- **Admin Panel:** http://127.0.0.1:5000/admin
- **Generate Timetable:** http://127.0.0.1:5000/generate
- **Teacher View:** http://127.0.0.1:5000/teacher

---

### API Endpoints

- `GET /api/teachers` - List all teachers
- `POST /api/teachers` - Create teacher
- `GET /api/courses` - List all courses
- `POST /api/courses` - Create course
- `GET /api/rooms` - List all rooms
- `POST /api/rooms` - Create room
- `POST /api/generate-timetable` - Generate timetable
- `GET /api/timetable` - Get full timetable
- `GET /api/teachers/<id>/timetable` - Get teacher's schedule

---

### Project Structure

```
smartScheduler/
├── app.py                  # Main application
├── database.py            # MongoDB connection
├── populate_timeslots.py  # Database seeder
├── requirements.txt       # Dependencies
├── .env                   # Configuration (DO NOT COMMIT)
├── .env.example          # Configuration template
├── static/style.css      # Stylesheet
└── templates/            # HTML templates
    ├── dashboard.html
    ├── adminPanel.html
    ├── generate.html
    └── teacherView.html
```

---

**For detailed documentation, see [README.md](README.md)**

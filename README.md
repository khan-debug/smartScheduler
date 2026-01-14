# SmartScheduler

A modern web-based timetable management system for educational institutions with automated scheduling using genetic algorithms.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.2-green)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen)

## Features

### Core Features
- **Automated Timetable Generation** - AI-powered scheduling with genetic algorithm optimization
- **Manual Scheduling** - Full control over class assignments
- **Smart Room Utilization** - Minimizes room usage per floor (95% efficiency)
- **Conflict Detection** - Prevents teacher and room conflicts automatically
- **Multi-Floor Management** - Organize rooms and classes across building floors

### Management
- **Faculty Management** - Add, edit, delete teachers with automatic email credentials
- **Course Management** - Auto credit hour assignment (3CH for Lectures, 1CH for Labs)
- **Room Management** - Bulk creation across floors with type enforcement
- **Import/Export** - Excel bulk import for faculty and courses

### User Experience
- **Modern UI** - Consistent design system with dark theme
- **Interactive Wizard** - Guided setup for first-time users
- **Role-Based Access** - Admin and teacher dashboards
- **Responsive Design** - Works on desktop and mobile

## Tech Stack

- **Backend**: Flask 3.1.2, Python 3.11+
- **Database**: MongoDB Atlas (cloud-hosted)
- **Frontend**: HTML5, CSS3 (Design System), JavaScript (ES6+)
- **Algorithm**: Genetic Algorithm for optimization
- **Email**: SMTP (automatic credential delivery)
- **Production**: Gunicorn WSGI server

## Quick Start

### Prerequisites
- Python 3.11 or higher
- MongoDB Atlas account (free tier available)
- Gmail account (for email notifications)

### Installation

1. **Clone and Install**
```bash
git clone <repository-url>
cd smartScheduler
pip install -r requirements.txt
```

2. **Configure MongoDB**
```bash
cp .env.example .env
```

Edit `.env`:
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=smartscheduler_db
FLASK_SECRET_KEY=<generate-random-key>
```

To generate a secure secret key:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

3. **Configure Email (Optional but Recommended)**
```bash
cp config/email_settings.txt.example config/email_settings.txt
```

Edit `config/email_settings.txt`:
```
your.email@gmail.com
your-app-password
```

**Get Gmail App Password:**
1. Enable 2FA on Gmail
2. Go to: Google Account → Security → 2-Step Verification → App passwords
3. Generate new app password for "Mail"

4. **Run Application**
```bash
# Development
python app.py

# Production
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

Access at: **http://localhost:5000**

### Default Credentials
- **Username**: `admin`
- **Password**: `0880`

**⚠️ Change immediately after first login via Admin Panel**

## MongoDB Atlas Setup

1. **Create Free Cluster**
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up and create a free M0 cluster (512MB, good for small institutions)
   - Choose region closest to your location

2. **Configure Access**
   - Database Access: Create user with read/write privileges
   - Network Access: Add your IP address (or 0.0.0.0/0 for any IP - less secure)

3. **Get Connection String**
   - Click "Connect" → "Connect your application"
   - Copy connection string and replace `<password>` with your database user password
   - Add to `.env` file

## Usage Guide

### Initial Setup
1. Login with default credentials
2. Click "Get Started" on dashboard
3. Follow the 4-step wizard:
   - **Step 1**: Add faculty members (or import via Excel)
   - **Step 2**: Create courses and assign teachers
   - **Step 3**: Setup rooms (defines lecture halls and labs)
   - **Step 4**: Generate timetable

### Generating Schedules

#### Option 1: Autogenerate (Recommended)
1. Go to "Generate Schedule" → Select floor
2. Choose "Autopick" (automatic) or "Manual Pick" (select specific courses)
3. System schedules optimally with:
   - No teacher conflicts
   - No room conflicts
   - Minimal room usage
   - 3CH courses → Lecture Halls
   - 1CH courses → Labs

#### Option 2: Manual Scheduling
1. Go to "Manual Edit"
2. Select floor and time slot
3. Choose course, teacher, and room
4. Save (system prevents conflicts)

### Managing Data

**Bulk Import:**
- Faculty: Upload Excel with columns: name, email, password
- Courses: Upload Excel with columns: course_name, course_type, shift, teacher_name, sections

**Individual Entry:**
- Use management pages for faculty, courses, and rooms
- Credit hours auto-assign based on course type

## Project Structure

```
smartScheduler/
├── app.py                      # Main application (Flask routes, genetic algorithm)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create from .env.example)
├── config/
│   └── email_settings.txt      # Email SMTP configuration
├── static/
│   └── css/
│       ├── design-system.css   # Design tokens and variables
│       ├── utilities.css       # Utility classes
│       └── components/         # Button, card, form styles
├── templates/
│   ├── layouts/
│   │   └── base.html          # Base template with navigation
│   ├── pages/                  # All page templates
│   ├── auth/                   # Login page
│   └── management/             # Management interfaces
└── README.md
```

## Key Features Explained

### Genetic Algorithm
- **Population**: 50 schedules per generation
- **Generations**: 100 iterations
- **Fitness Function**: Evaluates conflicts, room usage, day distribution
- **Optimization**: 95% room concentration in first available room
- **Constraints**: Hard constraints for room types and teacher availability

### Room Utilization
- Extreme penalty (500 points) for using extra rooms
- 95% probability of using first available room
- Results in minimal room usage per floor
- Balances between optimization and genetic diversity

### Conflict Prevention
- Real-time validation before saving
- Pre-populates existing schedules in genetic algorithm
- Prevents double-booking of teachers and rooms
- Enforces shift timing (morning/evening)

## Security Best Practices

**Before Production:**
- [ ] Change default admin password
- [ ] Generate strong FLASK_SECRET_KEY (32+ characters)
- [ ] Restrict MongoDB Network Access to specific IPs
- [ ] Enable HTTPS (use reverse proxy like nginx)
- [ ] Set up regular database backups
- [ ] Never commit `.env` to version control
- [ ] Review email settings permissions

**Add to `.gitignore`:**
```
.env
config/email_settings.txt
__pycache__/
*.pyc
```

## Troubleshooting

### MongoDB Connection Failed
- Verify connection string format
- Check username/password (use URL encoding for special characters)
- Confirm IP address is whitelisted in Network Access
- Test connection: `ping <cluster-hostname>`

### Email Not Sending
- Verify 2FA is enabled on Gmail
- Use app password, not account password
- Check firewall allows SMTP port 587
- Test with: `telnet smtp.gmail.com 587`

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000
# Kill process
kill -9 <PID>
# Or use different port
python app.py --port 5001
```

### Genetic Algorithm Not Finding Solution
- Reduce courses per floor
- Increase generation count in `app.py` (line ~160)
- Check if enough rooms available for course types
- Verify teacher availability for assigned courses

## Performance Optimization

- **Database**: Add indexes on frequently queried fields
- **Caching**: Consider Redis for session management
- **Workers**: Scale gunicorn workers based on CPU cores
- **CDN**: Host static assets on CDN for faster loading
- **Monitoring**: Use application monitoring (New Relic, Datadog)

## Deployment

### Railway (Recommended for Beginners)
1. Connect GitHub repository
2. Add environment variables in dashboard
3. Deploy automatically on push

### Render
1. Connect repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn app:app`
4. Add environment variables

### VPS (DigitalOcean, AWS, etc.)
```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip nginx

# Setup application
git clone <repo>
pip3 install -r requirements.txt

# Configure nginx reverse proxy
# Setup systemd service for auto-restart
# Configure SSL with Let's Encrypt
```

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - Free for educational and commercial use

## Support

For issues and questions:
- Check troubleshooting section above
- Review MongoDB connection string format
- Ensure all dependencies are installed
- Verify Python version is 3.11+

## Changelog

**Version 2.3** (Current)
- Improved room utilization (95% efficiency)
- Added manual pick for autogenerate mode
- Enhanced UI consistency with design system
- Removed Docker dependencies
- Added getting started wizard

---

**Built for educational institutions** | Automated scheduling made simple

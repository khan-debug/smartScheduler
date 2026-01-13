# SmartScheduler

A web-based timetable management system for educational institutions. Manage users, rooms, courses, and generate schedules efficiently.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.2-green)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen)

## Features

- **User Management** - Add, edit, and delete teachers with automatic email notifications
- **Room Management** - Bulk create rooms across multiple floors
- **Course Management** - Handle course information and credit hours
- **Admin Security** - Change admin password with OTP verification via email
- **Dashboard** - Real-time statistics and overview
- **Email Integration** - Automatic credential emails to new users
- **MongoDB Cloud Database** - Scalable cloud-based data storage
- **Responsive Design** - Clean and modern dark theme UI

## Tech Stack

- **Backend**: Flask 3.1.2
- **Database**: MongoDB Atlas (PyMongo 4.15.5)
- **Frontend**: HTML, CSS, JavaScript
- **Email**: SMTP (smtplib)
- **Server**: Gunicorn (production ready)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
```

Edit `.env` with your MongoDB credentials:
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=smartscheduler_db
FLASK_SECRET_KEY=your-secret-key-here
```

### 3. Configure Email (Optional)

```bash
# Copy and edit email config
cp config/email_settings.txt.example config/email_settings.txt
```

**Note**: Email is required for user management and admin password change features.

### 4. Run the Application

```bash
# Development
python app.py

# Production
gunicorn --bind 0.0.0.0:5000 app:app
```

Access at: **http://localhost:5000**

## Default Login

- **Username**: `admin`
- **Password**: `0880`

⚠️ Change the default password after first login using the Admin Panel.

## Project Structure

```
smartScheduler/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── config/               # Configuration files
│   └── email_settings.txt
├── static/               # CSS and JavaScript
└── templates/            # HTML templates
```

## MongoDB Setup

1. Create a free MongoDB Atlas account
2. Create a cluster and get connection string
3. Add your IP to Network Access whitelist
4. Update `MONGODB_URI` in `.env`

See `docs/CREATE_MONGODB_CLUSTER.md` for detailed instructions.

## Email Setup (Gmail)

1. Enable 2-Factor Authentication on Gmail
2. Generate App Password: Google Account → Security → App passwords
3. Add credentials to `config/email_settings.txt`

## Security Notes

⚠️ **Before deploying to production**:
- Change default admin password
- Use strong `FLASK_SECRET_KEY`
- Restrict MongoDB Network Access
- Enable HTTPS
- Never commit `.env` to git

## Documentation

- **Running the App**: `docs/RUN_APP.md`
- **MongoDB Setup**: `docs/CREATE_MONGODB_CLUSTER.md`
- **Troubleshooting**: `docs/MONGODB_SETUP_GUIDE.md`

## License

This project is for educational purposes.

---

**Built with ❤️ for educational institutions**

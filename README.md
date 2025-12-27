# SmartScheduler (prototype 2.4)

A web-based timetable management system for educational institutions. Manage users, rooms, courses, and generate schedules efficiently.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.2-green)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen)

---

## Features

- **User Management**: Add, edit, and delete teachers with automatic email notifications
- **Room Management**: Bulk create rooms across multiple floors with auto-fill gap prevention
- **Course Management**: Handle course information and credit hours
- **Admin Security**: Change admin password with OTP verification via email
- **Dashboard**: Real-time statistics and overview
- **Email Integration**: Automatic credential emails to new users
- **MongoDB Cloud Database**: Scalable cloud-based data storage
- **Responsive Design**: Clean and modern dark theme UI

---

## Project Structure

```
smartScheduler/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── config/                    # Configuration files
│   ├── email_settings.txt     # Email SMTP configuration (git-ignored)
│   ├── email_settings.txt.example  # Email config template
│   ├── admin_credentials.txt  # Custom admin password (optional, git-ignored)
│   └── admin_credentials.txt.example  # Admin credentials template
│
├── docs/                      # Documentation
│   ├── RUN_APP.md            # How to run the application
│   ├── CREATE_MONGODB_CLUSTER.md  # MongoDB setup guide
│   └── MONGODB_SETUP_GUIDE.md     # MongoDB troubleshooting
│
├── static/                    # Static assets
│   ├── css/                   # Stylesheets
│   │   ├── login.css
│   │   └── style.css
│   └── js/                    # JavaScript files
│       └── management.js
│
└── templates/                 # HTML templates
    ├── auth/                  # Authentication pages
    │   └── login.html
    ├── layouts/               # Base layouts
    │   └── base.html
    ├── management/            # CRUD management pages
    │   └── management.html
    ├── pages/                 # Main pages
    │   ├── adminPanel.html
    │   ├── dashboard.html
    │   ├── generate.html
    │   └── selectFloor.html
    └── timetables/            # Timetable views
        └── timetable_base.html
```

---

## Prerequisites

- **Python**: 3.11+ (use conda environment `sc`)
- **MongoDB Atlas**: Free tier account
- **Conda**: For environment management

---

## Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd smartScheduler
```

### 2. Set Up Conda Environment
```bash
conda activate sc
```

If you don't have the `sc` environment:
```bash
conda create -n sc python=3.11 -y
conda activate sc
conda install -c conda-forge 'openssl<3.4' -y
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your MongoDB credentials
nano .env
```

### 5. Configure Email Settings
```bash
# Copy example email config
cp config/email_settings.txt.example config/email_settings.txt

# Edit with your SMTP credentials (Gmail App Password recommended)
nano config/email_settings.txt
```

**Note**: Email is required for user management features (sending credentials to teachers) and admin password change via OTP.

### 6. Run the Application
```bash
python app.py
```

Access the application at: **http://127.0.0.1:5000**

---

## Default Login Credentials

### Admin Access
- **Username**: `admin`
- **Password**: `0880` (default)

⚠️ **Important**: Change the default password using the "Change Admin Password" button in the Admin Panel. This feature sends a 6-digit OTP to your email for verification.

### Teacher Access
- Teachers login using their **Registration Number** (not username)
- Created through the Admin Panel
- Receive credentials via email automatically

---

## MongoDB Configuration

This application uses **MongoDB Atlas** (cloud database).

### Current Setup
- **Database**: `smartscheduler_db`
- **Collections**: `users`, `rooms`, `courses`

### Setup New Cluster
See detailed instructions in: `docs/CREATE_MONGODB_CLUSTER.md`

**Important**: Make sure to:
1. Add your IP to Network Access in MongoDB Atlas
2. Use the connection string format: `mongodb+srv://...`
3. Update `MONGODB_URI` in `.env` or `app.py`

---

## Email Configuration

Email notifications are sent when users are created or updated.

### Setup
1. Use Gmail with App Password (recommended)
2. Copy `config/email_settings.txt.example` to `config/email_settings.txt`
3. Fill in your SMTP credentials

### How to Get Gmail App Password
1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account → Security → 2-Step Verification → App passwords
3. Create a new app password for "Mail"
4. Use this 16-character password in `email_settings.txt`

### Email Settings Structure
```json
"EmailSettings": {
    "Enabled": true,
    "FromEmail": "your-email@gmail.com",
    "EmailName": "SmartScheduler",
    "Subject": "Account Created - SmartScheduler",
    "Smtp": {
        "Server": "smtp.gmail.com",
        "Port": 587,
        "Username": "your-email@gmail.com",
        "Password": "your-app-password"
    }
}
```

**Note**: The `FromEmail` is also used as the admin email for receiving OTP when changing admin password.

---

## Development

### Technologies Used
- **Backend**: Flask 3.1.2
- **Database**: MongoDB Atlas (PyMongo 4.15.5)
- **Frontend**: HTML, CSS, JavaScript
- **Email**: SMTP (smtplib)

### Environment Requirements
- Python 3.11+ with OpenSSL 3.3.5 (for MongoDB compatibility)
- Conda environment: `sc`

---

## Troubleshooting

### MongoDB Connection Issues
See: `docs/MONGODB_SETUP_GUIDE.md`

Common fixes:
- Check IP whitelist in MongoDB Atlas Network Access
- Verify connection string is correct
- Ensure using the `sc` conda environment

### Email Not Sending
- Verify `config/email_settings.txt` exists and is configured
- Use Gmail App Password, not regular password
- Check SMTP server and port settings

### Application Won't Start
```bash
# Ensure you're in the correct environment
conda activate sc

# Check if all dependencies are installed
pip install -r requirements.txt

# Verify MongoDB connection
python -c "from pymongo import MongoClient; client = MongoClient('your-connection-string'); client.admin.command('ping'); print('✓ MongoDB OK')"
```

---

## Documentation

- **Running the App**: `docs/RUN_APP.md`
- **MongoDB Setup**: `docs/CREATE_MONGODB_CLUSTER.md`
- **Troubleshooting**: `docs/MONGODB_SETUP_GUIDE.md`

---

## Security Notes

⚠️ **Before Production Deployment**:
1. Change default admin password using "Change Admin Password" in Admin Panel
2. Use environment variables for sensitive data
3. Enable HTTPS
4. Restrict MongoDB Network Access (remove 0.0.0.0/0)
5. Use production WSGI server (not Flask dev server)
6. Never commit sensitive files to git:
   - `config/email_settings.txt`
   - `config/admin_credentials.txt`
   - `.env`

⚠️ **Files Included in Repository** (for open source):
- `config/email_settings.txt.example` - Template for email configuration
- `config/admin_credentials.txt.example` - Template for custom admin password (optional)
- `.env.example` - Template for environment variables

**Setup Instructions**: Copy the `.example` files and remove the `.example` extension, then fill in your actual credentials.

---

## License

This project is for educational purposes.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## Support

For issues and questions, please check the documentation in the `docs/` folder.

---

**Built with ❤️ for educational institutions**

# How to Run Your SmartScheduler Application

## ✅ Setup Complete!
Your application is now successfully connected to MongoDB Atlas!

## Running the Application

### 1. Activate the conda environment
```bash
conda activate sc
```

### 2. Start the Flask application
```bash
python app.py
```

### 3. Access the application
Open your browser and go to:
```
http://127.0.0.1:5000
```

### 4. Login
- **Admin Login:**
  - Username: `admin`
  - Password: `0880`

## What's Working Now

✅ MongoDB Atlas connection
✅ User management (with email notifications)
✅ Room management
✅ Course management
✅ Dashboard with statistics
✅ Admin panel
✅ Teacher view

## Your MongoDB Setup

- **Database:** smartscheduler_db
- **Collections:** users, rooms, courses
- **Cluster:** smartscheduler.tqtyuhp.mongodb.net
- **Environment:** sc (conda environment with Python 3.11 + OpenSSL 3.3.5)

## Important Notes

⚠️ **Always use the `sc` conda environment** when running this app
```bash
conda activate sc
python app.py
```

⚠️ **Email functionality** requires EmailSettings Enabled.txt to be configured

⚠️ **For production deployment:**
- Change the admin password from default "0880"
- Use environment variables for MongoDB connection string
- Use a production WSGI server (not Flask development server)
- Restrict MongoDB Network Access (remove 0.0.0.0/0 if used)

## Troubleshooting

If the app won't start:
```bash
# Make sure you're in the right environment
conda activate sc

# Check if MongoDB is accessible
python -c "from pymongo import MongoClient; client = MongoClient('mongodb+srv://aarij:aarij0990@smartscheduler.tqtyuhp.mongodb.net/'); client.admin.command('ping'); print('✓ MongoDB OK')"

# Check if all packages are installed
pip list | grep -E 'Flask|pymongo|certifi'
```

## Next Steps

1. Add some test users in the admin panel
2. Add rooms and courses
3. Test the timetable generation features
4. Customize the application for your needs

---
**Enjoy your fully functional SmartScheduler application! 🚀**

# PythonAnywhere Manual Configuration Guide

This guide provides step-by-step instructions for deploying SmartScheduler to PythonAnywhere using manual configuration.

**Your PythonAnywhere Username:** `Aarijkhan`
**Your App URL:** `https://Aarijkhan.pythonanywhere.com`

## Step 1: Create PythonAnywhere Account

1. Go to [www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Click "Pricing & signup"
3. Choose "Create a Beginner account" (Free)
4. Complete the registration with username: `Aarijkhan`

## Step 2: Upload Your Code

### Option A: Using Git (Recommended)

1. Open a **Bash console** from your PythonAnywhere dashboard
2. Clone your repository:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/smartScheduler.git
   cd smartScheduler
   ```

### Option B: Upload Files Manually

1. Go to **Files** tab
2. Create a new directory: `smartScheduler`
3. Upload all your project files

## Step 3: Create Virtual Environment

1. In the Bash console, navigate to your project:
   ```bash
   cd ~/smartScheduler
   ```

2. Create a virtual environment:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 smartscheduler-venv
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Step 4: Configure Web App

1. Go to the **Web** tab in PythonAnywhere dashboard
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"** (not Flask wizard)
4. Select **Python 3.10**
5. Click **Next**

## Step 5: Configure Virtual Environment

1. In the **Web** tab, find the **"Virtualenv"** section
2. Enter the path to your virtual environment:
   ```
   /home/Aarijkhan/.virtualenvs/smartscheduler-venv
   ```

## Step 6: Configure WSGI File

1. In the **Web** tab, find the **"Code"** section
2. Click on the **WSGI configuration file** link (e.g., `/var/www/Aarijkhan_pythonanywhere_com_wsgi.py`)
3. **Delete all the existing content** in the file
4. Copy and paste the following code:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/Aarijkhan/smartScheduler'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Flask app
from app import app as application
```

5. Click **Save**

## Step 7: Configure Static Files (Optional but Recommended)

1. In the **Web** tab, scroll to the **"Static files"** section
2. Add the following mapping:

   | URL           | Directory                                    |
   |---------------|----------------------------------------------|
   | /static/      | /home/Aarijkhan/smartScheduler/static        |

## Step 8: Reload Your Web App

1. Scroll to the top of the **Web** tab
2. Click the green **"Reload"** button
3. Wait a few seconds for the reload to complete

## Step 9: Test Your Application

1. Your app will be available at:
   ```
   https://Aarijkhan.pythonanywhere.com
   ```

2. Click the link in the Web tab to open your application

## Troubleshooting

### Error: "Something went wrong :("

1. Check the **Error log** and **Server log** in the Web tab
2. Common issues:
   - WSGI file has wrong username
   - Virtual environment path is incorrect
   - Missing dependencies in requirements.txt

### ImportError in logs

1. Make sure you activated the virtual environment:
   ```bash
   workon smartscheduler-venv
   pip install -r requirements.txt
   ```

2. Verify all packages are installed:
   ```bash
   pip list
   ```

### MongoDB Connection Issues

1. Ensure MongoDB Atlas allows connections from all IPs:
   - Go to MongoDB Atlas → Network Access
   - Add IP: `0.0.0.0/0`

2. Check that the MongoDB connection string in `app.py` is correct

### Application Runs but Static Files Don't Load

1. Verify the static files mapping in the Web tab
2. Check that the path is correct: `/home/Aarijkhan/smartScheduler/static`
3. Make sure the `static` folder exists in your project

## Updating Your Application

When you make changes to your code:

1. **If using Git:**
   ```bash
   cd ~/smartScheduler
   git pull
   ```

2. **If new dependencies were added:**
   ```bash
   workon smartscheduler-venv
   pip install -r requirements.txt
   ```

3. **Reload the web app:**
   - Go to Web tab
   - Click the green "Reload" button

## Important Notes

1. **Free Account Limitations:**
   - One web app only
   - Limited CPU seconds per day
   - App runs 24/7 (doesn't sleep like some platforms)

2. **Console Access:**
   - Free accounts have limited console time
   - Use Git for updates instead of editing files in console

3. **Custom Domain:**
   - Free accounts use: `Aarijkhan.pythonanywhere.com`
   - Paid accounts can use custom domains

## Quick Reference Commands

```bash
# Activate virtual environment
workon smartscheduler-venv

# Update code from Git
cd ~/smartScheduler && git pull

# Install/update dependencies
pip install -r requirements.txt

# Check Python version
python --version

# List installed packages
pip list

# View running processes
ps aux | grep python
```

## WSGI Configuration File Content

If you need to copy-paste the WSGI configuration, here it is again:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/Aarijkhan/smartScheduler'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Flask app
from app import app as application
```

## Need Help?

- Check [PythonAnywhere Help Pages](https://help.pythonanywhere.com/)
- View your error logs in the Web tab
- PythonAnywhere Forums: [www.pythonanywhere.com/forums](https://www.pythonanywhere.com/forums/)

---

**Your app URL:** `https://Aarijkhan.pythonanywhere.com`

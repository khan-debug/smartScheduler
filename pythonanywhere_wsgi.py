# WSGI configuration file for PythonAnywhere
# This file should be copied to the WSGI configuration file in your PythonAnywhere dashboard
# Path: Web tab → Code section → WSGI configuration file

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/Aarijkhan/smartScheduler'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables if needed
# os.environ['FLASK_ENV'] = 'production'

# Import your Flask app
from app import app as application

# If you need to set the secret key from environment variable:
# application.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

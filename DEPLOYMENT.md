# Deployment Guide for SmartScheduler

This guide will help you deploy SmartScheduler online so others can access it via a URL.

## Prerequisites

- Your code pushed to GitHub
- MongoDB Atlas connection string (already configured in `app.py`)
- Email settings configured in `config/email_settings.txt`

## Recommended Platforms (Free Tier Available)

### Option 1: Render.com (Recommended - Easiest)

1. **Create a Render account**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

2. **Create a new Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `smartScheduler` repository

3. **Configure the service**
   - **Name**: `smartscheduler` (or your preferred name)
   - **Region**: Choose closest to your location
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

4. **Set Environment Variables** (Optional - currently using hardcoded values)
   - You can add environment variables later if needed
   - Currently, MongoDB URI and email settings are in the code

5. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment
   - Your app will be live at: `https://smartscheduler-xxxx.onrender.com`

**Note**: Free tier sleeps after 15 minutes of inactivity. First request may take 30-60 seconds to wake up.

---

### Option 2: Railway.app

1. **Create a Railway account**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Deploy from GitHub**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `smartScheduler` repository

3. **Configure**
   - Railway will auto-detect it's a Python app
   - It will automatically use the `Procfile` for deployment

4. **Generate Domain**
   - Go to Settings → "Generate Domain"
   - Your app will be live at: `https://smartscheduler-production-xxxx.up.railway.app`

**Note**: Railway gives you $5 credit/month on free tier.

---

### Option 3: PythonAnywhere

1. **Create account**
   - Go to [pythonanywhere.com](https://www.pythonanywhere.com)
   - Sign up for free account

2. **Upload code**
   - Use Git to clone your repository
   - Or upload files via Web interface

3. **Configure Web App**
   - Create a new Flask web app
   - Point to your `app.py`
   - Install requirements: `pip install -r requirements.txt`

4. **Your URL**
   - Free tier gives you: `https://yourusername.pythonanywhere.com`

---

## Post-Deployment Checklist

- [ ] Test the deployed URL
- [ ] Verify MongoDB connection works
- [ ] Test user registration (check email delivery)
- [ ] Create a test schedule
- [ ] Share URL with friends for testing

## Troubleshooting

### App not loading
- Check deployment logs on your platform
- Verify MongoDB connection string is correct
- Ensure all files are committed to GitHub

### Email not sending
- Check `config/email_settings.txt` is present
- Verify SMTP credentials are correct
- Check Gmail "Less secure app access" or use App Password

### Database connection issues
- Verify MongoDB Atlas network access (whitelist 0.0.0.0/0 for all IPs)
- Check connection string format

## Important Notes

1. **MongoDB Atlas Network Access**
   - Go to MongoDB Atlas → Network Access
   - Add IP: `0.0.0.0/0` (allows access from anywhere)
   - This is necessary for cloud deployments

2. **Free Tier Limitations**
   - Render: App sleeps after 15 min inactivity
   - Railway: $5 credit/month
   - PythonAnywhere: Limited requests/day

3. **Scaling**
   - For production use, consider paid tiers
   - Current setup is perfect for testing with friends

## Quick Deploy Button (for Render)

Once you push to GitHub, you can add this to your README:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

---

**Need help?** Check the logs on your deployment platform or open an issue on GitHub.

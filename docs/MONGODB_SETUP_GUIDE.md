# MongoDB Connection Issue - Solutions

## Current Problem
Your application cannot connect to MongoDB Atlas due to **SSL/TLS compatibility issues** between:
- Python 3.14.2 (very new)
- OpenSSL 3.6.0 (very new, October 2025)
- MongoDB Atlas servers (using older TLS configurations)

## Error
```
SSL handshake failed: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
```

## Solutions (Try in Order)

### Solution 1: Add Your IP to MongoDB Atlas Network Access ⭐ MOST LIKELY FIX
1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Select your project and cluster
3. Click "Network Access" in the left sidebar
4. Click "Add IP Address"
5. Either:
   - Click "Add Current IP Address" (recommended)
   - Or add `0.0.0.0/0` for testing (NOT recommended for production)
6. Click "Confirm"
7. Wait 1-2 minutes for changes to propagate
8. Try running the app again: `python app.py`

### Solution 2: Use Python with Older OpenSSL
Your current Python 3.14.2 with OpenSSL 3.6.0 is too new. MongoDB Atlas works best with:
- Python 3.9-3.11
- OpenSSL 1.1.1 or 3.0.x

**Create a new conda environment:**
```bash
# Create environment with Python 3.11
conda create -n smartscheduler python=3.11 -y
conda activate smartscheduler

# Install dependencies
pip install flask pymongo certifi dnspython

# Run the app
python app.py
```

### Solution 3: Verify MongoDB Atlas Cluster Status
1. Log in to MongoDB Atlas
2. Ensure your cluster is **not paused**
3. Check cluster health status
4. Restart the cluster if needed

### Solution 4: Use Standard MongoDB Connection (Not mongodb+srv)
If the above don't work, try getting a standard `mongodb://` connection string:
1. In MongoDB Atlas, click "Connect"
2. Choose "Connect your application"
3. Select "Python" driver
4. Copy the standard connection string (mongodb:// not mongodb+srv://)
5. Update `MONGO_URI` in `app.py`

### Solution 5: Use Docker with Compatible Python
```bash
# Create a Dockerfile with Python 3.11
docker run -it -p 5000:5000 -v $(pwd):/app python:3.11-slim bash
cd /app
pip install flask pymongo certifi dnspython
python app.py
```

## Testing the Connection
After trying any solution, test with:
```bash
python test_mongo_openssl_fix.py
```

## Current Connection String
```
mongodb+srv://aarij67800_db_user:PmfScGkGndRJAyIt@cluster1.ittpo49.mongodb.net/
```

## Need More Help?
Check:
- MongoDB Atlas documentation: https://docs.atlas.mongodb.com/
- PyMongo compatibility: https://pymongo.readthedocs.io/
- OpenSSL compatibility issues with Python 3.14

---
**Most users fix this by adding their IP to MongoDB Atlas Network Access (Solution 1)**

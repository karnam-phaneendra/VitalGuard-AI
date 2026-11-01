import motor.motor_asyncio
import os

# MongoDB connection
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017/"
)

client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000
)

# Database
db = client.hospital_monitoring

# Collections
patients_col = db.patients
vitals_col = db.vitals
billing_col = db.billing
insurance_col = db.insurance
alerts_col = db.alerts
prescriptions_col = db.prescriptions
payments_col = db.payments

# Check database connection
async def check_db_connection():
    try:
        await client.admin.command("ping")
        print("MongoDB Connected Successfully!")
        return True
    except Exception as e:
        print("MongoDB Connection Failed:", e)
        return False
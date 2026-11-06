import motor.motor_asyncio
import os

PRIMARY_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/").strip()
LOCAL_URI = "mongodb://127.0.0.1:27017/"

def get_working_client():
    # Configure resilient AsyncIOMotorClient with TLS options for Atlas & fallback
    try:
        return motor.motor_asyncio.AsyncIOMotorClient(
            PRIMARY_URI,
            serverSelectionTimeoutMS=5000,
            tlsAllowInvalidCertificates=True
        )
    except Exception as e:
        print(f"Error creating Motor client: {e}, falling back to local MongoDB.")
        return motor.motor_asyncio.AsyncIOMotorClient(
            LOCAL_URI,
            serverSelectionTimeoutMS=5000
        )

client = get_working_client()

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
users_col = db.users

# Check database connection
async def check_db_connection():
    try:
        await client.admin.command("ping")
        print("MongoDB Connected Successfully!")
        return True
    except Exception as e:
        print("MongoDB Connection Failed:", e)
        return False

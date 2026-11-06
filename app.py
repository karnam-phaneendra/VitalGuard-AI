from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
import cv2
import base64
from dotenv import load_dotenv

load_dotenv()

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib import styles
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import jwt
from pwdlib import PasswordHash

# Database
from database.mongodb import db, patients_col, vitals_col, billing_col, insurance_col, alerts_col, prescriptions_col, payments_col


# Collections
users_col = db.users

# Agents
from agents.risk_agent import analyze_vitals, detect_critical_alerts
from agents.pharmacy_agent import (
    check_medicine_availability,
    get_medicine_price,
    find_medicine,
    decrement_medicine_stock,
    search_medicines,
    get_inventory_summary
)
from agents.billing_agent import calculate_bill
from agents.insurance_agent import check_insurance_eligibility
from agents.doctor_agent import decide_discharge

# Existing OCR Module
from vital_extractor.extractor import VitalExtractor
from vital_extractor.preprocess import preprocess_image, load_image, load_image_from_bytes


# Authentication Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing from environment variables")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Argon2 password hashing
password_hash = PasswordHash.recommended()

app = FastAPI(title="AI Hospital Monitoring System")

# Helper for security
# Helper for security - JWT Authentication
async def verify_admin(request: Request):
    auth_header = request.headers.get("Authorization", "")

    scheme, _, token = auth_header.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication token missing",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return payload

async def verify_patient_exists(patient_id: str):
    p_id = patient_id.lower()
    patient = await patients_col.find_one({"patient_id": p_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

async def verify_patient_active(patient_id: str):
    patient = await verify_patient_exists(patient_id)
    if patient.get("discharge"):
        raise HTTPException(status_code=400, detail="Patient is already discharged")
    return patient

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5174")

origins = list({
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    FRONTEND_URL,
    FRONTEND_ORIGIN
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(FRONTEND_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

# OCR Extractor Instance (Lazy-loaded to allow instant port binding on Render / cloud containers)
_extractor_instance = None

def get_extractor():
    global _extractor_instance
    if _extractor_instance is None:
        print("Initializing VitalExtractor (PaddleOCR)...", flush=True)
        _extractor_instance = VitalExtractor()
    return _extractor_instance

# Helper for password hashing# Helper for password hashing - Argon2
def hash_password(password: str):
    return password_hash.hash(password)


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "VitalGuard AI Backend API",
        "health": "/health",
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "VitalGuard AI"}

# Admin account initialization
@app.on_event("startup")
async def seed_admin():
    # Verify MongoDB connection safely without crashing the web service on startup
    try:
        await db.command("ping")
        print("MongoDB Connected Successfully!", flush=True)

        admin_email = os.getenv("ADMIN_EMAIL", "admin@hospital.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "PHANI123@9999")

        admin = await users_col.find_one({"email": admin_email})
        if not admin:
            await users_col.insert_one({
                "email": admin_email,
                "password": hash_password(admin_password),
                "role": "admin"
            })
            print("Admin account created successfully", flush=True)
        else:
            await users_col.update_one(
                {"_id": admin["_id"]},
                {
                    "$set": {
                        "password": hash_password(admin_password),
                        "role": "admin"
                    }
                }
            )
            print("Admin password verified", flush=True)
    except Exception as e:
        print(f"WARNING: MongoDB Atlas connection or authentication error: {e}", flush=True)
        print("Server remains running so Render can bind ports. Please verify your MONGODB_URI in Render dashboard.", flush=True)


# Login API
@app.post("/login")
async def login(
    email: str = Form(None),
    password: str = Form(None),
    patient_id: str = Form(None)
):
    # Patient login - preserve existing functionality
    if patient_id:
        p_id = patient_id.lower()

        patient = await patients_col.find_one({"patient_id": p_id})

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient ID not found"
            )

        return {
            "role": "patient",
            "patient_id": p_id,
            "name": patient["name"]
        }

    # Admin login
    if email and password:
        user = await users_col.find_one({"email": email})

        if not user or not password_hash.verify(
            password,
            user.get("password", "")
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid admin credentials"
            )

        payload = {
            "sub": user["email"],
            "role": "admin",
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }

        token = jwt.encode(
            payload,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM
        )

        return {
            "role": "admin",
            "email": user["email"],
            "token": token,
            "token_type": "bearer"
        }

    raise HTTPException(
        status_code=400,
        detail="Missing login credentials"
    )

@app.post("/register_patient")
async def register_patient(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    disease: str = Form(...),
    doctor: str = Form(...),
    bed_number: str = Form(...),
):
    await verify_admin(request)
    patient_id = str(uuid.uuid4())[:8]
    patient_data = {
        "patient_id": patient_id,
        "name": name,
        "age": age,
        "disease": disease,
        "doctor": doctor,
        "bed_number": bed_number,
        "status": "admitted",  # Default status
        "admission_date": datetime.now(),
        "bill_paid": False
    }
    await patients_col.insert_one(patient_data)
    return {"message": "Patient registered successfully", "patient_id": patient_id}

@app.post("/upload_vitals")
async def upload_vitals(
    request: Request,
    patient_id: str = Form(...),
    image: UploadFile = File(...)
):
    print("DEBUG: UPLOAD_VITALS ENDPOINT HIT", flush=True)
    await verify_admin(request)
    await verify_patient_active(patient_id)

    # In-memory image processing: Zero server disk usage, immune to container storage limits!
    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image is empty")
        img_bgr = load_image_from_bytes(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image decoding failed: {str(e)}")
    
    # OCR Extraction directly in memory
    try:
        processed_img = preprocess_image(img_bgr)
        extracted_vitals = get_extractor().extract_vitals_from_image(processed_img)
        print("FINAL EXTRACTED VITALS:", extracted_vitals, flush=True)
        
        # Format vitals for agent and storage
        vitals = {
            "heart_rate": extracted_vitals.get("heart_rate"),
            "spo2": extracted_vitals.get("spo2"),
            "bp": extracted_vitals.get("blood_pressure"),
            "resp_rate": extracted_vitals.get("respiration"),
            "temperature": extracted_vitals.get("temperature"),
        }

        # Risk Agent Analysis
        risk_level = analyze_vitals(vitals)
        
        # Lightweight base64 snapshot (stored safely in MongoDB Atlas, zero server disk usage)
        _, buffer = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 65])
        b64_snapshot = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

        # Store Vitals
        vitals_data = {
            "patient_id": patient_id,
            "image_path": image.filename,
            "image_snapshot": b64_snapshot,
            "heart_rate": vitals.get("heart_rate"),
            "spo2": vitals.get("spo2"),
            "bp": vitals.get("bp"),
            "resp_rate": vitals.get("resp_rate"),
            "temperature": vitals.get("temperature"),
            "risk_level": risk_level,
            "timestamp": datetime.now()
        }
        await vitals_col.insert_one(vitals_data)
        
        # Check Critical Alerts
        # Resolve previous alerts when the corresponding vital becomes normal
        safe_vitals = {
            "SpO2": vitals.get("spo2") is not None and vitals["spo2"] >= 95,

            "Heart Rate": vitals.get("heart_rate") is not None
                  and 60 <= vitals["heart_rate"] <= 100,

            "Temperature": vitals.get("temperature") is not None
                   and 36.1 <= vitals["temperature"] <= 37.2,

            "Respiratory Rate": vitals.get("resp_rate") is not None
                        and 12 <= vitals["resp_rate"] <= 20
            }

        for vital_name, is_safe in safe_vitals.items():
            if is_safe:
                await alerts_col.update_many(
                    {
                        "patient_id": patient_id,
                        "alert_type": "CRITICAL_VITAL",
                        "vital": vital_name,
                        "status": {"$ne": "resolved"}
            },
            {
                "$set": {
                    "status": "resolved",
                    "resolved_at": datetime.now()
                }
            }
        )

# Generate new alerts
        critical_alerts = detect_critical_alerts(patient_id, vitals)

# Mark newly generated alerts as active
        for alert in critical_alerts:
                alert["status"] = "active"

        if critical_alerts:
            await alerts_col.insert_many(critical_alerts)
        
        return {
            "status": "success",
            "vitals": vitals,
            "risk_level": risk_level,
            "critical_alerts": [a['message'] for a in critical_alerts] if critical_alerts else []
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assign_medicine")
async def assign_medicine(request: Request, patient_id: str = Form(...), medicine_name: str = Form(...), quantity: int = Form(...)):
    await verify_admin(request)
    p_id = patient_id.lower()
    await verify_patient_active(p_id)

    med_info = find_medicine(medicine_name)
    if not med_info:
        await alerts_col.insert_one({
            "patient_id": p_id,
            "alert_type": "PHARMACY_ALERT",
            "message": f"Medicine '{medicine_name}' NOT found in pharmacy inventory.",
            "timestamp": datetime.now()
        })
        return {"status": "unavailable", "message": f"Medicine '{medicine_name}' not found in pharmacy."}

    current_stock = med_info["quantity"]
    if current_stock < quantity:
        await alerts_col.insert_one({
            "patient_id": p_id,
            "alert_type": "PHARMACY_ALERT",
            "message": f"Medicine '{med_info['medicine_name']}' has insufficient stock ({current_stock} available, requested {quantity}).",
            "timestamp": datetime.now()
        })
        return {
            "status": "unavailable",
            "message": f"Insufficient stock for {med_info['medicine_name']}. Only {current_stock} units available."
        }
    
    unit_price = med_info["price"]
    total_cost = round(unit_price * quantity, 2)
    
    # Decrement stock in pharmacy dataset
    remaining_stock = decrement_medicine_stock(med_info["medicine_name"], quantity)
    if remaining_stock is None:
        remaining_stock = max(0, current_stock - quantity)
        
    # Stock availability warning logic:
    # < 50: RED WARNING
    # <= 100: YELLOW WARNING
    # > 100: Normal
    if remaining_stock < 50:
        warning_level = "red"
        warning_msg = f"CRITICAL STOCK ALERT: Only {remaining_stock} units left of {med_info['medicine_name']} (< 50 units)!"
        await alerts_col.insert_one({
            "patient_id": p_id,
            "alert_type": "CRITICAL_ALERT",
            "message": warning_msg,
            "timestamp": datetime.now()
        })
    elif remaining_stock <= 100:
        warning_level = "yellow"
        warning_msg = f"LOW STOCK WARNING: Only {remaining_stock} units left of {med_info['medicine_name']} (<= 100 units)."
        await alerts_col.insert_one({
            "patient_id": p_id,
            "alert_type": "PHARMACY_WARNING",
            "message": warning_msg,
            "timestamp": datetime.now()
        })
    else:
        warning_level = "none"
        warning_msg = f"In stock: {remaining_stock} units remaining."
        
    prescription = {
        "patient_id": p_id,
        "medicine_name": med_info["medicine_name"],
        "nickname": med_info.get("nickname", ""),
        "generic_name": med_info.get("generic_name", ""),
        "quantity": quantity,
        "price": unit_price,
        "total_cost": total_cost,
        "stock_remaining": remaining_stock,
        "stock_warning": warning_level,
        "status": "assigned",
        "timestamp": datetime.now()
    }
    res = await prescriptions_col.insert_one(prescription)
    prescription["_id"] = str(res.inserted_id)
    
    return {
        "status": "success",
        "medicine_name": med_info["medicine_name"],
        "unit_price": unit_price,
        "total_cost": total_cost,
        "stock_remaining": remaining_stock,
        "warning_level": warning_level,
        "warning_message": warning_msg
    }

@app.get("/pharmacy/lookup")
async def pharmacy_lookup(q: str):
    med = find_medicine(q)
    if not med:
        raise HTTPException(status_code=404, detail=f"Medicine '{q}' not found in pharmacy inventory.")
    return med

@app.get("/pharmacy/search")
async def pharmacy_search(q: str = "", limit: int = 10):
    if not q:
        return []
    return search_medicines(q, limit=limit)

@app.get("/pharmacy/inventory")
async def pharmacy_inventory(limit: int = 100, alert: Optional[str] = None):
    return get_inventory_summary(limit=limit, filter_alert=alert)

@app.get("/patient/{patient_id}")
async def get_patient(patient_id: str):
    patient = await verify_patient_exists(patient_id)
    # Exclude _id from response
    patient_resp = {k: v for k, v in patient.items() if k != "_id"}
    if patient_resp.get("discharge") or patient_resp.get("status") == "discharged":
        patient_resp["status"] = "discharged"
        patient_resp["discharge"] = True
    else:
        patient_resp["status"] = "active"
        patient_resp["discharge"] = False
    return patient_resp

@app.get("/vitals/{patient_id}")
async def get_vitals(patient_id: str):
    patient_id = patient_id.lower()
    await verify_patient_exists(patient_id)
    cursor = vitals_col.find({"patient_id": patient_id}, {"_id": 0}).sort("timestamp", -1)
    vitals_list = await cursor.to_list(length=100)
    return vitals_list

@app.get("/billing/{patient_id}")
async def get_billing(patient_id: str):
    patient_id = patient_id.lower()
    # Sum medicine costs
    prescriptions = await prescriptions_col.find({"patient_id": patient_id}).to_list(100)
    medicine_cost = sum(p.get("total_cost", 0) for p in prescriptions)
    
    # Calculate bed days
    patient = await verify_patient_exists(patient_id)
    
    admission_date = patient.get("admission_date") or datetime.now()
    if isinstance(admission_date, str):
        try:
            admission_date = datetime.fromisoformat(admission_date.replace("Z", "+00:00"))
        except:
            admission_date = datetime.now()

    # Ensure both are naive for subtraction
    now = datetime.now()
    if hasattr(admission_date, "tzinfo") and admission_date.tzinfo:
        admission_date = admission_date.replace(tzinfo=None)
    
    days_admitted = max(1, (now - admission_date).days)
    
    # Use dynamic costs if set by admin, else defaults
    bed_cost_per_day = float(patient.get("bed_cost_per_day", 500))
    treatment_cost = float(patient.get("treatment_cost", 1000))
    
    bill = calculate_bill(medicine_cost, days_admitted, bed_cost_per_day, treatment_cost)
    
    # Dynamic Insurance Coverage manually entered (NO default value!)
    insurance_coverage = float(patient.get("insurance_coverage", 0.0))
    
    # Update or insert billing doc
    billing_doc = {
        "medicine_cost": medicine_cost,
        "bed_cost": bill['bed_cost'],
        "treatment_cost": treatment_cost,
        "total_bill": bill['total_bill'],
        "bed_cost_per_day": bed_cost_per_day,
        "insurance_coverage": insurance_coverage
    }
    
    await billing_col.update_one(
        {"patient_id": patient_id},
        [
            {"$set": billing_doc},
            {"$set": {"bill_paid": {"$ifNull": ["$bill_paid", False]}}}
        ],
        upsert=True
    )
    
    # Fetch payments
    payments = await payments_col.find({"patient_id": patient_id}).to_list(100)
    paid_amount = sum(float(p.get("amount", 0) or 0) for p in payments)
    
    remaining_balance = max(0.0, bill['total_bill'] - insurance_coverage - paid_amount)
    
    return {
        "medicine_cost": medicine_cost,
        "bed_cost": bill['bed_cost'],
        "bed_days": days_admitted,
        "bed_rate": bed_cost_per_day,
        "treatment_cost": treatment_cost,
        "total_bill": bill['total_bill'],
        "insurance_coverage": insurance_coverage,
        "paid_amount": paid_amount,
        "remaining_balance": remaining_balance
    }

@app.post("/update_billing_costs")
async def update_billing_costs(request: Request):
    await verify_admin(request)
    data = await request.json()
    patient_id = data.get("patient_id", "").lower()
    field = data.get("field") # 'bed_cost_per_day', 'treatment_cost', or 'insurance_coverage'
    new_value = data.get("new_value")
    
    if field not in ["bed_cost_per_day", "treatment_cost", "insurance_coverage"]:
        raise HTTPException(status_code=400, detail="Invalid field")
        
    await patients_col.update_one(
        {"patient_id": patient_id},
        {"$set": {field: float(new_value)}}
    )
    return {"status": "success", "field": field, "new_value": float(new_value)}
    
@app.post("/add_payment")
async def add_payment(
    request: Request,
    patient_id: str = Form(...),
    amount: float = Form(...),
    purpose: str = Form(...)
):
    await verify_admin(request)
    patient_id = patient_id.lower()
    await verify_patient_active(patient_id)
    
    payment_doc = {
        "patient_id": patient_id,
        "amount": amount,
        "purpose": purpose,
        "timestamp": datetime.now()
    }
    await payments_col.insert_one(payment_doc)
    return {"status": "success", "message": "Payment recorded successfully"}

@app.get("/payments/{patient_id}")
async def get_payments(patient_id: str):
    patient_id = patient_id.lower()
    await verify_patient_exists(patient_id)
         
    cursor = payments_col.find({"patient_id": patient_id}, {"_id": 0}).sort("timestamp", -1)
    payments = await cursor.to_list(length=100)
    return payments

@app.get("/decision/{patient_id}")
async def get_decision(patient_id: str):
    patient_id = patient_id.lower()
    patient = await verify_patient_exists(patient_id)
    
    if patient.get("discharge"):
        return {"discharge": False, "reason": "Already discharged"}

    # Last 48h vitals
    time_limit_48h = datetime.now() - timedelta(hours=48)
    vitals_history = await vitals_col.find({"patient_id": patient_id, "timestamp": {"$gte": time_limit_48h}}).to_list(100)
    
    # Check for Critical alerts in last 24h
    time_limit_24h = datetime.now() - timedelta(hours=24)
    alerts_24h = await alerts_col.find({"patient_id": patient_id, "timestamp": {"$gte": time_limit_24h}}).to_list(100)
    has_critical_alerts = any("CRITICAL" in a.get("message", "").upper() or "CRITICAL" in a.get("alert_type", "").upper() for a in alerts_24h)
    
    # Billing info
    bill_info = await get_billing(patient_id)
    total_bill = bill_info.get("total_bill", 0)
    total_payments = bill_info.get("paid_amount", 0) + bill_info.get("insurance_coverage", 0)
    
    discharge, reason = decide_discharge(vitals_history, has_critical_alerts, total_payments, total_bill)
    
    if discharge:
        await patients_col.update_one(
            {"patient_id": patient_id}, 
            {"$set": {
                "status": "discharged", 
                "discharge": True, 
                "discharged_at": datetime.now(), 
                "discharge_type": "Regular", 
                "doctor_notes": "Patient recovered."
            }}
        )
        
    return {
        "patient_id": patient_id,
        "discharge": discharge,
        "reason": reason
    }

@app.get("/patients")
async def get_all_patients():
    patients = await patients_col.find().to_list(100)
    # Convert ObjectIDs to strings and normalize status
    for p in patients:
        p["_id"] = str(p["_id"])
        is_discharged = bool(p.get("discharge") or p.get("status") == "discharged")
        p["status"] = "discharged" if is_discharged else "active"
        p["discharge"] = is_discharged
    return patients

@app.get("/alerts/{patient_id}")
async def get_alerts(patient_id: str):
    patient_id = patient_id.lower()
    await verify_patient_exists(patient_id)
    alerts = await alerts_col.find({
    "patient_id": patient_id,
    "status": {"$ne": "resolved"}
}).sort("timestamp", -1).to_list(50)
    for a in alerts:
        a["_id"] = str(a["_id"])
    return alerts

@app.get("/latest_vitals/{patient_id}")
async def get_latest_vitals(patient_id: str):
    patient_id = patient_id.lower()
    await verify_patient_exists(patient_id)
    latest = await vitals_col.find_one({"patient_id": patient_id}, sort=[("timestamp", -1)])
    if not latest:
        return {}
    latest["_id"] = str(latest["_id"])
    return latest

@app.get("/prescriptions/{patient_id}")
async def get_prescriptions(patient_id: str):
    patient_id = patient_id.lower()
    await verify_patient_exists(patient_id)
    cursor = prescriptions_col.find({"patient_id": patient_id}).sort("timestamp", -1)
    prescriptions = await cursor.to_list(length=100)
    for p in prescriptions:
        p["_id"] = str(p["_id"])
        med_info = find_medicine(p.get("medicine_name", ""))
        if med_info:
            p["stock_remaining"] = med_info.get("quantity", 0)
            p["warning_level"] = med_info.get("warning_level", "none")
            p["warning_message"] = med_info.get("warning_message", "")
    return prescriptions

@app.delete("/prescription/{presc_id}")
async def delete_prescription(request: Request, presc_id: str):
    print(f"DEBUG: DELETE request for {presc_id}")

    await verify_admin(request)
    try:
        obj_id = ObjectId(presc_id)
        result = await prescriptions_col.delete_one({"_id": obj_id})
        print(f"DEBUG: Deleted count: {result.deleted_count}")
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return {"status": "success", "message": "Prescription deleted"}
    except Exception as e:
        print(f"DEBUG: Delete error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid ID or error: {str(e)}")

@app.get("/discharge_report/{patient_id}")
async def get_discharge_report(patient_id: str):
    patient_id = patient_id.lower()
    patient = await verify_patient_exists(patient_id)
    patient_resp = {k: v for k, v in patient.items() if k != "_id"}
    
    vitals = await get_vitals(patient_id)
    prescriptions = await get_prescriptions(patient_id)
    billing = await get_billing(patient_id)
    payments = await get_payments(patient_id)
    alerts = await get_alerts(patient_id)
    
    decision = await get_decision(patient_id)
    
    return {
        "patient": patient_resp,
        "vitals": vitals,
        "prescriptions": prescriptions,
        "billing": billing,
        "payments": payments,
        "alerts": alerts,
        "decision": decision
    }

@app.post("/generate_report/{patient_id}")
async def generate_report(request: Request, patient_id: str):
    await verify_admin(request)
    patient_id = patient_id.lower()
    
    report_data = await get_discharge_report(patient_id)
    patient = report_data["patient"]
    vitals = report_data["vitals"]
    prescriptions = report_data["prescriptions"]
    billing = report_data["billing"]
    payments = report_data["payments"]
    
    os.makedirs("reports", exist_ok=True)
    pdf_path = os.path.join("reports", f"{patient_id}_discharge.pdf")
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    # Title
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=20)
    elements.append(Paragraph("DISCHARGE REPORT", title_style))
     
    # Patient Info
    elements.append(Paragraph("Patient Information", styles['Heading2']))
    p_info = [
        [f"Name: {patient.get('name', 'N/A')}", f"ID: {patient.get('patient_id', 'N/A')}"],
        [f"Age: {patient.get('age', 'N/A')}", f"Disease: {patient.get('disease', 'N/A')}"],
        [f"Status: {patient.get('status', 'N/A')}", f"Discharged At: {patient.get('discharged_at', 'N/A')}"]
    ]
    t_info = Table(p_info, colWidths=[250, 250])
    t_info.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 10))
    
    # Vitals Table
    if vitals:
        elements.append(Paragraph("Vitals History (Last 5 records)", styles['Heading2']))
        v_data = [["Time", "SpO2", "Heart Rate", "Temp", "BP"]]
        for v in vitals[:5]:
            ts = v.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M") if hasattr(ts, 'strftime') else str(ts)
            v_data.append([
                ts_str,
                str(v.get("spo2", "-")),
                str(v.get("heart_rate", "-")),
                str(v.get("temperature", "-")),
                str(v.get("bp", "-"))
            ])
        t_vitals = Table(v_data, colWidths=[120, 70, 80, 70, 100])
        t_vitals.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(t_vitals)
        elements.append(Spacer(1, 10))
        
    # Medicines
    if prescriptions:
        elements.append(Paragraph("Medicines Prescribed", styles['Heading2']))
        m_data = [["Medicine", "Quantity", "Total Cost"]]
        for p in prescriptions:
            m_data.append([
                str(p.get("medicine_name", "-")),
                str(p.get("quantity", "-")),
                f"₹{float(p.get('total_cost', 0)):,.2f}"
            ])
        t_meds = Table(m_data, colWidths=[250, 100, 100])
        t_meds.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(t_meds)
        elements.append(Spacer(1, 10))
        
    # Billing
    elements.append(Paragraph("Billing Summary", styles['Heading2']))
    b_data = [
    ["Total Bill:", f"₹{float(billing.get('total_bill', 0)):,.2f}"],
    ["Total Payments:", f"₹{sum(float(p.get('amount', 0) or 0) for p in payments):,.2f}"],
    ["Remaining:", f"₹{float(billing.get('remaining_balance', 0)):,.2f}"]
    ] 
    t_bill = Table(b_data, colWidths=[200, 200])
    t_bill.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(t_bill)
    elements.append(Spacer(1, 10))
    
    # Final Status
    elements.append(Paragraph("Final Decisions & Notes", styles['Heading2']))
    decision_info = report_data.get("decision", {})
    elements.append(Paragraph(f"Discharge Ready: {decision_info.get('discharge', False)}", styles['Normal']))
    elements.append(Paragraph(f"Reason: {decision_info.get('reason', '')}", styles['Normal']))
    if patient.get("doctor_notes"):
        elements.append(Paragraph(f"Doctor Notes: {patient.get('doctor_notes')}", styles['Normal']))
    
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], alignment=1, textColor=colors.gray)
    elements.append(Paragraph("Generated by VitalGuard AI", footer_style))
    
    doc.build(elements)
    
    return {"file_url": f"/reports/{patient_id}_discharge.pdf"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

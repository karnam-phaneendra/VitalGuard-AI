import asyncio
import os
import sys

# Add project root to path to import database
sys.path.append(os.getcwd())

from database.mongodb import patients_col, prescriptions_col, billing_col

async def diagnose():
    patient_id = "88bccc3b" # From screenshot
    print(f"--- Diagnosing Patient {patient_id} ---")
    
    patient = await patients_col.find_one({"patient_id": patient_id})
    print(f"Patient Found: {patient is not None}")
    if patient:
        print(f"Name: {patient.get('name')}")
    
    prescriptions = await prescriptions_col.find({"patient_id": patient_id}).to_list(length=100)
    print(f"Prescriptions Count: {len(prescriptions)}")
    for p in prescriptions:
        print(f" - {p.get('medicine_name')}: {p.get('quantity')} (Price: {p.get('price')}, Total: {p.get('total_cost')}, TS: {p.get('timestamp')})")
        
    billing = await billing_col.find_one({"patient_id": patient_id})
    if billing:
        print(f"Billing Total: {billing.get('total_bill')}")
        print(f"Medicine Cost: {billing.get('medicine_cost')}")
    else:
        print("Billing document NOT FOUND")

if __name__ == "__main__":
    asyncio.run(diagnose())

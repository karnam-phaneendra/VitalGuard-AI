from datetime import datetime

def decide_discharge(vitals_history, has_critical_alerts_24h, total_payments, total_bill):
    """
    Conditions:
    1. Minimum 5 records
    2. Sort vitals by timestamp
    3. Rules for last 48 hours:
       - SpO2 > 94
       - Temp < 38
       - Heart Rate < 100
    4. No CRITICAL alerts in last 24h
    5. total_payments >= total_bill
    """
    # 1) Minimum 5 records
    if not vitals_history or len(vitals_history) < 5:
        return False, f"Insufficient vitals history. Need at least 5 readings (found {len(vitals_history) if vitals_history else 0})."

    # 2) Sort vitals by timestamp ascending
    try:
        sorted_vitals = sorted(vitals_history, key=lambda x: x.get("timestamp") or datetime.min)
    except Exception:
        sorted_vitals = vitals_history

    # 3) Apply rules
    for v in sorted_vitals:
        spo2 = v.get("spo2")
        temp = v.get("temperature")
        hr = v.get("heart_rate")
        
        if spo2 is not None and float(spo2) <= 94:
            return False, f"Unstable SpO2 detected: {spo2}"
        if temp is not None and float(temp) >= 38:
            return False, f"Unstable Temperature detected: {temp}"
        if hr is not None and float(hr) >= 100:
            return False, f"Unstable Heart Rate detected: {hr}"

    # 4) Check CRITICAL alerts in last 24h
    if has_critical_alerts_24h:
        return False, "CRITICAL alerts detected in the last 24 hours."
    
    # 5) Payment logic
    if total_payments < total_bill:
        return False, f"Pending payment. Total paid: {total_payments}, Total bill: {total_bill}."

    return True, "Patient is stable and ready for discharge."

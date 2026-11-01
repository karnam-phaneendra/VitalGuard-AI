from datetime import datetime


def analyze_vitals(vitals):
    """
    Overall risk classification based on adult vital-sign thresholds.
    """
    spo2 = vitals.get("spo2")
    temp = vitals.get("temperature")
    hr = vitals.get("heart_rate")
    rr = vitals.get("resp_rate")

    if (
        (spo2 is not None and spo2 < 95) or
        (temp is not None and (temp < 36.1 or temp > 37.2)) or
        (hr is not None and (hr < 60 or hr > 100)) or
        (rr is not None and (rr < 12 or rr > 20))
    ):
        return "HIGH_RISK"

    return "LOW_RISK"


def detect_critical_alerts(patient_id, vitals):
    """
    Generate WARNING and CRITICAL alerts for abnormal vital signs.
    Thresholds are illustrative adult resting reference values.
    """
    alerts = []

    spo2 = vitals.get("spo2")
    hr = vitals.get("heart_rate")
    temp = vitals.get("temperature")
    rr = vitals.get("resp_rate")

    def add_alert(vital, value, severity, message, normal_range):
        alerts.append({
            "patient_id": patient_id,
            "alert_type": "CRITICAL_VITAL",
            "severity": severity,
            "vital": vital,
            "value": value,
            "normal_range": normal_range,
            "message": message,
            "timestamp": datetime.now()
        })

    # Oxygen saturation
    if spo2 is not None:
        if spo2 < 85:
            add_alert("SpO2", spo2, "CRITICAL",
                      f"Critical oxygen saturation: {spo2}%.",
                      "95-100%")
        elif spo2 < 95:
            add_alert("SpO2", spo2, "WARNING",
                      f"Low oxygen saturation detected: {spo2}%.",
                      "95-100%")

    # Heart rate
    if hr is not None:
        if hr < 40 or hr > 140:
            add_alert("Heart Rate", hr, "CRITICAL",
                      f"Critical heart rate detected: {hr} bpm.",
                      "60-100 bpm")
        elif hr < 60 or hr > 100:
            severity = "WARNING"
            message = f"Abnormal heart rate detected: {hr} bpm."
            add_alert("Heart Rate", hr, severity, message, "60-100 bpm")

    # Body temperature
    if temp is not None:
        if temp > 40:
            add_alert("Temperature", temp, "CRITICAL",
                      f"Critical temperature detected: {temp}°C.",
                      "36.1-37.2°C")
        elif temp > 37.2 or temp < 36.1:
            add_alert("Temperature", temp, "WARNING",
                      f"Abnormal temperature detected: {temp}°C.",
                      "36.1-37.2°C")

    # Respiratory rate
    if rr is not None:
        if rr < 8 or rr > 30:
            add_alert("Respiratory Rate", rr, "CRITICAL",
                      f"Critical respiratory rate detected: {rr}/min.",
                      "12-20/min")
        elif rr < 12 or rr > 20:
            add_alert("Respiratory Rate", rr, "WARNING",
                      f"Abnormal respiratory rate detected: {rr}/min.",
                      "12-20/min")

    return alerts


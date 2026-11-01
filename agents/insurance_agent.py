def check_insurance_eligibility(patient_id):
    # Simulated check
    import random
    return "approved" if random.random() > 0.3 else "denied"

def update_coverage(current_coverage, bill_amount):
    """
    Subtract hospital bill from coverage.
    """
    remaining = current_coverage - bill_amount
    return max(0, remaining)

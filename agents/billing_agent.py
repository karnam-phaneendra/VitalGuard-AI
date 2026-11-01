def calculate_bill(medicine_cost, admission_days, bed_cost_per_day, treatment_cost):
    """
    Calculate total bill using:
    total_bill = medicine_cost + (bed_cost_per_day * admission_days) + treatment_cost
    """
    bed_total = admission_days * bed_cost_per_day
    total_bill = medicine_cost + bed_total + treatment_cost
    
    return {
        "medicine_cost": medicine_cost,
        "bed_cost": bed_total,
        "treatment_cost": treatment_cost,
        "total_bill": total_bill
    }

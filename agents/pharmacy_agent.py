import pandas as pd
import os

DATASET_PATH = os.path.join("dataset", "hospital_pharmacy_inventory.csv")

def check_medicine_availability(medicine_name, quantity):
    """
    Check medicine availability using the dataset.
    Returns: available, limited, out_of_stock
    """
    if not os.path.exists(DATASET_PATH):
        return "out_of_stock"
    
    df = pd.read_csv(DATASET_PATH)
    # Case insensitive search
    match = df[df['medicine_name'].str.contains(medicine_name, case=False, na=False)]
    
    if match.empty:
        return "out_of_stock"
    
    available_qty = match.iloc[0]['quantity']
    
    if available_qty >= quantity:
        return "available"
    elif available_qty > 0:
        return "limited"
    else:
        return "out_of_stock"

def get_medicine_price(medicine_name):
    if not os.path.exists(DATASET_PATH):
        return 0
    
    df = pd.read_csv(DATASET_PATH)
    match = df[df['medicine_name'].str.contains(medicine_name, case=False, na=False)]
    
    if match.empty:
        return 0
    
    return float(match.iloc[0]['price'])

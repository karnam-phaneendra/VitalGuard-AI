import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "hospital_pharmacy_inventory.csv")

def _load_inventory():
    if not os.path.exists(DATASET_PATH):
        return pd.DataFrame(columns=[
            "medicine_name", "nickname", "generic_name", "price", "quantity", "unit", "category", "stock_alert", "availability"
        ])
    return pd.read_csv(DATASET_PATH)

def _save_inventory(df):
    df.to_csv(DATASET_PATH, index=False)

def find_medicine(query):
    """
    Search for a medicine by exact name, nickname, or generic name with smart prioritization.
    Returns a dict with all details, accurate Indian price in INR, available stock, and warning level.
    """
    if not query:
        return None
    
    df = _load_inventory()
    if df.empty:
        return None
        
    query_clean = str(query).strip().lower()
    
    # 1. Exact match on medicine_name
    match = df[df['medicine_name'].str.lower() == query_clean]
    
    # 2. Match in nicknames (comma-separated aliases)
    if match.empty and 'nickname' in df.columns:
        match = df[df['nickname'].astype(str).str.lower().apply(lambda x: any(query_clean == alias.strip() for alias in x.split(',')))]
        
    # 3. Match in generic name
    if match.empty and 'generic_name' in df.columns:
        match = df[df['generic_name'].astype(str).str.lower() == query_clean]

    # 4. Word startswith match in medicine_name or nicknames
    if match.empty:
        match = df[df['medicine_name'].str.lower().str.startswith(query_clean)]

    # 5. Fallback substring search
    if match.empty:
        match = df[
            df['medicine_name'].str.contains(query_clean, case=False, na=False) |
            df['nickname'].astype(str).str.contains(query_clean, case=False, na=False) |
            df['generic_name'].astype(str).str.contains(query_clean, case=False, na=False)
        ]

    if match.empty:
        return None

    row = match.iloc[0]
    qty = int(row.get('quantity', 0))
    price = float(row.get('price', 0.0))
    
    # Stock availability warning logic:
    # < 50: RED WARNING
    # <= 100: YELLOW WARNING
    # > 100: Normal (In Stock)
    if qty <= 0:
        stock_status = "out_of_stock"
        warning_level = "red"
        warning_message = "OUT OF STOCK: 0 units available in pharmacy."
    elif qty < 50:
        stock_status = "critical_stock"
        warning_level = "red"
        warning_message = f"CRITICAL STOCK ALERT: Only {qty} units available (< 50 units)! Immediate replenishment required."
    elif qty <= 100:
        stock_status = "low_stock"
        warning_level = "yellow"
        warning_message = f"LOW STOCK WARNING: {qty} units left in pharmacy (<= 100 units). Consider reordering."
    else:
        stock_status = "available"
        warning_level = "none"
        warning_message = f"Sufficient stock available ({qty} units in inventory)."

    return {
        "found": True,
        "medicine_name": str(row['medicine_name']),
        "nickname": str(row.get('nickname', '')),
        "generic_name": str(row.get('generic_name', '')),
        "price": price,
        "quantity": qty,
        "unit": str(row.get('unit', 'Unit')),
        "category": str(row.get('category', 'General')),
        "stock_status": stock_status,
        "warning_level": warning_level,
        "warning_message": warning_message
    }

def check_medicine_availability(medicine_name, quantity):
    """
    Check medicine availability using the dataset.
    Returns: 'available', 'limited', 'low_stock', 'critical_stock', or 'out_of_stock'
    """
    med = find_medicine(medicine_name)
    if not med:
        return "out_of_stock"
    
    avail_qty = med["quantity"]
    if avail_qty < quantity:
        return "out_of_stock" if avail_qty <= 0 else "limited"
    
    # Return specific alert tier based on stock
    if avail_qty < 50:
        return "critical_stock"
    elif avail_qty <= 100:
        return "low_stock"
    return "available"

def get_medicine_price(medicine_name):
    """Returns unit price in INR (Rs)."""
    med = find_medicine(medicine_name)
    if not med:
        return 0.0
    return med["price"]

def decrement_medicine_stock(medicine_name, quantity):
    """
    Safely decrements the pharmacy stock upon dispensing a prescription.
    Updates the CSV in real-time.
    """
    try:
        df = _load_inventory()
        med = find_medicine(medicine_name)
        if not med:
            return None
        
        idx = df[df['medicine_name'] == med['medicine_name']].index
        if len(idx) > 0:
            current_qty = int(df.loc[idx[0], 'quantity'])
            new_qty = max(0, current_qty - int(quantity))
            df.loc[idx[0], 'quantity'] = new_qty
            
            # Update availability and stock_alert
            if new_qty <= 0:
                df.loc[idx[0], 'availability'] = 'out_of_stock'
                df.loc[idx[0], 'stock_alert'] = 'red'
            elif new_qty < 50:
                df.loc[idx[0], 'availability'] = 'critical_stock'
                df.loc[idx[0], 'stock_alert'] = 'red'
            elif new_qty <= 100:
                df.loc[idx[0], 'availability'] = 'low_stock'
                df.loc[idx[0], 'stock_alert'] = 'yellow'
            else:
                df.loc[idx[0], 'availability'] = 'available'
                df.loc[idx[0], 'stock_alert'] = 'normal'
                
            _save_inventory(df)
            return new_qty
    except Exception as e:
        print("Error decrementing stock:", e)
    return None

def search_medicines(query, limit=10):
    """Search helper for frontend autocomplete/dropdown."""
    df = _load_inventory()
    if df.empty or not query:
        return []
    
    q = str(query).strip().lower()
    match = df[
        df['medicine_name'].str.contains(q, case=False, na=False) |
        df['nickname'].astype(str).str.contains(q, case=False, na=False) |
        df['generic_name'].astype(str).str.contains(q, case=False, na=False)
    ].head(limit)
    
    results = []
    for _, row in match.iterrows():
        qty = int(row.get('quantity', 0))
        if qty < 50:
            warn = "red"
        elif qty <= 100:
            warn = "yellow"
        else:
            warn = "none"
            
        results.append({
            "medicine_name": str(row['medicine_name']),
            "nickname": str(row.get('nickname', '')),
            "generic_name": str(row.get('generic_name', '')),
            "price": float(row.get('price', 0.0)),
            "quantity": qty,
            "unit": str(row.get('unit', 'Unit')),
            "warning_level": warn
        })
    return results

def get_inventory_summary(limit=100, filter_alert=None):
    """Returns inventory list with counts for low stock (<=100) and critical stock (<50)."""
    df = _load_inventory()
    if df.empty:
        return {"items": [], "total_items": 0, "low_stock_count": 0, "critical_stock_count": 0}
        
    items = []
    low_count = 0
    crit_count = 0
    
    for _, row in df.iterrows():
        qty = int(row.get('quantity', 0))
        if qty < 50:
            warn = "red"
            crit_count += 1
        elif qty <= 100:
            warn = "yellow"
            low_count += 1
        else:
            warn = "none"
            
        if filter_alert and warn != filter_alert:
            continue
            
        if len(items) < limit:
            items.append({
                "medicine_name": str(row['medicine_name']),
                "nickname": str(row.get('nickname', '')),
                "generic_name": str(row.get('generic_name', '')),
                "price": float(row.get('price', 0.0)),
                "quantity": qty,
                "unit": str(row.get('unit', 'Unit')),
                "category": str(row.get('category', 'General')),
                "warning_level": warn
            })
            
    return {
        "items": items,
        "total_items": len(df),
        "low_stock_count": low_count,
        "critical_stock_count": crit_count
    }

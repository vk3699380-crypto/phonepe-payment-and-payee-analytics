import os
import json
import sqlite3
import subprocess
import pandas as pd

# Define paths
REPO_URL = "https://github.com/PhonePe/pulse.git"
CLONE_DIR = "phonepe_pulse"
DB_PATH = "phonepe.db"

def clone_repo():
    """Shallow clones the PhonePe Pulse repository if not already present."""
    if not os.path.exists(CLONE_DIR):
        print(f"Cloning PhonePe Pulse repository (shallow clone)...")
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, CLONE_DIR], check=True)
        print("Cloning complete.")
    else:
        print("PhonePe Pulse repository already exists. Skipping clone.")

def clean_state_name(state_folder):
    """Formats raw state folder names into user-friendly names."""
    parts = state_folder.split('-')
    cleaned_parts = []
    for part in parts:
        if part == '&':
            cleaned_parts.append('&')
        else:
            cleaned_parts.append(part.capitalize())
    state = ' '.join(cleaned_parts)
    # Special mappings
    state_mapping = {
        "Andaman & Nicobar Islands": "Andaman & Nicobar Islands",
        "Dadra & Nagar Haveli & Daman & Diu": "Dadra & Nagar Haveli & Daman & Diu",
        "Jammu & Kashmir": "Jammu & Kashmir",
    }
    return state_mapping.get(state, state)

def clean_district_name(district):
    """Standardizes district names by removing words like 'district' or extra spaces."""
    name = district.strip().lower()
    if name.endswith(" district"):
        name = name[:-9]
    return name.title()

def extract_aggregated_transactions():
    print("Extracting Aggregated Transactions...")
    path = os.path.join(CLONE_DIR, "data", "aggregated", "transaction", "country", "india", "state")
    data_list = []
    
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return pd.DataFrame()
        
    for state_folder in os.listdir(path):
        state_path = os.path.join(path, state_folder)
        if not os.path.isdir(state_path):
            continue
        state = clean_state_name(state_folder)
        
        for year_folder in os.listdir(state_path):
            year_path = os.path.join(state_path, year_folder)
            if not os.path.isdir(year_path):
                continue
            year = int(year_folder)
            
            for file_name in os.listdir(year_path):
                if not file_name.endswith(".json"):
                    continue
                quarter = int(file_name.split('.')[0])
                file_path = os.path.join(year_path, file_name)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                tx_data = json_data.get('data', {}).get('transactionData', [])
                if tx_data:
                    for item in tx_data:
                        name = item.get('name')
                        instruments = item.get('paymentInstruments', [])
                        for inst in instruments:
                            count = inst.get('count', 0)
                            amount = inst.get('amount', 0.0)
                            data_list.append({
                                'state': state,
                                'year': year,
                                'quarter': quarter,
                                'transaction_type': name,
                                'transaction_count': count,
                                'transaction_amount': amount
                            })
    return pd.DataFrame(data_list)

def extract_aggregated_users():
    print("Extracting Aggregated Users...")
    path = os.path.join(CLONE_DIR, "data", "aggregated", "user", "country", "india", "state")
    data_list = []
    
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return pd.DataFrame()

    for state_folder in os.listdir(path):
        state_path = os.path.join(path, state_folder)
        if not os.path.isdir(state_path):
            continue
        state = clean_state_name(state_folder)
        
        for year_folder in os.listdir(state_path):
            year_path = os.path.join(state_path, year_folder)
            if not os.path.isdir(year_path):
                continue
            year = int(year_folder)
            
            for file_name in os.listdir(year_path):
                if not file_name.endswith(".json"):
                    continue
                quarter = int(file_name.split('.')[0])
                file_path = os.path.join(year_path, file_name)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                user_data = json_data.get('data', {})
                agg_data = user_data.get('aggregatedData', {})
                registered_users = agg_data.get('registeredUsers', 0)
                app_opens = agg_data.get('appOpens', 0)
                
                devices = user_data.get('usersByDevice')
                if devices: # list of devices
                    for device in devices:
                        brand = device.get('brand')
                        count = device.get('count', 0)
                        percentage = device.get('percentage', 0.0)
                        data_list.append({
                            'state': state,
                            'year': year,
                            'quarter': quarter,
                            'brand': brand,
                            'user_count': count,
                            'percentage': percentage,
                            'registered_users': registered_users,
                            'app_opens': app_opens
                        })
                else:
                    data_list.append({
                        'state': state,
                        'year': year,
                        'quarter': quarter,
                        'brand': 'Unknown',
                        'user_count': 0,
                        'percentage': 0.0,
                        'registered_users': registered_users,
                        'app_opens': app_opens
                    })
    return pd.DataFrame(data_list)

def extract_map_transactions():
    print("Extracting Map Transactions...")
    path = os.path.join(CLONE_DIR, "data", "map", "transaction", "hover", "country", "india", "state")
    data_list = []
    
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return pd.DataFrame()

    for state_folder in os.listdir(path):
        state_path = os.path.join(path, state_folder)
        if not os.path.isdir(state_path):
            continue
        state = clean_state_name(state_folder)
        
        for year_folder in os.listdir(state_path):
            year_path = os.path.join(state_path, year_folder)
            if not os.path.isdir(year_path):
                continue
            year = int(year_folder)
            
            for file_name in os.listdir(year_path):
                if not file_name.endswith(".json"):
                    continue
                quarter = int(file_name.split('.')[0])
                file_path = os.path.join(year_path, file_name)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                hover_list = json_data.get('data', {}).get('hoverDataList', [])
                if hover_list:
                    for item in hover_list:
                        district = clean_district_name(item.get('name', ''))
                        metrics = item.get('metric', [])
                        for metric in metrics:
                            count = metric.get('count', 0)
                            amount = metric.get('amount', 0.0)
                            data_list.append({
                                'state': state,
                                'year': year,
                                'quarter': quarter,
                                'district': district,
                                'transaction_count': count,
                                'transaction_amount': amount
                            })
    return pd.DataFrame(data_list)

def extract_map_users():
    print("Extracting Map Users...")
    path = os.path.join(CLONE_DIR, "data", "map", "user", "hover", "country", "india", "state")
    data_list = []
    
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return pd.DataFrame()

    for state_folder in os.listdir(path):
        state_path = os.path.join(path, state_folder)
        if not os.path.isdir(state_path):
            continue
        state = clean_state_name(state_folder)
        
        for year_folder in os.listdir(state_path):
            year_path = os.path.join(state_path, year_folder)
            if not os.path.isdir(year_path):
                continue
            year = int(year_folder)
            
            for file_name in os.listdir(year_path):
                if not file_name.endswith(".json"):
                    continue
                quarter = int(file_name.split('.')[0])
                file_path = os.path.join(year_path, file_name)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                hover_data = json_data.get('data', {}).get('hoverData', {})
                if hover_data:
                    for district_raw, val in hover_data.items():
                        district = clean_district_name(district_raw)
                        reg_users = val.get('registeredUsers', 0)
                        app_opens = val.get('appOpens', 0)
                        data_list.append({
                            'state': state,
                            'year': year,
                            'quarter': quarter,
                            'district': district,
                            'registered_users': reg_users,
                            'app_opens': app_opens
                        })
    return pd.DataFrame(data_list)

def extract_top_transactions():
    print("Extracting Top Transactions...")
    path = os.path.join(CLONE_DIR, "data", "top", "transaction", "country", "india", "state")
    data_list = []
    
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return pd.DataFrame()

    for state_folder in os.listdir(path):
        state_path = os.path.join(path, state_folder)
        if not os.path.isdir(state_path):
            continue
        state = clean_state_name(state_folder)
        
        for year_folder in os.listdir(state_path):
            year_path = os.path.join(state_path, year_folder)
            if not os.path.isdir(year_path):
                continue
            year = int(year_folder)
            
            for file_name in os.listdir(year_path):
                if not file_name.endswith(".json"):
                    continue
                quarter = int(file_name.split('.')[0])
                file_path = os.path.join(year_path, file_name)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                top_data = json_data.get('data', {})
                
                # Extract districts
                districts = top_data.get('districts', [])
                if districts:
                    for dist in districts:
                        district = clean_district_name(str(dist.get('entityName') or ''))
                        metric = dist.get('metric', {})
                        data_list.append({
                            'state': state,
                            'year': year,
                            'quarter': quarter,
                            'level_type': 'District',
                            'level_name': district,
                            'transaction_count': metric.get('count', 0),
                            'transaction_amount': metric.get('amount', 0.0)
                        })
                            
                # Extract pincodes
                pincodes = top_data.get('pincodes', [])
                if pincodes:
                    for pin in pincodes:
                        pincode = str(pin.get('entityName') or '').strip()
                        metric = pin.get('metric', {})
                        data_list.append({
                            'state': state,
                            'year': year,
                            'quarter': quarter,
                            'level_type': 'Pincode',
                            'level_name': pincode,
                            'transaction_count': metric.get('count', 0),
                            'transaction_amount': metric.get('amount', 0.0)
                        })
    return pd.DataFrame(data_list)

def extract_top_users():
    print("Extracting Top Users...")
    path = os.path.join(CLONE_DIR, "data", "top", "user", "country", "india", "state")
    data_list = []
    
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return pd.DataFrame()

    for state_folder in os.listdir(path):
        state_path = os.path.join(path, state_folder)
        if not os.path.isdir(state_path):
            continue
        state = clean_state_name(state_folder)
        
        for year_folder in os.listdir(state_path):
            year_path = os.path.join(state_path, year_folder)
            if not os.path.isdir(year_path):
                continue
            year = int(year_folder)
            
            for file_name in os.listdir(year_path):
                if not file_name.endswith(".json"):
                    continue
                quarter = int(file_name.split('.')[0])
                file_path = os.path.join(year_path, file_name)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                top_data = json_data.get('data', {})
                
                # Extract districts
                districts = top_data.get('districts', [])
                if districts:
                    for dist in districts:
                        district = clean_district_name(dist.get('name', ''))
                        reg_users = dist.get('registeredUsers', 0)
                        data_list.append({
                            'state': state,
                            'year': year,
                            'quarter': quarter,
                            'level_type': 'District',
                            'level_name': district,
                            'registered_users': reg_users
                        })
                        
                # Extract pincodes
                pincodes = top_data.get('pincodes', [])
                if pincodes:
                    for pin in pincodes:
                        pincode = pin.get('name', '').strip()
                        reg_users = pin.get('registeredUsers', 0)
                        data_list.append({
                            'state': state,
                            'year': year,
                            'quarter': quarter,
                            'level_type': 'Pincode',
                            'level_name': pincode,
                            'registered_users': reg_users
                        })
    return pd.DataFrame(data_list)

def setup_sqlite(dfs):
    """Establishes connection to SQLite and inserts DataFrames into tables."""
    print("Setting up SQLite Database...")
    conn = sqlite3.connect(DB_PATH)
    
    for table_name, df in dfs.items():
        if df.empty:
            print(f"Skipping table {table_name} - DataFrame is empty.")
            continue
        print(f"Writing {len(df)} rows to table '{table_name}'...")
        # Write to SQL
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
    conn.commit()
    conn.close()
    print("Database setup complete.")

def main():
    clone_repo()
    
    # Extract data
    dfs = {
        "agg_trans": extract_aggregated_transactions(),
        "agg_user": extract_aggregated_users(),
        "map_trans": extract_map_transactions(),
        "map_user": extract_map_users(),
        "top_trans": extract_top_transactions(),
        "top_user": extract_top_users()
    }
    
    # Save to SQLite
    setup_sqlite(dfs)
    print("Preprocessing completed successfully!")

if __name__ == "__main__":
    main()

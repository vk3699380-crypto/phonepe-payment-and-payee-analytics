import os
import json
import sqlite3
from pathlib import Path

DB_FILE = "phonepe_pulse.db"
DATA_DIR = Path("pulse/data")

def format_state_name(state_raw):
    """Normalize directory names to readable state names."""
    if not state_raw:
        return "Unknown"
    state_raw = str(state_raw)
    if state_raw.lower() == "india":
        return "India"
    words = state_raw.replace("-", " ").split()
    formatted = []
    for w in words:
        if w == "and":
            formatted.append("and")
        elif w == "&":
            formatted.append("&")
        else:
            formatted.append(w.capitalize())
    return " ".join(formatted)

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop existing tables if any
    tables = [
        "agg_trans", "agg_user", "agg_user_device",
        "map_trans", "map_user",
        "top_trans_state", "top_trans_district", "top_trans_pincode",
        "top_user_state", "top_user_district", "top_user_pincode",
        "agg_insurance", "map_insurance",
        "top_insurance_state", "top_insurance_district", "top_insurance_pincode"
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    # Create tables
    # Aggregated Transaction
    cursor.execute("""
        CREATE TABLE agg_trans (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            transaction_type TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    # Aggregated User
    cursor.execute("""
        CREATE TABLE agg_user (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            registered_users INTEGER,
            app_opens INTEGER
        )
    """)

    # Aggregated User by Device
    cursor.execute("""
        CREATE TABLE agg_user_device (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            brand TEXT,
            count INTEGER,
            percentage REAL
        )
    """)

    # Map Transaction
    cursor.execute("""
        CREATE TABLE map_trans (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            district TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    # Map User
    cursor.execute("""
        CREATE TABLE map_user (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            district TEXT,
            registered_users INTEGER,
            app_opens INTEGER
        )
    """)

    # Top Transaction State
    cursor.execute("""
        CREATE TABLE top_trans_state (
            year INTEGER,
            quarter INTEGER,
            state TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    # Top Transaction District
    cursor.execute("""
        CREATE TABLE top_trans_district (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            district TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    # Top Transaction Pincode
    cursor.execute("""
        CREATE TABLE top_trans_pincode (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            pincode TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    # Top User State
    cursor.execute("""
        CREATE TABLE top_user_state (
            year INTEGER,
            quarter INTEGER,
            state TEXT,
            registered_users INTEGER
        )
    """)

    # Top User District
    cursor.execute("""
        CREATE TABLE top_user_district (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            district TEXT,
            registered_users INTEGER
        )
    """)

    # Top User Pincode
    cursor.execute("""
        CREATE TABLE top_user_pincode (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            pincode TEXT,
            registered_users INTEGER
        )
    """)

    # Aggregated Insurance
    cursor.execute("""
        CREATE TABLE agg_insurance (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            insurance_type TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    # Map Insurance
    cursor.execute("""
        CREATE TABLE map_insurance (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            district TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    # Top Insurance State
    cursor.execute("""
        CREATE TABLE top_insurance_state (
            year INTEGER,
            quarter INTEGER,
            state TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    # Top Insurance District
    cursor.execute("""
        CREATE TABLE top_insurance_district (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            district TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    # Top Insurance Pincode
    cursor.execute("""
        CREATE TABLE top_insurance_pincode (
            state TEXT,
            year INTEGER,
            quarter INTEGER,
            pincode TEXT,
            count INTEGER,
            amount REAL
        )
    """)

    conn.commit()
    conn.close()
    print("Database tables created successfully.")

def ingest_aggregated_transaction():
    print("Ingesting Aggregated Transactions...")
    conn = get_db_connection()
    cursor = conn.cursor()

    path_state = DATA_DIR / "aggregated" / "transaction" / "country" / "india" / "state"
    path_country = DATA_DIR / "aggregated" / "transaction" / "country" / "india"

    records = []

    # State-level
    if path_state.exists():
        for state_dir in path_state.iterdir():
            if not state_dir.is_dir():
                continue
            state_name = format_state_name(state_dir.name)
            for year_dir in state_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                year = int(year_dir.name)
                for q_file in year_dir.iterdir():
                    if not q_file.name.endswith(".json"):
                        continue
                    quarter = int(q_file.stem)
                    with open(q_file, 'r') as f:
                        data = json.load(f)
                    
                    tx_data = data.get("data", {}).get("transactionData", [])
                    if tx_data:
                        for item in tx_data:
                            tx_type = item.get("name")
                            instruments = item.get("paymentInstruments", [])
                            for inst in instruments:
                                count = inst.get("count")
                                amount = inst.get("amount")
                                records.append((state_name, year, quarter, tx_type, count, amount))

    # Country-level (India)
    for year_dir in path_country.iterdir():
        if not year_dir.is_dir() or year_dir.name == "state":
            continue
        year = int(year_dir.name)
        for q_file in year_dir.iterdir():
            if not q_file.name.endswith(".json"):
                continue
            quarter = int(q_file.stem)
            with open(q_file, 'r') as f:
                data = json.load(f)
            
            tx_data = data.get("data", {}).get("transactionData", [])
            if tx_data:
                for item in tx_data:
                    tx_type = item.get("name")
                    instruments = item.get("paymentInstruments", [])
                    for inst in instruments:
                        count = inst.get("count")
                        amount = inst.get("amount")
                        records.append(("India", year, quarter, tx_type, count, amount))

    cursor.executemany("INSERT INTO agg_trans VALUES (?, ?, ?, ?, ?, ?)", records)
    conn.commit()
    print(f"Aggregated Transactions: Loaded {len(records)} records.")
    conn.close()

def ingest_aggregated_user():
    print("Ingesting Aggregated Users...")
    conn = get_db_connection()
    cursor = conn.cursor()

    path_state = DATA_DIR / "aggregated" / "user" / "country" / "india" / "state"
    path_country = DATA_DIR / "aggregated" / "user" / "country" / "india"

    user_records = []
    device_records = []

    # State-level
    if path_state.exists():
        for state_dir in path_state.iterdir():
            if not state_dir.is_dir():
                continue
            state_name = format_state_name(state_dir.name)
            for year_dir in state_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                year = int(year_dir.name)
                for q_file in year_dir.iterdir():
                    if not q_file.name.endswith(".json"):
                        continue
                    quarter = int(q_file.stem)
                    with open(q_file, 'r') as f:
                        data = json.load(f)
                    
                    agg_data = data.get("data", {}).get("aggregated", {})
                    if agg_data:
                        reg_users = agg_data.get("registeredUsers")
                        app_opens = agg_data.get("appOpens")
                        user_records.append((state_name, year, quarter, reg_users, app_opens))
                    
                    device_data = data.get("data", {}).get("usersByDevice")
                    if device_data:
                        for device in device_data:
                            brand = device.get("brand")
                            count = device.get("count")
                            pct = device.get("percentage")
                            device_records.append((state_name, year, quarter, brand, count, pct))

    # Country-level (India)
    for year_dir in path_country.iterdir():
        if not year_dir.is_dir() or year_dir.name == "state":
            continue
        year = int(year_dir.name)
        for q_file in year_dir.iterdir():
            if not q_file.name.endswith(".json"):
                continue
            quarter = int(q_file.stem)
            with open(q_file, 'r') as f:
                data = json.load(f)
            
            agg_data = data.get("data", {}).get("aggregated", {})
            if agg_data:
                reg_users = agg_data.get("registeredUsers")
                app_opens = agg_data.get("appOpens")
                user_records.append(("India", year, quarter, reg_users, app_opens))
            
            device_data = data.get("data", {}).get("usersByDevice")
            if device_data:
                for device in device_data:
                    brand = device.get("brand")
                    count = device.get("count")
                    pct = device.get("percentage")
                    device_records.append(("India", year, quarter, brand, count, pct))

    cursor.executemany("INSERT INTO agg_user VALUES (?, ?, ?, ?, ?)", user_records)
    cursor.executemany("INSERT INTO agg_user_device VALUES (?, ?, ?, ?, ?, ?)", device_records)
    conn.commit()
    print(f"Aggregated Users: Loaded {len(user_records)} records.")
    print(f"User Devices: Loaded {len(device_records)} records.")
    conn.close()

def ingest_map_transaction():
    print("Ingesting Map Transactions...")
    conn = get_db_connection()
    cursor = conn.cursor()

    path_state = DATA_DIR / "map" / "transaction" / "hover" / "country" / "india" / "state"
    records = []

    if path_state.exists():
        for state_dir in path_state.iterdir():
            if not state_dir.is_dir():
                continue
            state_name = format_state_name(state_dir.name)
            for year_dir in state_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                year = int(year_dir.name)
                for q_file in year_dir.iterdir():
                    if not q_file.name.endswith(".json"):
                        continue
                    quarter = int(q_file.stem)
                    with open(q_file, 'r') as f:
                        data = json.load(f)
                    
                    hover_list = data.get("data", {}).get("hoverDataList", [])
                    if hover_list:
                        for hover in hover_list:
                            district_raw = hover.get("name")
                            if district_raw:
                                district = str(district_raw).replace("district", "").strip().title()
                            else:
                                district = "Unknown"
                            metrics = hover.get("metric", [])
                            for m in metrics:
                                count = m.get("count")
                                amount = m.get("amount")
                                records.append((state_name, year, quarter, district, count, amount))

    cursor.executemany("INSERT INTO map_trans VALUES (?, ?, ?, ?, ?, ?)", records)
    conn.commit()
    print(f"Map Transactions: Loaded {len(records)} records.")
    conn.close()

def ingest_map_user():
    print("Ingesting Map Users...")
    conn = get_db_connection()
    cursor = conn.cursor()

    path_state = DATA_DIR / "map" / "user" / "hover" / "country" / "india" / "state"
    records = []

    if path_state.exists():
        for state_dir in path_state.iterdir():
            if not state_dir.is_dir():
                continue
            state_name = format_state_name(state_dir.name)
            for year_dir in state_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                year = int(year_dir.name)
                for q_file in year_dir.iterdir():
                    if not q_file.name.endswith(".json"):
                        continue
                    quarter = int(q_file.stem)
                    with open(q_file, 'r') as f:
                        data = json.load(f)
                    
                    hover_data = data.get("data", {}).get("hoverData", {})
                    if hover_data:
                        for dist_raw, metrics in hover_data.items():
                            if dist_raw:
                                district = str(dist_raw).replace("district", "").strip().title()
                            else:
                                district = "Unknown"
                            reg_users = metrics.get("registeredUsers")
                            app_opens = metrics.get("appOpens")
                            records.append((state_name, year, quarter, district, reg_users, app_opens))

    cursor.executemany("INSERT INTO map_user VALUES (?, ?, ?, ?, ?, ?)", records)
    conn.commit()
    print(f"Map Users: Loaded {len(records)} records.")
    conn.close()

def ingest_top_transaction():
    print("Ingesting Top Transactions...")
    conn = get_db_connection()
    cursor = conn.cursor()

    path_state = DATA_DIR / "top" / "transaction" / "country" / "india" / "state"
    path_country = DATA_DIR / "top" / "transaction" / "country" / "india"

    state_records = []
    dist_records = []
    pin_records = []

    # State-level
    if path_state.exists():
        for state_dir in path_state.iterdir():
            if not state_dir.is_dir():
                continue
            state_name = format_state_name(state_dir.name)
            for year_dir in state_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                year = int(year_dir.name)
                for q_file in year_dir.iterdir():
                    if not q_file.name.endswith(".json"):
                        continue
                    quarter = int(q_file.stem)
                    with open(q_file, 'r') as f:
                        data = json.load(f)
                    
                    districts = data.get("data", {}).get("districts", [])
                    if districts:
                        for d in districts:
                            name = d.get("entityName")
                            if name:
                                dist_name = str(name).replace("district", "").strip().title()
                            else:
                                dist_name = "Unknown"
                            metric = d.get("metric", {})
                            count = metric.get("count")
                            amount = metric.get("amount")
                            dist_records.append((state_name, year, quarter, dist_name, count, amount))

                    pincodes = data.get("data", {}).get("pincodes", [])
                    if pincodes:
                        for p in pincodes:
                            pin = p.get("entityName")
                            if pin:
                                pin = str(pin).strip()
                            else:
                                pin = "Unknown"
                            metric = p.get("metric", {})
                            count = metric.get("count")
                            amount = metric.get("amount")
                            pin_records.append((state_name, year, quarter, pin, count, amount))

    # Country-level (India)
    for year_dir in path_country.iterdir():
        if not year_dir.is_dir() or year_dir.name == "state":
            continue
        year = int(year_dir.name)
        for q_file in year_dir.iterdir():
            if not q_file.name.endswith(".json"):
                continue
            quarter = int(q_file.stem)
            with open(q_file, 'r') as f:
                data = json.load(f)
            
            states = data.get("data", {}).get("states", [])
            if states:
                for s in states:
                    name = s.get("entityName")
                    if name:
                        s_name = format_state_name(name)
                    else:
                        s_name = "Unknown"
                    metric = s.get("metric", {})
                    count = metric.get("count")
                    amount = metric.get("amount")
                    state_records.append((year, quarter, s_name, count, amount))

            districts = data.get("data", {}).get("districts", [])
            if districts:
                for d in districts:
                    name = d.get("entityName")
                    if name:
                        dist_name = str(name).replace("district", "").strip().title()
                    else:
                        dist_name = "Unknown"
                    metric = d.get("metric", {})
                    count = metric.get("count")
                    amount = metric.get("amount")
                    dist_records.append(("India", year, quarter, dist_name, count, amount))

            pincodes = data.get("data", {}).get("pincodes", [])
            if pincodes:
                for p in pincodes:
                    pin = p.get("entityName")
                    if pin:
                        pin = str(pin).strip()
                    else:
                        pin = "Unknown"
                    metric = p.get("metric", {})
                    count = metric.get("count")
                    amount = metric.get("amount")
                    pin_records.append(("India", year, quarter, pin, count, amount))

    cursor.executemany("INSERT INTO top_trans_state VALUES (?, ?, ?, ?, ?)", state_records)
    cursor.executemany("INSERT INTO top_trans_district VALUES (?, ?, ?, ?, ?, ?)", dist_records)
    cursor.executemany("INSERT INTO top_trans_pincode VALUES (?, ?, ?, ?, ?, ?)", pin_records)
    conn.commit()
    print(f"Top Trans States: Loaded {len(state_records)} records.")
    print(f"Top Trans Districts: Loaded {len(dist_records)} records.")
    print(f"Top Trans Pincodes: Loaded {len(pin_records)} records.")
    conn.close()

def ingest_top_user():
    print("Ingesting Top Users...")
    conn = get_db_connection()
    cursor = conn.cursor()

    path_state = DATA_DIR / "top" / "user" / "country" / "india" / "state"
    path_country = DATA_DIR / "top" / "user" / "country" / "india"

    state_records = []
    dist_records = []
    pin_records = []

    # State-level
    if path_state.exists():
        for state_dir in path_state.iterdir():
            if not state_dir.is_dir():
                continue
            state_name = format_state_name(state_dir.name)
            for year_dir in state_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                year = int(year_dir.name)
                for q_file in year_dir.iterdir():
                    if not q_file.name.endswith(".json"):
                        continue
                    quarter = int(q_file.stem)
                    with open(q_file, 'r') as f:
                        data = json.load(f)
                    
                    districts = data.get("data", {}).get("districts", [])
                    if districts:
                        for d in districts:
                            name = d.get("entityName")
                            if name:
                                dist_name = str(name).replace("district", "").strip().title()
                            else:
                                dist_name = "Unknown"
                            reg_users = d.get("registeredUsers")
                            dist_records.append((state_name, year, quarter, dist_name, reg_users))

                    pincodes = data.get("data", {}).get("pincodes", [])
                    if pincodes:
                        for p in pincodes:
                            pin = p.get("entityName")
                            if pin:
                                pin = str(pin).strip()
                            else:
                                pin = "Unknown"
                            reg_users = p.get("registeredUsers")
                            pin_records.append((state_name, year, quarter, pin, reg_users))

    # Country-level (India)
    for year_dir in path_country.iterdir():
        if not year_dir.is_dir() or year_dir.name == "state":
            continue
        year = int(year_dir.name)
        for q_file in year_dir.iterdir():
            if not q_file.name.endswith(".json"):
                continue
            quarter = int(q_file.stem)
            with open(q_file, 'r') as f:
                data = json.load(f)
            
            states = data.get("data", {}).get("states", [])
            if states:
                for s in states:
                    name = s.get("entityName")
                    if name:
                        s_name = format_state_name(name)
                    else:
                        s_name = "Unknown"
                    reg_users = s.get("registeredUsers")
                    state_records.append((year, quarter, s_name, reg_users))

            districts = data.get("data", {}).get("districts", [])
            if districts:
                for d in districts:
                    name = d.get("entityName")
                    if name:
                        dist_name = str(name).replace("district", "").strip().title()
                    else:
                        dist_name = "Unknown"
                    reg_users = d.get("registeredUsers")
                    dist_records.append(("India", year, quarter, dist_name, reg_users))

            pincodes = data.get("data", {}).get("pincodes", [])
            if pincodes:
                for p in pincodes:
                    pin = p.get("entityName")
                    if pin:
                        pin = str(pin).strip()
                    else:
                        pin = "Unknown"
                    reg_users = p.get("registeredUsers")
                    pin_records.append(("India", year, quarter, pin, reg_users))

    cursor.executemany("INSERT INTO top_user_state VALUES (?, ?, ?, ?)", state_records)
    cursor.executemany("INSERT INTO top_user_district VALUES (?, ?, ?, ?, ?)", dist_records)
    cursor.executemany("INSERT INTO top_user_pincode VALUES (?, ?, ?, ?, ?)", pin_records)
    conn.commit()
    print(f"Top User States: Loaded {len(state_records)} records.")
    print(f"Top User Districts: Loaded {len(dist_records)} records.")
    print(f"Top User Pincodes: Loaded {len(pin_records)} records.")
    conn.close()

def ingest_insurance():
    print("Ingesting Insurance Data...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Aggregated Insurance
    agg_path_state = DATA_DIR / "aggregated" / "insurance" / "country" / "india" / "state"
    agg_path_country = DATA_DIR / "aggregated" / "insurance" / "country" / "india"
    agg_records = []

    if agg_path_state.exists():
        for state_dir in agg_path_state.iterdir():
            if not state_dir.is_dir():
                continue
            state_name = format_state_name(state_dir.name)
            for year_dir in state_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                year = int(year_dir.name)
                for q_file in year_dir.iterdir():
                    if not q_file.name.endswith(".json"):
                        continue
                    quarter = int(q_file.stem)
                    with open(q_file, 'r') as f:
                        data = json.load(f)
                    
                    tx_data = data.get("data", {}).get("transactionData", [])
                    if tx_data:
                        for item in tx_data:
                            ins_type = item.get("name")
                            instruments = item.get("paymentInstruments", [])
                            for inst in instruments:
                                count = inst.get("count")
                                amount = inst.get("amount")
                                agg_records.append((state_name, year, quarter, ins_type, count, amount))

    # Country level
    for year_dir in agg_path_country.iterdir():
        if not year_dir.is_dir() or year_dir.name == "state":
            continue
        year = int(year_dir.name)
        for q_file in year_dir.iterdir():
            if not q_file.name.endswith(".json"):
                continue
            quarter = int(q_file.stem)
            with open(q_file, 'r') as f:
                data = json.load(f)
            
            tx_data = data.get("data", {}).get("transactionData", [])
            if tx_data:
                for item in tx_data:
                    ins_type = item.get("name")
                    instruments = item.get("paymentInstruments", [])
                    for inst in instruments:
                        count = inst.get("count")
                        amount = inst.get("amount")
                        agg_records.append(("India", year, quarter, ins_type, count, amount))

    cursor.executemany("INSERT INTO agg_insurance VALUES (?, ?, ?, ?, ?, ?)", agg_records)

    # 2. Map Insurance
    map_path_state = DATA_DIR / "map" / "insurance" / "hover" / "country" / "india" / "state"
    map_records = []

    if map_path_state.exists():
        for state_dir in map_path_state.iterdir():
            if not state_dir.is_dir():
                continue
            state_name = format_state_name(state_dir.name)
            for year_dir in state_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                year = int(year_dir.name)
                for q_file in year_dir.iterdir():
                    if not q_file.name.endswith(".json"):
                        continue
                    quarter = int(q_file.stem)
                    with open(q_file, 'r') as f:
                        data = json.load(f)
                    
                    hover_list = data.get("data", {}).get("hoverDataList", [])
                    if hover_list:
                        for hover in hover_list:
                            district_raw = hover.get("name")
                            if district_raw:
                                district = str(district_raw).replace("district", "").strip().title()
                            else:
                                district = "Unknown"
                            metrics = hover.get("metric", [])
                            for m in metrics:
                                count = m.get("count")
                                amount = m.get("amount")
                                map_records.append((state_name, year, quarter, district, count, amount))

    cursor.executemany("INSERT INTO map_insurance VALUES (?, ?, ?, ?, ?, ?)", map_records)

    # 3. Top Insurance
    top_path_state = DATA_DIR / "top" / "insurance" / "country" / "india" / "state"
    top_path_country = DATA_DIR / "top" / "insurance" / "country" / "india"

    top_state_records = []
    top_dist_records = []
    top_pin_records = []

    if top_path_state.exists():
        for state_dir in top_path_state.iterdir():
            if not state_dir.is_dir():
                continue
            state_name = format_state_name(state_dir.name)
            for year_dir in state_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                year = int(year_dir.name)
                for q_file in year_dir.iterdir():
                    if not q_file.name.endswith(".json"):
                        continue
                    quarter = int(q_file.stem)
                    with open(q_file, 'r') as f:
                        data = json.load(f)
                    
                    districts = data.get("data", {}).get("districts", [])
                    if districts:
                        for d in districts:
                            name = d.get("entityName")
                            if name:
                                dist_name = str(name).replace("district", "").strip().title()
                            else:
                                dist_name = "Unknown"
                            metric = d.get("metric", {})
                            count = metric.get("count")
                            amount = metric.get("amount")
                            top_dist_records.append((state_name, year, quarter, dist_name, count, amount))

                    pincodes = data.get("data", {}).get("pincodes", [])
                    if pincodes:
                        for p in pincodes:
                            pin = p.get("entityName")
                            if pin:
                                pin = str(pin).strip()
                            else:
                                pin = "Unknown"
                            metric = p.get("metric", {})
                            count = metric.get("count")
                            amount = metric.get("amount")
                            top_pin_records.append((state_name, year, quarter, pin, count, amount))

    # Country level
    for year_dir in top_path_country.iterdir():
        if not year_dir.is_dir() or year_dir.name == "state":
            continue
        year = int(year_dir.name)
        for q_file in year_dir.iterdir():
            if not q_file.name.endswith(".json"):
                continue
            quarter = int(q_file.stem)
            with open(q_file, 'r') as f:
                data = json.load(f)
            
            states = data.get("data", {}).get("states", [])
            if states:
                for s in states:
                    name = s.get("entityName")
                    if name:
                        s_name = format_state_name(name)
                    else:
                        s_name = "Unknown"
                    metric = s.get("metric", {})
                    count = metric.get("count")
                    amount = metric.get("amount")
                    top_state_records.append((year, quarter, s_name, count, amount))

            districts = data.get("data", {}).get("districts", [])
            if districts:
                for d in districts:
                    name = d.get("entityName")
                    if name:
                        dist_name = str(name).replace("district", "").strip().title()
                    else:
                        dist_name = "Unknown"
                    metric = d.get("metric", {})
                    count = metric.get("count")
                    amount = metric.get("amount")
                    top_dist_records.append(("India", year, quarter, dist_name, count, amount))

            pincodes = data.get("data", {}).get("pincodes", [])
            if pincodes:
                for p in pincodes:
                    pin = p.get("entityName")
                    if pin:
                        pin = str(pin).strip()
                    else:
                        pin = "Unknown"
                    metric = p.get("metric", {})
                    count = metric.get("count")
                    amount = metric.get("amount")
                    top_pin_records.append(("India", year, quarter, pin, count, amount))

    cursor.executemany("INSERT INTO top_insurance_state VALUES (?, ?, ?, ?, ?)", top_state_records)
    cursor.executemany("INSERT INTO top_insurance_district VALUES (?, ?, ?, ?, ?, ?)", top_dist_records)
    cursor.executemany("INSERT INTO top_insurance_pincode VALUES (?, ?, ?, ?, ?, ?)", top_pin_records)

    conn.commit()
    print(f"Aggregated Insurance: Loaded {len(agg_records)} records.")
    print(f"Map Insurance: Loaded {len(map_records)} records.")
    print(f"Top Insurance States: Loaded {len(top_state_records)} records.")
    print(f"Top Insurance Districts: Loaded {len(top_dist_records)} records.")
    print(f"Top Insurance Pincodes: Loaded {len(top_pin_records)} records.")
    conn.close()

def build_indexes():
    print("Building database indexes for fast query performance...")
    conn = get_db_connection()
    cursor = conn.cursor()

    index_cmds = [
        "CREATE INDEX IF NOT EXISTS idx_agg_trans ON agg_trans (state, year, quarter, transaction_type)",
        "CREATE INDEX IF NOT EXISTS idx_agg_user ON agg_user (state, year, quarter)",
        "CREATE INDEX IF NOT EXISTS idx_agg_user_device ON agg_user_device (state, year, quarter, brand)",
        "CREATE INDEX IF NOT EXISTS idx_map_trans ON map_trans (state, year, quarter, district)",
        "CREATE INDEX IF NOT EXISTS idx_map_user ON map_user (state, year, quarter, district)",
        "CREATE INDEX IF NOT EXISTS idx_top_trans_state ON top_trans_state (year, quarter, state)",
        "CREATE INDEX IF NOT EXISTS idx_top_trans_district ON top_trans_district (state, year, quarter, district)",
        "CREATE INDEX IF NOT EXISTS idx_top_trans_pincode ON top_trans_pincode (state, year, quarter, pincode)",
        "CREATE INDEX IF NOT EXISTS idx_top_user_state ON top_user_state (year, quarter, state)",
        "CREATE INDEX IF NOT EXISTS idx_top_user_district ON top_user_district (state, year, quarter, district)",
        "CREATE INDEX IF NOT EXISTS idx_top_user_pincode ON top_user_pincode (state, year, quarter, pincode)",
        "CREATE INDEX IF NOT EXISTS idx_agg_insurance ON agg_insurance (state, year, quarter, insurance_type)",
        "CREATE INDEX IF NOT EXISTS idx_map_insurance ON map_insurance (state, year, quarter, district)",
        "CREATE INDEX IF NOT EXISTS idx_top_ins_state ON top_insurance_state (year, quarter, state)",
        "CREATE INDEX IF NOT EXISTS idx_top_ins_district ON top_insurance_district (state, year, quarter, district)",
        "CREATE INDEX IF NOT EXISTS idx_top_ins_pincode ON top_insurance_pincode (state, year, quarter, pincode)"
    ]

    for cmd in index_cmds:
        cursor.execute(cmd)
    
    conn.commit()
    conn.close()
    print("Database indexes successfully created.")

def verify_data():
    print("\n--- DATA INTEGRITY DIAGNOSTIC ---")
    conn = get_db_connection()
    cursor = conn.cursor()

    tables = [
        "agg_trans", "agg_user", "agg_user_device",
        "map_trans", "map_user",
        "top_trans_state", "top_trans_district", "top_trans_pincode",
        "top_user_state", "top_user_district", "top_user_pincode",
        "agg_insurance", "map_insurance",
        "top_insurance_state", "top_insurance_district", "top_insurance_pincode"
    ]

    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        print(f"Table '{t}': {count} rows")

    # Sample check for Karnataka 2023 Q1
    cursor.execute("SELECT SUM(amount), SUM(count) FROM agg_trans WHERE state='Karnataka' AND year=2023 AND quarter=1")
    amt, cnt = cursor.fetchone()
    print(f"\nVerification Query: Karnataka 2023 Q1 Aggregated Transaction Volume: {cnt}, Value: Rs. {amt:,.2f}" if amt else "\nVerification Query: No data found!")
    
    conn.close()
    print("---------------------------------")

if __name__ == "__main__":
    setup_database()
    ingest_aggregated_transaction()
    ingest_aggregated_user()
    ingest_map_transaction()
    ingest_map_user()
    ingest_top_transaction()
    ingest_top_user()
    ingest_insurance()
    build_indexes()
    verify_data()
    print("Data ingestion complete!")

import pandas as pd
import os

# --- CONFIG ---
OUTPUT_DIR = r"C:\Users\SKF\Documents\Translater\EC data\Output"
MASTER_FILE = os.path.join(OUTPUT_DIR, "AREGUDEM_MASTER_VOTERS.csv")

def combine_ward_data():
    all_wards = []
    
    # Matching your specific final filenames
    target_files = ["WARD_1_FINAL.csv", "WARD_2_FINAL.csv"]
    
    print("🚀 Starting Master Village Consolidation (V1.1)...")
    
    for filename in target_files:
        path = os.path.join(OUTPUT_DIR, filename)
        
        if os.path.exists(path):
            print(f"📦 Processing: {filename}")
            df = pd.read_csv(path)
            
            # --- FIX: COLUMN MAPPING ---
            # Based on V12.4, the column name is 'serial_no' and 'house_no'
            # If 'ward_no' is missing, we extract it from the filename or header
            if 'ward_no' not in df.columns and 'Ward' in df.columns:
                df = df.rename(columns={'Ward': 'ward_no'})
            
            # If still missing, we manually add it based on the filename
            if 'ward_no' not in df.columns:
                ward_id = re.search(r'\d+', filename).group()
                df['ward_no'] = int(ward_id)

            # 1. CLEANING: Remove Excel formula formatting
            # Converts '="1-1"' back to '1-1'
            if 'house_no' in df.columns:
                df['house_no'] = df['house_no'].astype(str).str.replace('="', '', regex=False).str.replace('"', '', regex=False)
            
            # 2. ENRICHMENT: Generate Family ID
            # Logic: W{ward}-H{house}
            df['family_id'] = "W" + df['ward_no'].astype(str) + "-H" + df['house_no'].astype(str)
            
            all_wards.append(df)
        else:
            print(f"⚠️ Warning: {filename} not found.")

    if all_wards:
        # 3. MERGING: Create the single master table
        master_df = pd.concat(all_wards, ignore_index=True)
        
        # 4. DATA TYPE CORRECTION: Ensure Serial No is Integer
        if 'serial_no' in master_df.columns:
            master_df['serial_no'] = pd.to_numeric(master_df['serial_no'], errors='coerce').fillna(0).astype(int)
        
        # 5. INTEGRITY: Drop duplicates across the whole village
        master_df = master_df.drop_duplicates(subset=['ward_no', 'serial_no'])
        
        # 6. EXPORT: Save for GCP Upload
        master_df.to_csv(MASTER_FILE, index=False)
        
        print("\n" + "="*40)
        print(f"✅ CONSOLIDATION COMPLETE")
        print(f"📊 Total Village Voters: {len(master_df)}")
        print(f"📂 Combined File: {MASTER_FILE}")
        print("="*40)
    else:
        print("❌ Error: No ward data was processed.")

if __name__ == "__main__":
    import re # Added for ward detection
    combine_ward_data()
import pandas as pd
import os

# --- CONFIG ---
# We use the absolute path to avoid 'FileNotFoundError'
BASE_DIR = r"C:\Users\SKF\Documents\Translater\EC data\Output"
INPUT_FILE = os.path.join(BASE_DIR, "AREGUDEM_MASTER_VOTERS.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "AREGUDEM_MASTER_FINAL_PROD.csv")

def polish_voter_data():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Could not find {INPUT_FILE}")
        print("Please check if the file is in the Output folder.")
        return

    print(f"📂 Loading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)

    # 1. FIX THE "JAN-1" ISSUE
    # Logic: Convert Excel date errors like '1-JAN' or 'JAN-1' back to '1-1'
    def fix_house_number(val):
        val_str = str(val).strip().upper()
        if 'JAN' in val_str:
            return '1-1'
        return val

    df['house_no'] = df['house_no'].apply(fix_house_number)

    # 2. STANDARDIZE GENDER
    # Standardizing to 'Male' and 'Female' for database consistency
    gender_map = {'M': 'Male', 'MALE': 'Male', 'F': 'Female', 'FEMALE': 'Female'}
    df['gender'] = df['gender'].str.upper().map(gender_map)

    # 3. REGENERATE FAMILY_ID
    # Ensuring family grouping works with the new '1-1' house numbers
    df['family_id'] = "W" + df['ward_no'].astype(str) + "-H" + df['house_no'].astype(str)

    # 4. DATA TYPE CLEANUP
    df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0).astype(int)
    df['serial_no'] = pd.to_numeric(df['serial_no'], errors='coerce').fillna(0).astype(int)

    # 5. SAVE FINAL PRODUCT
    df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n" + "="*40)
    print("✨ POLISHING SUCCESSFUL")
    print(f"✅ 'Jan-1' errors fixed to '1-1'")
    print(f"✅ Genders standardized to Male/Female")
    print(f"📂 Saved to: {OUTPUT_FILE}")
    print("="*40)

if __name__ == "__main__":
    polish_voter_data()
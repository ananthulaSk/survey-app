import pandas as pd
from sqlalchemy import create_engine
import urllib.parse  # Added for password safety
import os

# --- 1. SETTINGS ---
DB_USER = "postgres"
DB_PASS = "Akhanda@2"
DB_HOST = "34.180.55.125"
DB_NAME = "postgres"
CSV_PATH = r"C:\Users\SKF\Documents\Translater\EC data\Output\AREGUDEM_MASTER_FINAL_PROD.csv"

def run_migration():
    try:
        if not os.path.exists(CSV_PATH):
            print(f"❌ Error: File not found at {CSV_PATH}")
            return

        print(f"📂 Reading polished data...")
        df = pd.read_csv(CSV_PATH)
        
        # --- FIX: URL-encode the password to handle the '@' symbol ---
        safe_password = urllib.parse.quote_plus(DB_PASS)
        
        # Create the connection engine using the safe password
        conn_string = f'postgresql://{DB_USER}:{safe_password}@{DB_HOST}:5432/{DB_NAME}'
        engine = create_engine(conn_string)
        
        print(f"🚀 Pushing {len(df)} voters to GCP Cloud SQL...")
        
        # Upload to the 'voters' table
        df.to_sql('voters', engine, if_exists='append', index=False, method='multi')
        
        print("\n" + "="*40)
        print("🎉 SUCCESS: Your Village Data is now LIVE in the Cloud!")
        print("="*40)

    except Exception as e:
        print(f"❌ MIGRATION FAILED: {e}")
        print("\n💡 TIP: Ensure your IP is still added to 'Authorized Networks' in GCP.")

if __name__ == "__main__":
    run_migration()
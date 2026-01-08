import os

# Define your paths exactly as they are in your main script
creds_path = r'C:\Users\SKF\Documents\Translater\credentials\service_account_key.json'
pdf_path = r'C:\Users\SKF\Documents\Translater\EC survey\Input\1 ward.pdf'

print("--- Path Diagnostic Tool ---")

if os.path.exists(creds_path):
    print(f"✅ FOUND Credentials: {creds_path}")
else:
    print(f"❌ MISSING Credentials: {creds_path}")

if os.path.exists(pdf_path):
    print(f"✅ FOUND PDF File: {pdf_path}")
else:
    print(f"❌ MISSING PDF File: {pdf_path}")
    # Check if the folder exists at least
    folder = os.path.dirname(pdf_path)
    if os.path.exists(folder):
        print(f"   (Note: The folder '{folder}' exists, but the file is not inside it.)")
    else:
        print(f"   (Note: The folder '{folder}' does not even exist.)")
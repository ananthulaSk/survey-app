import os
import pandas as pd
import re
import json
import warnings
import io
import copy 
from pypdf import PdfReader, PdfWriter
from difflib import get_close_matches

# --- 1. MASTER SURNAMES (Aregudem Master List) ---
MASTER_SURNAMES = [
    "Manne", "Ananthula", "Kontham", "Konduri", "Savoji", "Baddam", 
    "Chinala", "Vaddagoni", "Gundeboina", "Palle", "Jala", "Sama", 
    "Palcham", "Polamoni", "Kolanu", "Ellanki", "Ganganaboina", 
    "Polaboina", "Padamati", "Gattigorla", "Sriramula", "Kotha", 
    "Pisati", "Arvapally", "Bommalapally"
]

# --- 2. SETUP ---
warnings.filterwarnings("ignore")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:\Users\SKF\Documents\Translater\credentials\service_account_key.json'

from vertexai.generative_models import GenerativeModel, Part
import vertexai

PROJECT_ID = "startest-oct" 
VERTEX_LOCATION = "us-central1" 
MODEL_NAME = "gemini-2.0-flash-001" 
INPUT_FILE = r"C:\Users\SKF\Documents\Translater\EC data\Input\1 ward.pdf"
OUTPUT_DIR = r"C:\Users\SKF\Documents\Translater\EC data\Output"

# Set to True only to see why #30 or #95 might be failing
DEBUG_RAW_JSON = False 

# --- 3. HARDENED UTILITIES ---

def get_clean_sl(sl_value):
    """Sanitizes '30.', '30)', or 'SL 30' into integer 30."""
    try:
        clean = re.sub(r'\D', '', str(sl_value))
        return int(clean) if clean else 0
    except: return 0

def crop_page_into_quadrants(reader, page_index):
    """Safely clones pages using copy.copy to prevent bleed."""
    page = reader.pages[page_index]
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    coords = [
        (0, h/2, w/2, h),       # 0: top-left
        (w/2, h/2, w, h),       # 1: top-right ⭐ (Target for #30)
        (0, 0, w/2, h/2),       # 2: bottom-left
        (w/2, 0, w, h/2)        # 3: bottom-right
    ]
    crops = []
    for (x1, y1, x2, y2) in coords:
        writer = PdfWriter()
        # SAFE CLONE: Prevents mutations from leaking across scans
        cloned = copy.copy(reader.pages[page_index]) 
        cloned.cropbox.lower_left = (x1, y1)
        cloned.cropbox.upper_right = (x2, y2)
        writer.add_page(cloned)
        stream = io.BytesIO(); writer.write(stream)
        crops.append(stream.getvalue())
    return crops

def neural_fetch(page_bytes, missing_range=None):
    vertexai.init(project=PROJECT_ID, location=VERTEX_LOCATION)
    model = GenerativeModel(MODEL_NAME)
    surname_str = ", ".join(MASTER_SURNAMES)
    context = f"TARGET: Missing {missing_range}. Extract even if partially visible." if missing_range else ""
    prompt = f"Extract voters to JSON list: sl, house_no, name, gender, age, rel_name, surname. Rules: 1. Surnames from: {surname_str}. 2. 'Kontham' is a surname. {context}"
    response = model.generate_content([Part.from_data(page_bytes, "application/pdf"), prompt], 
                                     generation_config={"response_mime_type": "application/json", "temperature": 0.1})
    try: 
        data = json.loads(response.text)
        if DEBUG_RAW_JSON: print("RAW RESPONSE:", json.dumps(data, indent=2))
        return data
    except: return []

# --- 4. EXECUTION ---

def run_v84_audit():
    print(f"🚀 Launching V8.4 Audit sniper...")
    reader = PdfReader(INPUT_FILE)
    official_target = 158 
    all_found_raw = []
    page_map = {}
    data_pages = list(range(1, len(reader.pages) - 1))

    # Phase 1: Full Scan
    for i in data_pages:
        print(f"🔍 Page {i+1} Scanning...")
        writer = PdfWriter(); writer.add_page(reader.pages[i])
        stream = io.BytesIO(); writer.write(stream)
        data = neural_fetch(stream.getvalue())
        if data:
            for item in data:
                sn = get_clean_sl(item.get('sl', 0))
                if sn > 0: all_found_raw.append(item); page_map[sn] = i

    def get_missing():
        found = {get_clean_sl(v['sl']) for v in all_found_raw if str(v.get('sl','')).strip()}
        return sorted(list(set(range(1, official_target + 1)) - found))

    # Phase 2: Block-Healing (Neighbor Logic)
    missing = get_missing()
    if missing:
        print(f"⚠️ Missing: {missing}. Healing neighbors...")
        target_pages = set()
        for sn in missing:
            idx = page_map.get(sn - 1) or page_map.get(sn + 1)
            if idx is not None:
                target_pages.update([max(1, idx - 1), idx, min(len(reader.pages)-2, idx + 1)])
        for idx in sorted(target_pages):
            writer = PdfWriter(); writer.add_page(reader.pages[idx])
            stream = io.BytesIO(); writer.write(stream)
            data = neural_fetch(stream.getvalue(), missing_range=missing)
            if data:
                for r in data:
                    if get_clean_sl(r.get('sl', 0)) in missing: all_found_raw.append(r); print(f"   ✨ HEALED #{r['sl']}")
            missing = get_missing()

    # PHASE 3: GRID-CROP RESCUE (The Surgical Move)
    if missing:
        print(f"🧨 FINAL SNIPER RESCUE: {missing}")
        priority = [1, 0, 2, 3] # Top-right priority for #30
        for sn in missing:
            page_idx = page_map.get(sn - 1) or page_map.get(sn + 1)
            if page_idx is None: continue
            quadrants = crop_page_into_quadrants(reader, page_idx)
            for q_idx in priority:
                data = neural_fetch(quadrants[q_idx], missing_range=[sn])
                found = False
                for r in data:
                    if get_clean_sl(r.get('sl', 0)) == sn:
                        all_found_raw.append(r); print(f"   🏆 RECOVERED #{sn}!"); found = True; break
                if found: break

    # Final Export Logic
    master_upper = [s.upper() for s in MASTER_SURNAMES]
    final_rows = []
    for v in all_found_raw:
        v_name, raw_s = str(v.get('name', '')).upper().strip(), str(v.get('surname', '')).upper().strip()
        match = get_close_matches(raw_s, master_upper, n=1, cutoff=0.6)
        final_s = match[0] if match else raw_s
        if final_s not in master_upper or final_s in ["REDDY", "RADHA"]:
            for s in master_upper:
                if s in v_name: final_s = s; break
        final_rows.append({'serial_no': get_clean_sl(v.get('sl', 0)), 'house_no': f"'{str(v.get('house_no', ''))}", 'voter_name': v_name, 'gender': str(v.get('gender', '')).upper(), 'age': str(v.get('age', '')), 'relation_name': str(v.get('rel_name', '')).upper().strip(), 'surname': final_s})

    df = pd.DataFrame(final_rows).drop_duplicates(subset=['serial_no']).sort_values(by='serial_no')
    df.to_csv(os.path.join(OUTPUT_DIR, "AREGUDEM_WARD_1_FINAL.csv"), index=False)
    print(f"\n========================================\n📊 REPORT: {len(df)} / {official_target}\n========================================")

if __name__ == "__main__":
    run_v84_audit()
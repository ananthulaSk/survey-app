import os, pandas as pd, re, json, warnings, io, time, copy
from pypdf import PdfReader, PdfWriter
from fpdf import FPDF
from difflib import get_close_matches
from vertexai.generative_models import GenerativeModel, Part
import vertexai

# --- 1. SYSTEM CONFIG ---
PROJECT_ID = "startest-oct" 
VERTEX_LOCATION = "us-central1" 
MODEL_NAME = "gemini-2.0-flash-001" 
INPUT_DIR = r"C:\Users\hariprasad ananthula\OneDrive\Documents\Translater\EC data\Input"
OUTPUT_DIR = r"C:\Users\hariprasad ananthula\OneDrive\Documents\Translater\EC data\Output"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:\Users\hariprasad ananthula\OneDrive\Documents\Translater\credentials\service_account_key.json'
warnings.filterwarnings("ignore")

audit_log = []

# --- 2. AUDIT PDF REPORT (HARDENED PRODUCTION VERSION) ---
class AuditPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Aregudem Village - Sequence Audit Report', 0, 1, 'C')
        self.ln(5)

    def draw_table(self, data):
        self.set_font('Arial', 'B', 10)
        w = {'ward': 15, 'range': 35, 'target': 20, 'actual': 20, 'missing': 75, 'status': 25}
        
        # Headers
        self.cell(w['ward'], 10, 'Ward', 1, 0, 'C')
        self.cell(w['range'], 10, 'Range', 1, 0, 'C')
        self.cell(w['target'], 10, 'Target', 1, 0, 'C')
        self.cell(w['actual'], 10, 'Actual', 1, 0, 'C')
        self.cell(w['missing'], 10, 'Missing Serials', 1, 0, 'C')
        self.cell(w['status'], 10, 'Status', 1, 1, 'C')
        
        self.set_font('Arial', '', 9)
        for e in data:
            missing_text = str(e['Missing'])
            line_height = 6

            # Native FPDF line calculation
            wrapped_lines = self.multi_cell(
                w['missing'], line_height, missing_text,
                border=0, align='L', split_only=True
            )
            row_height = max(10, line_height * len(wrapped_lines))

            # HARDENING: Page Break Safety Check
            if self.get_y() + row_height > self.page_break_trigger:
                self.add_page()
                # Redraw Headers on new page for clarity
                self.set_font('Arial', 'B', 10)
                self.cell(w['ward'], 10, 'Ward', 1, 0, 'C'); self.cell(w['range'], 10, 'Range', 1, 0, 'C')
                self.cell(w['target'], 10, 'Target', 1, 0, 'C'); self.cell(w['actual'], 10, 'Actual', 1, 0, 'C')
                self.cell(w['missing'], 10, 'Missing Serials', 1, 0, 'C'); self.cell(w['status'], 10, 'Status', 1, 1, 'C')
                self.set_font('Arial', '', 9)

            x, y = self.get_x(), self.get_y()

            # Render Data Cells
            self.cell(w['ward'], row_height, str(e['Ward']), 1, 0, 'C')
            self.cell(w['range'], row_height, f"{e['Start']}-{e['End']}", 1, 0, 'C')
            self.cell(w['target'], row_height, str(e['Target']), 1, 0, 'C')
            self.cell(w['actual'], row_height, str(e['Actual']), 1, 0, 'C')

            # Render Wrapped Text (XY Corrected)
            self.set_xy(x + w['ward'] + w['range'] + w['target'] + w['actual'], y)
            self.multi_cell(w['missing'], line_height, missing_text, 1, 'L')

            # Render Status
            self.set_xy(x + w['ward'] + w['range'] + w['target'] + w['actual'] + w['missing'], y)
            self.cell(w['status'], row_height, e['Status'], 1, 1, 'C')

# --- 3. DYNAMIC UTILITIES ---
def get_clean_sl(val):
    try:
        clean = re.sub(r'\D', '', str(val))
        return int(clean) if clean else 0
    except: return 0

def load_ward_config(pdf_filename):
    ward_id = re.search(r'\d+', pdf_filename).group()
    for f in os.listdir(INPUT_DIR):
        if f.endswith(".json") and ward_id in f:
            with open(os.path.join(INPUT_DIR, f), 'r', encoding='utf-8') as jfile:
                return json.load(jfile)
    return None

def neural_fetch(page_bytes, surnames, target_ids=None):
    vertexai.init(project=PROJECT_ID, location=VERTEX_LOCATION)
    model = GenerativeModel(MODEL_NAME)
    s_list = ", ".join(surnames)
    prompt = f"Extract voters to JSON list: sl, house_no, name, gender, age, rel_name, surname. Rules: 1. Full names. 2. Surnames from: {s_list}."
    try:
        res = model.generate_content([Part.from_data(page_bytes, "application/pdf"), prompt], 
                                     generation_config={"response_mime_type": "application/json", "temperature": 0.1})
        return json.loads(res.text)
    except: return []

# --- 4. THE SEQUENCE ENGINE ---
def process_ward(pdf_path):
    pdf_name = os.path.basename(pdf_path)
    config = load_ward_config(pdf_name)
    if not config: return

    # --- 🛠️ FIX START: Handle Single JSON with Multiple Wards ---
    # 1. Extract the Ward Number from the PDF Filename (e.g., "Lakkaram 1.pdf" -> 1)
    try:
        pdf_ward_id = int(re.search(r'\d+', pdf_name).group())
    except:
        print(f"⚠️ SKIPPING: Could not detect ward number in filename: {pdf_name}")
        return

    # 2. Check if JSON is the new "Single File" format (contains "wards" list)
    if "wards" in config:
        # Search the list for the ward matching the PDF
        target_data = next((w for w in config["wards"] if w["ward_no"] == pdf_ward_id), None)
        
        if not target_data:
            print(f"❌ ERROR: JSON loaded, but Ward {pdf_ward_id} data is missing inside it.")
            return
            
        # Unpack data from the specific ward object
        ward_no = target_data["ward_no"]
        total = target_data["total_electors"]
        surnames = target_data["surnames"]
    
    # 3. Fallback for Old Format (Flat JSON)
    elif "ward_no" in config:
        ward_no = config["ward_no"]
        total = config["total_electors"]
        surnames = config["surnames"]
    else:
        print("❌ ERROR: JSON format unrecognized (missing 'wards' list or 'ward_no' key).")
        return
    # --- 🛠️ FIX END ---

    print(f"\n🚀 PRODUCING WARD {ward_no}...")
    
    reader = PdfReader(pdf_path)
    all_raw, page_map = [], {}
    
    # Step 1: Detect Start Serial
    w_start = PdfWriter(); w_start.add_page(reader.pages[1])
    s_start = io.BytesIO(); w_start.write(s_start)
    first_data = neural_fetch(s_start.getvalue(), surnames)
    start_sn = min([get_clean_sl(x['sl']) for x in first_data if get_clean_sl(x['sl']) > 0]) if first_data else 1
    if start_sn < 1: start_sn = 1 
    end_sn = (start_sn + total) - 1 

    # Step 2: Main Scan
    for i in range(1, len(reader.pages) - 1):
        print(f"📦 Scanning Page {i+1}...", end="\r")
        writer = PdfWriter(); writer.add_page(copy.copy(reader.pages[i]))
        stream = io.BytesIO(); writer.write(stream)
        data = neural_fetch(stream.getvalue(), surnames)
        if data:
            for item in data:
                sn = get_clean_sl(item.get('sl', 0))
                if sn > 0: all_raw.append(item); page_map[sn] = i

    def get_missing_ids():
        found = {get_clean_sl(v['sl']) for v in all_raw if str(v.get('sl','')).strip()}
        return sorted(list(set(range(start_sn, end_sn + 1)) - found))

    # Step 3: Recovery Phase
    missing = get_missing_ids()
    if missing:
        for sn in missing:
            idx = page_map.get(sn-1) or page_map.get(sn+1)
            if idx:
                writer = PdfWriter(); writer.add_page(copy.copy(reader.pages[idx]))
                stream = io.BytesIO(); writer.write(stream)
                retry = neural_fetch(stream.getvalue(), surnames, target_ids=[sn])
                for r in retry:
                    if get_clean_sl(r.get('sl',0)) == sn: all_raw.append(r); break

    # Step 4: House No Fix & Save CSV
    final_rows = []
    for v in all_raw:
        house = str(v.get('house_no', '')).replace("'", "").strip()
        final_rows.append({
            'serial_no': get_clean_sl(v.get('sl', 0)), 'house_no': f'="{house}"',
            'voter_name': str(v.get('name','')).upper(), 'gender': str(v.get('gender','')).upper(),
            'age': str(v.get('age','')), 'relation_name': str(v.get('rel_name','')).upper(), 'surname': str(v.get('surname','')).upper()
        })

    df = pd.DataFrame(final_rows).drop_duplicates(subset=['serial_no']).sort_values(by='serial_no')
    df.to_csv(os.path.join(OUTPUT_DIR, f"WARD_{ward_no}_FINAL.csv"), index=False)
    
    audit_log.append({
        'Ward': ward_no, 'Start': start_sn, 'End': end_sn, 'Target': total, 
        'Actual': len(df), 'Missing': get_missing_ids() if len(df) < total else "NONE",
        'Status': "SUCCESS" if len(df) == total else "GAP"
    })



    
if __name__ == "__main__":
    for f in sorted(os.listdir(INPUT_DIR)):
        if f.endswith(".pdf"): process_ward(os.path.join(INPUT_DIR, f))
    
    if audit_log:
        pdf = AuditPDF(); pdf.add_page(); pdf.draw_table(audit_log)
        pdf.output(os.path.join(OUTPUT_DIR, "Village_Sequence_Audit.pdf"))
        print(f"\n🌟 HARDENED PRODUCTION AUDIT GENERATED: Village_Sequence_Audit.pdf")
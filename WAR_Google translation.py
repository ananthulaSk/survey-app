import json
import os
import sys
import time
import traceback

# Google Cloud imports
from google.cloud import translate_v3beta1 as translate
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# --- Configuration ---
INPUT_DIR = r"C:\Users\SKF\Documents\Translater\Eng to Telugu Trans\Input"
OUTPUT_DIR = r"C:\Users\SKF\Documents\Translater\Eng to Telugu Trans\Output"
TARGET_LANGUAGE_CODE = 'te'  # Telugu
PROJECT_ID = 'quixotic-dynamo-469111-j2' # Keep your project ID
LOCATION = 'global'

# OAuth config
CLIENT_SECRETS_FILE = 'client_secrets.json'
TOKEN_FILE = 'token.json'
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

# Chunk size
QUESTIONS_PER_CHUNK = 4

# Create output folder if not exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Created output directory: {OUTPUT_DIR}")

# --- OAuth 2.0 Authentication ---
def authenticate_with_oauth():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing existing credentials...")
            creds.refresh(Request())
        else:
            print("No valid credentials found. Launching browser for authorization...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"Credentials saved to {TOKEN_FILE}")

    return creds

# Initialize client
try:
    credentials = authenticate_with_oauth()
    translate_client = translate.TranslationServiceClient(credentials=credentials)
    parent_resource = f"projects/{PROJECT_ID}/locations/{LOCATION}"
    print("Google Cloud Translation service initialized.")
except FileNotFoundError:
    print(f"Error: {CLIENT_SECRETS_FILE} not found. Make sure it's in the same directory as the script.")
    sys.exit(1)
except Exception as e:
    print(f"Error initializing Translation service: {e}")
    sys.exit(1)

# --- Translation Function ---
def translate_batch_of_texts(texts_to_translate, target_language):
    if not texts_to_translate:
        return []

    try:
        print(f"  Translating {len(texts_to_translate)} texts to '{target_language}'...")
        request = {
            'parent': parent_resource,
            'contents': texts_to_translate,
            'target_language_code': target_language,
            'source_language_code': 'en',
            'mime_type': 'text/plain'
        }
        response = translate_client.translate_text(request=request)
        time.sleep(0.5)

        translated_texts = [t.translated_text for t in response.translations]
        return translated_texts

    except Exception as e:
        print(f"Translation API error: {e}")
        traceback.print_exc()
        return texts_to_translate

# --- File Processing ---
def translate_json_file_chunked(input_filepath, output_filepath):
    print(f"\nProcessing: {os.path.basename(input_filepath)}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'mcqs' not in data or not isinstance(data['mcqs'], list):
            print(f"  Skipped: No 'mcqs' found in {os.path.basename(input_filepath)}")
            return

        original_mcqs = data['mcqs']
        
        # Remove the supporting_evidence key from the input data before processing
        print("  Sanitizing input: Removing 'supporting_evidence' key...")
        for mcq in original_mcqs:
            if 'supporting_evidence' in mcq:
                del mcq['supporting_evidence']

        translated_mcqs = [mcq.copy() for mcq in original_mcqs]
        total_questions = len(original_mcqs)

        for i in range(0, total_questions, QUESTIONS_PER_CHUNK):
            chunk_start_idx = i
            chunk_end_idx = min(i + QUESTIONS_PER_CHUNK, total_questions)
            current_mcq_chunk_original = original_mcqs[chunk_start_idx:chunk_end_idx]
            current_mcq_chunk_translated = translated_mcqs[chunk_start_idx:chunk_end_idx]

            print(f"  Translating Q {chunk_start_idx + 1} to {chunk_end_idx} of {total_questions}...")

            texts_to_translate_info = []

            for local_idx, mcq_original in enumerate(current_mcq_chunk_original):
                # Handles 'question', 'assertion', 'reason', 'explanation'
                for key in ['question', 'assertion', 'reason', 'explanation']:
                    if key in mcq_original and mcq_original.get(key):
                         texts_to_translate_info.append((mcq_original.get(key, ''), local_idx, key, None))

                # Handles 'options' dictionary
                if 'options' in mcq_original and isinstance(mcq_original['options'], dict):
                    for key, value in mcq_original['options'].items():
                        texts_to_translate_info.append((str(value), local_idx, 'option', key))
                
                # Handles lists like 'statements', 'column_a', 'column_b'
                for col_key in ['column_a', 'column_b', 'statements']:
                     if col_key in mcq_original and isinstance(mcq_original[col_key], list):
                        for item_idx, item in enumerate(mcq_original[col_key]):
                             texts_to_translate_info.append((str(item), local_idx, col_key, item_idx))
                
                # Handles 'list1' and 'list2' dictionaries
                for list_key in ['list1', 'list2']:
                    if list_key in mcq_original and isinstance(mcq_original[list_key], dict):
                        for key, value in mcq_original[list_key].items():
                            texts_to_translate_info.append((str(value), local_idx, list_key, key))

            original_texts_list = [item[0] for item in texts_to_translate_info]
            translated_texts_list = translate_batch_of_texts(original_texts_list, TARGET_LANGUAGE_CODE)

            for idx_in_list, (_, local_mcq_idx, field_type, field_key) in enumerate(texts_to_translate_info):
                translated_mcq_item = current_mcq_chunk_translated[local_mcq_idx]
                translated_text = translated_texts_list[idx_in_list]

                if field_type in ['question', 'assertion', 'reason', 'explanation']:
                    translated_mcq_item[field_type] = translated_text
                elif field_type == 'option':
                    if 'options' not in translated_mcq_item: translated_mcq_item['options'] = {}
                    translated_mcq_item['options'][field_key] = translated_text
                elif field_type in ['column_a', 'column_b', 'statements']:
                    translated_mcq_item[field_type][field_key] = translated_text
                elif field_type in ['list1', 'list2']:
                    if field_type not in translated_mcq_item: translated_mcq_item[field_type] = {}
                    translated_mcq_item[field_type][field_key] = translated_text
        
        data['mcqs'] = translated_mcqs

        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Saved: {os.path.basename(output_filepath)}")

    except json.JSONDecodeError as e:
        print(f"JSON Error in {os.path.basename(input_filepath)}: {e}")
    except Exception as e:
        print(f"Error processing {os.path.basename(input_filepath)}: {e}")
        traceback.print_exc()

# --- Main Execution ---
print(f"Starting translation...\nFrom: {INPUT_DIR}\nTo: {OUTPUT_DIR}\nChunk size: {QUESTIONS_PER_CHUNK}")

json_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
if not json_files:
    print("\nNo JSON files found in the input directory. Please check the path.")
else:
    for filename in json_files:
        input_filepath = os.path.join(INPUT_DIR, filename)
        output_filename = filename.replace('.json', '_telugu.json')
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)
        translate_json_file_chunked(input_filepath, output_filepath)
    print("\n✅ All files processed.")
import torch
import json
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit.processor import IndicProcessor

# Define the model name and target language
MODEL_NAME = "ai4bharat/indictrans2-en-indic-1B"
TARGET_LANGUAGE = "tel_Telu"  # 'tel_Telu' is the code for Telugu

# 1. Load the pre-trained model and tokenizer
print("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, trust_remote_code=True)

# 2. Force the model to use the CPU for compatibility
DEVICE = "cpu"
model.to(DEVICE)

# 3. Create a processor for pre- and post-processing
ip = IndicProcessor()

# 4. Load your JSON data from a file
# Make sure your file is named 'your_mcqs.json' and is uploaded to Colab
try:
    with open('your_mcqs.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    print("JSON data loaded successfully.")
except FileNotFoundError:
    print("Error: 'your_mcqs.json' not found. Please upload your file.")
    exit()

# 5. Extract the text you want to translate
text_to_translate = [json_data["question"]] + json_data["options"]

# 6. Pre-process the text for the model
batch = ip.preprocess_batch(text_to_translate, src_lang='eng_Latn', tgt_lang=TARGET_LANGUAGE)

# 7. Tokenize and run the model for translation (Updated line for compatibility)
# This uses a simple search and should run without errors on a CPU
inputs = tokenizer(batch, truncation=True, padding="longest", return_tensors="pt", return_attention_mask=True).to(DEVICE)
with torch.no_grad():
    generated_tokens = model.generate(**inputs, num_beams=1, max_length=256)

# 8. Decode the tokens back to human-readable text
decoded_tokens = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)

# 9. Post-process the translated text
translated_text = ip.postprocess_batch(decoded_tokens, src_lang='eng_Latn', tgt_lang=TARGET_LANGUAGE)

# 10. Update your JSON data with the translated text
json_data["question_telugu"] = translated_text[0]
json_data["options_telugu"] = translated_text[1:]

# 11. Print the final translated JSON
print("\nTranslated JSON:")
print(json.dumps(json_data, indent=4, ensure_ascii=False))
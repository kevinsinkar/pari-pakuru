import json
import os

base_path = r'c:\Users\k1s4l\OneDrive\Desktop\Repos\pari-pakuru\Dictionary Data'
missed_path = os.path.join(base_path, 'skiri_to_english_parsed_MISSED.json')
parsed_path = os.path.join(base_path, 'skiri_to_english_parsed.json')

with open(missed_path, 'r', encoding='utf-8') as f:
    missed_data = json.load(f)

with open(parsed_path, 'r', encoding='utf-8') as f:
    parsed_data = json.load(f)

def get_word_details(entry):
    skiri = entry.get('skiri_term') or entry.get('skiri_entry_word')
    page = entry.get('entry_metadata', {}).get('page_number')
    return f"{skiri} (Page {page})"

print(f"Total entries in MISSED: {len(missed_data)}")

print("\n--- FIRST 20 ENTRIES OF MISSED ---")
for i in range(20):
    print(f"{i}: {get_word_details(missed_data[i])}")

print("\n--- LAST 20 ENTRIES OF MISSED ---")
for i in range(len(missed_data)-20, len(missed_data)):
    print(f"{i}: {get_word_details(missed_data[i])}")

print("\n--- FIRST 10 ENTRIES OF PARSED ---")
for i in range(10):
    print(f"{i}: {get_word_details(parsed_data[i])}")

# Let's check for an anchor point in the middle of MISSED that isn't 'Unknown'
for i in range(len(missed_data)):
    word = missed_data[i].get('skiri_term') or missed_data[i].get('skiri_entry_word')
    if word and word != "Unknown":
        print(f"\nPotential Anchor - MISSED[{i}]: {get_word_details(missed_data[i])}")
        
        # Search for this in PARSED
        for j, p_entry in enumerate(parsed_data):
            p_word = p_entry.get('skiri_term') or p_entry.get('skiri_entry_word')
            if p_word == word:
                print(f"Match found in PARSED[{j}]: {get_word_details(p_entry)}")

import json
import os

base_path = r'c:\Users\k1s4l\OneDrive\Desktop\Repos\pari-pakuru\Dictionary Data'
missed_path = os.path.join(base_path, 'english_to_skiri_complete_missed.json')
complete_path = os.path.join(base_path, 'english_to_skiri_complete.json')

with open(missed_path, 'r', encoding='utf-8') as f:
    missed_data = json.load(f)

with open(complete_path, 'r', encoding='utf-8') as f:
    complete_data = json.load(f)

print('--- LAST 20 ENTRIES OF COMPLETE ---')
for entry in complete_data[-20:]:
    print(f"Word: {entry.get('english_entry_word')}, Page: {entry.get('entry_metadata', {}).get('page_number')}")

print('\n--- FIRST 20 ENTRIES OF MISSED ---')
for entry in missed_data[:20]:
    print(f"Word: {entry.get('english_entry_word')}, Page: {entry.get('entry_metadata', {}).get('page_number')}")

print('\n--- LAST 20 ENTRIES OF MISSED ---')
for entry in missed_data[-20:]:
    print(f"Word: {entry.get('english_entry_word')}, Page: {entry.get('entry_metadata', {}).get('page_number')}")

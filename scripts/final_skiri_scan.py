import json
import os

base_path = r'c:\Users\k1s4l\OneDrive\Desktop\Repos\pari-pakuru\Dictionary Data'
missed_path = os.path.join(base_path, 'skiri_to_english_parsed_MISSED.json')
parsed_path = os.path.join(base_path, 'skiri_to_english_parsed.json')

with open(missed_path, 'r', encoding='utf-8') as f:
    missed_data = json.load(f)

with open(parsed_path, 'r', encoding='utf-8') as f:
    parsed_data = json.load(f)

def get_entry_repr(entry):
    subentries = entry.get('subentries', [])
    if subentries:
        p1 = subentries[0].get('part_I', {})
        if p1:
            return f"Term: {p1.get('skiri_term')}, Gloss: {p1.get('english_glosses')}"
    return "Unknown/Empty Entry"

print("--- MISSED UNIQUE SEQUENCE ---")
for i in range(len(missed_data)):
    print(f"{i}: {get_entry_repr(missed_data[i])}")

print("\n--- PARSED SEQUENCE AROUND INDEX 0 ---")
for i in range(10):
    print(f"{i}: {get_entry_repr(parsed_data[i])}")

print("\n--- PARSED SEQUENCE AROUND INDEX 25-30 (Page 2 zone) ---")
for i in range(25, 35):
    print(f"{i}: {get_entry_repr(parsed_data[i])}")

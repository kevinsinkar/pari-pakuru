import json
import os

base_path = r'c:\Users\k1s4l\OneDrive\Desktop\Repos\pari-pakuru\Dictionary Data'
missed_path = os.path.join(base_path, 'skiri_to_english_parsed_MISSED.json')
parsed_path = os.path.join(base_path, 'skiri_to_english_parsed.json')

with open(missed_path, 'r', encoding='utf-8') as f:
    missed_data = json.load(f)

with open(parsed_path, 'r', encoding='utf-8') as f:
    parsed_data = json.load(f)

def get_word(entry):
    # Depending on schema, it might be 'skiri_entry_word' or similar
    # Based on file naming, let's look at the keys
    return entry.get('skiri_entry_word') or entry.get('english_entry_word') or "Unknown"

parsed_words = [get_word(e) for e in parsed_data]
missed_words = [get_word(e) for e in missed_data]

print('--- FIRST 5 ENTRIES OF PARSED ---')
for i in range(min(5, len(parsed_words))):
    print(f"{i}: {parsed_words[i]}")

print('\n--- LAST 5 ENTRIES OF PARSED ---')
for i in range(max(0, len(parsed_words)-5), len(parsed_words)):
    print(f"{i}: {parsed_words[i]}")

print('\n--- FIRST 5 ENTRIES OF MISSED ---')
for i in range(min(5, len(missed_words))):
    print(f"{i}: {missed_words[i]}")

print('\n--- ELEMENTS FROM MISSED FOUND IN PARSED ---')
found = []
for i, word in enumerate(missed_words):
    if word in parsed_words:
        # Check if it appears multiple times or find closest match in sequence
        indices = [j for j, x in enumerate(parsed_words) if x == word]
        found.append((i, word, indices))

if found:
    print(f"Found {len(found)} overlapping words.")
    for i, word, idxs in found[:15]:
        print(f"Missed index {i}: '{word}' -> Parsed indices {idxs}")
else:
    print("No overlapping words found.")

import json
import os

base_path = r'c:\Users\k1s4l\OneDrive\Desktop\Repos\pari-pakuru\Dictionary Data'
missed_path = os.path.join(base_path, 'english_to_skiri_complete_missed.json')
complete_path = os.path.join(base_path, 'english_to_skiri_complete.json')

with open(missed_path, 'r', encoding='utf-8') as f:
    missed_data = json.load(f)

with open(complete_path, 'r', encoding='utf-8') as f:
    complete_data = json.load(f)

complete_words = [entry.get('english_entry_word') for entry in complete_data]
missed_words = [entry.get('english_entry_word') for entry in missed_data]

print('--- FIRST 5 ENTRIES OF COMPLETE ---')
for i in range(min(5, len(complete_words))):
    print(f"{i}: {complete_words[i]}")

print('\n--- ELEMENTS FROM MISSED FOUND IN COMPLETE ---')
found = []
for i, word in enumerate(missed_words):
    if word in complete_words:
        found.append((i, word, complete_words.index(word)))

if found:
    print(f"Found {len(found)} overlapping words.")
    # Show search result for first and last few
    for i, word, idx in found[:10]:
        print(f"Missed index {i}: '{word}' -> Complete index {idx}")
    print("...")
    for i, word, idx in found[-10:]:
        print(f"Missed index {i}: '{word}' -> Complete index {idx}")
else:
    print("No overlapping words found.")

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
    return entry.get('skiri_entry_word') or entry.get('english_entry_word') or "Unknown"

print(f"Total missed: {len(missed_data)}")
print(f"Total parsed: {len(parsed_data)}")

# Looking for specific sequence of words in MISSED that matches sequence in PARSED
# We need to find where the tail of MISSED matches a section of PARSED

# Check words from MISSED index 15 onwards (to avoid 'Unknown' at the start)
# Looking for a solid anchor point
for i in range(15, len(missed_data)):
    word = get_word(missed_data[i])
    if word != "Unknown":
        print(f"Index {i}: {word}")

# Re-run a more targeted overlap check
# Let's check the last 10 entries of missed and search for them as a sequence in parsed
tail_size = 10
missed_tail_words = [get_word(e) for e in missed_data[-tail_size:]]
print(f"\nSearching for tail sequence in parsed: {missed_tail_words}")

parsed_words = [get_word(e) for e in parsed_data]

potential_indices = []
for i in range(len(parsed_words) - tail_size + 1):
    if parsed_words[i:i+tail_size] == missed_tail_words:
        potential_indices.append(i)

print(f"Found tail sequence at parsed indices: {potential_indices}")

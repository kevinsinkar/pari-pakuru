import json
import os

base_path = r'c:\Users\k1s4l\OneDrive\Desktop\Repos\pari-pakuru\Dictionary Data'
missed_path = os.path.join(base_path, 'skiri_to_english_parsed_MISSED.json')
parsed_path = os.path.join(base_path, 'skiri_to_english_parsed.json')

with open(missed_path, 'r', encoding='utf-8') as f:
    missed_data = json.load(f)

with open(parsed_path, 'r', encoding='utf-8') as f:
    parsed_data = json.load(f)

# Use full JSON dumps to find sequence matches
def get_raw_sequence(data_slice):
    return [json.dumps(e, sort_keys=True) for e in data_slice]

# Search for the tail of MISSED in PARSED
tail_len = 10
missed_tail = get_raw_sequence(missed_data[-tail_len:])
parsed_all = get_raw_sequence(parsed_data)

found_at = []
for i in range(len(parsed_all) - tail_len + 1):
    if parsed_all[i:i+tail_len] == missed_tail:
        found_at.append(i)

print(f"Tail of MISSED found in PARSED at indices: {found_at}")

# Also check for front overlap
front_len = 5
missed_front = get_raw_sequence(missed_data[:front_len])
found_front = []
for i in range(len(parsed_all) - front_len + 1):
    if parsed_all[i:i+front_len] == missed_front:
        found_front.append(i)

print(f"Front of MISSED found in PARSED at indices: {found_front}")

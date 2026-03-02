import json
import os

base_path = r'c:\Users\k1s4l\OneDrive\Desktop\Repos\pari-pakuru\Dictionary Data'
missed_path = os.path.join(base_path, 'skiri_to_english_parsed_MISSED.json')
parsed_path = os.path.join(base_path, 'skiri_to_english_parsed.json')

with open(missed_path, 'r', encoding='utf-8') as f:
    missed_data = json.load(f)

with open(parsed_path, 'r', encoding='utf-8') as f:
    parsed_data = json.load(f)

# Sort based on page number
merged_data = missed_data + parsed_data
merged_data.sort(key=lambda x: x.get('entry_metadata', {}).get('page_number', 0))

# Result file
output_path = os.path.join(base_path, 'skiri_to_english_complete.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(merged_data, f, indent=2, ensure_ascii=False)

print(f"Successfully merged {len(missed_data)} missed and {len(parsed_data)} parsed entries into {output_path}")
print(f"Total entries: {len(merged_data)}")

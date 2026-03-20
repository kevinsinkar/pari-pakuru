import json
import os

base_path = r'c:\Users\k1s4l\OneDrive\Desktop\Repos\pari-pakuru\Dictionary Data'
missed_path = os.path.join(base_path, 'english_to_skiri_complete_missed.json')
complete_path = os.path.join(base_path, 'english_to_skiri_complete.json')

with open(missed_path, 'r', encoding='utf-8') as f:
    missed_data = json.load(f)

with open(complete_path, 'r', encoding='utf-8') as f:
    complete_data = json.load(f)

# Entries from missed_data[0:27] are missing in complete_data
# They belong between complete_data[1786] and complete_data[1787]
# complete_data[1786] is 'edge, on the'
# complete_data[1787] is 'embrace'

missing_entries = missed_data[:27]
print(f"Number of missing entries to insert: {len(missing_entries)}")
print(f"First missing entry: {missing_entries[0].get('english_entry_word')}")
print(f"Last missing entry: {missing_entries[-1].get('english_entry_word')}")

# Identify the entry just before the insertion point in complete
print(f"Entry at index 1786 in complete: {complete_data[1786].get('english_entry_word')}")
print(f"Entry at index 1787 in complete: {complete_data[1787].get('english_entry_word')}")

# Create new merged data
new_complete_data = complete_data[:1787] + missing_entries + complete_data[1787:]

# Verify the sequence around the insertion point
print("\n--- VERIFYING MERGE ---")
start_v = 1784
end_v = 1787 + 27 + 3
for i in range(start_v, end_v):
    print(f"{i}: {new_complete_data[i].get('english_entry_word')}")

# Write to the destination file
output_path = complete_path
# Create a backup first just in case
backup_path = complete_path + ".backup"
os.replace(complete_path, backup_path)
print(f"\nCreated backup at {backup_path}")

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(new_complete_data, f, indent=2, ensure_ascii=False)

print(f"Successfully merged into {output_path}")
print(f"Original length: {len(complete_data)}")
print(f"New length: {len(new_complete_data)}")

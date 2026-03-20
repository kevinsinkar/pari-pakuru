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
    keys = list(entry.keys())
    metadata = entry.get('entry_metadata', {})
    subentries = entry.get('subentries', [])
    
    first_subentry_ii = None
    if subentries and len(subentries) > 0:
        part_ii = subentries[0].get('part_II', {})
        if part_ii and 'paradigmatic_forms' in part_ii:
            forms = part_ii.get('paradigmatic_forms', [])
            if forms:
                first_subentry_ii = forms[0].get('skiri_form')

    first_subentry_iii = None
    if subentries and len(subentries) > 0:
        part_iii = subentries[0].get('part_III', {})
        if part_iii and 'cross_references' in part_iii:
            refs = part_iii.get('cross_references', [])
            if refs:
                first_subentry_iii = refs[0].get('english_term')

    return {
        "page": metadata.get('page_number'),
        "first_form": first_subentry_ii,
        "first_xref": first_subentry_iii
    }

print("--- MISSED SAMPLES ---")
for i in [0, 10, 20, 30, 40, 50, 54]:
    if i < len(missed_data):
        print(f"Index {i}: {get_entry_repr(missed_data[i])}")

print("\n--- PARSED SAMPLES ---")
for i in [0, 500, 1000, 2000, 3000, 4000, 4217]:
    if i < len(parsed_data):
        print(f"Index {i}: {get_entry_repr(parsed_data[i])}")

# Let's see if we can find a matching form/xref sequence
# Looking for Page 2 entries in PARSED
print("\n--- Entires in PARSED with Page 2 ---")
count = 0
for i, entry in enumerate(parsed_data):
    if entry.get('entry_metadata', {}).get('page_number') == 2:
        count += 1
        if count < 10:
            print(f"Found Page 2 at index {i}: {get_entry_repr(entry)}")
print(f"Total entries with Page 2 mapping in Parsed: {count}")

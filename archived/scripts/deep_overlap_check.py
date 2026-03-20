import json
import os

base_path = r'c:\Users\k1s4l\OneDrive\Desktop\Repos\pari-pakuru\Dictionary Data'
missed_path = os.path.join(base_path, 'skiri_to_english_parsed_MISSED.json')
parsed_path = os.path.join(base_path, 'skiri_to_english_parsed.json')

with open(missed_path, 'r', encoding='utf-8') as f:
    missed_data = json.load(f)

with open(parsed_path, 'r', encoding='utf-8') as f:
    parsed_data = json.load(f)

def entry_hash(entry):
    # Create a string representation of the entry that includes key structural data
    # We'll use the first subentry's part_I and part_II skiri strings if they exist
    parts = []
    subentries = entry.get('subentries', [])
    if subentries:
        p1 = subentries[0].get('part_I', {})
        if p1:
            parts.append(str(p1.get('skiri_term')))
            parts.append(str(p1.get('english_glosses')))
        p2 = subentries[0].get('part_II', {})
        if p2:
            parts.append(str(p2.get('paradigmatic_forms')))
        p3 = subentries[0].get('part_III', {})
        if p3:
            parts.append(str(p3.get('cross_references')))
    return "|".join(parts)

# Let's map entries in missed_data to PARSED indices
found_matches = []
for i, m_entry in enumerate(missed_data):
    m_h = entry_hash(m_entry)
    for j, p_entry in enumerate(parsed_data):
        if entry_hash(p_entry) == m_h:
            found_matches.append((i, j))
            break

if found_matches:
    print(f"Found {len(found_matches)} matches.")
    # Show first 10 matches
    for m_idx, p_idx in found_matches[:10]:
        print(f"MISSED[{m_idx}] is in PARSED at index {p_idx}")
    # Show last 10 matches
    if len(found_matches) > 10:
        print("...")
        for m_idx, p_idx in found_matches[-10:]:
            print(f"MISSED[{m_idx}] is in PARSED at index {p_idx}")
else:
    print("No structural matches found between MISSED and PARSED.")

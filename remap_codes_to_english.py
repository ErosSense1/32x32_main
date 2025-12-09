#!/usr/bin/env python3
"""
remap_codes_to_english.py

Remap the first 31 non-REVEAL_ALL keys in `codes.json` to a list of
English love-related words (UPPERCASE, no spaces). Preserve `REVEAL_ALL`.

Usage:
  py -3 remap_codes_to_english.py
"""
import json, os, sys

CODES = 'codes.json'
if not os.path.exists(CODES):
    print('Error: codes.json not found')
    sys.exit(1)

with open(CODES, 'r', encoding='utf-8') as f:
    data = json.load(f)

# English love-related words (31)
english = [
    'DARLING','SWEETHEART','LOVE','BELOVED','HONEY','DEAR','TREASURE','MYLOVE',
    'BABY','SUNSHINE','MOONLIGHT','BLOSSOM','HEART','ADORABLE','PRECIOUS','ANGEL',
    'PRINCE','PRINCESS','SNUGGLE','CUPID','SWEETIE','LOVER','BEAU','HONEYBUN',
    'LOVEBUG','SOULMATE','CHERUB','MYDARLING','TENDER','SWEETS','BAE'
]

# Determine keys to remap (preserve order)
keys = [k for k in data.keys() if k != 'REVEAL_ALL']
new = {}
used = set()
count = 0
for k in keys:
    if count < len(english):
        new_key = english[count]
        new[new_key] = data[k]
        used.add(k)
        count += 1
    else:
        # for any remaining keys beyond 31, keep them as-is (unlikely)
        new[k] = data[k]

# Ensure REVEAL_ALL preserved
if 'REVEAL_ALL' in data:
    new['REVEAL_ALL'] = data['REVEAL_ALL']
else:
    # create REVEAL_ALL by flattening remaining arrays in original order
    flat = []
    for k in keys:
        arr = data.get(k) or []
        flat.extend(arr)
    new['REVEAL_ALL'] = flat

with open(CODES, 'w', encoding='utf-8') as f:
    json.dump(new, f, indent=2, ensure_ascii=False)

print(f'Wrote {CODES} with {len(new)} keys (including REVEAL_ALL)')

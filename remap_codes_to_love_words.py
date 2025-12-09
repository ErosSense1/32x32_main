#!/usr/bin/env python3
"""
remap_codes_to_love_words.py

Read `codes.json`, remap the first 31 ROW_* keys to Spanish love-word keys,
and overwrite `codes.json` with the new mapping. Keeps `REVEAL_ALL` key.
"""
import json
import os

CODES = 'codes.json'

LOVE_KEYS = [
    'AMOR','MIAMOR','CORAZON','CARINO','QUERIDA','TESORO','PRECIOSO','AMORCITO',
    'PRINCESA','REY','NENA','NENE','LUZ','VIDA','ALMA','BELLA','BELLO','SUENO',
    'DULZURA','MIREINA','MIREY','CIELO','ESTRELLA','ENCANTO','TESORILLO',
    'BOMBON','MISOL','CORAZONCITO','MIMOS','BESITOS','MI_AMORCITO'
]

ROW_LABELS = [chr(ord('A')+i) for i in range(26)] + list('abcdef')

if not os.path.exists(CODES):
    print('Error: codes.json not found in this folder')
    raise SystemExit(1)

with open(CODES, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Prefer rows in `rows` key if file is in the pixels-style structure
# but if codes.json already contains ROW_* keys, use them directly.
new_map = {}

# If file has top-level ROW_* keys, use that mapping
existing_keys = [k for k in data.keys() if k.upper().startswith('ROW_')]
if existing_keys:
    # sort by ROW_A, ROW_B, ... using ROW_<letter> pattern
    def row_sort_key(k):
        lab = k.split('_',1)[1] if '_' in k else k
        return lab
    existing_keys = sorted(existing_keys, key=row_sort_key)
    # map first 31 existing ROW_* to LOVE_KEYS
    for i, love in enumerate(LOVE_KEYS):
        if i < len(existing_keys):
            src = existing_keys[i]
            new_map[love] = data.get(src, [])
        else:
            new_map[love] = []
else:
    # try to find rows inside a 'rows' object
    rows = data.get('rows') or data.get('Rows') or data.get('ROWS')
    if not rows:
        print('No ROW_* keys and no "rows" object found — aborting')
        raise SystemExit(1)
    for i, love in enumerate(LOVE_KEYS):
        if i < len(ROW_LABELS):
            row_label = ROW_LABELS[i]
            key = row_label
            # rows may use uppercase labels
            candidate = rows.get(key.upper()) or rows.get(key)
            new_map[love] = candidate or []
        else:
            new_map[love] = []

# copy REVEAL_ALL if present (keep as-is), otherwise create by flattening
if 'REVEAL_ALL' in data:
    new_map['REVEAL_ALL'] = data['REVEAL_ALL']
else:
    flat = []
    for r in ROW_LABELS:
        arr = None
        # existing data may be under rows
        if isinstance(data.get('rows'), dict):
            arr = data['rows'].get(r) or data['rows'].get(r.upper())
        # or in original mapping under ROW_<r>
        if not arr:
            arr = data.get(f'ROW_{r}') or data.get(f'ROW_{r.upper()}')
        if arr:
            flat.extend(arr)
    new_map['REVEAL_ALL'] = flat

with open(CODES, 'w', encoding='utf-8') as f:
    json.dump(new_map, f, indent=2, ensure_ascii=False)

print(f'Wrote {CODES} with {len(new_map)} keys (including REVEAL_ALL)')

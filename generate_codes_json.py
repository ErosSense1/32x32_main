#!/usr/bin/env python3
"""
generate_codes_json.py

Generate `codes.json` mapping 31 secret codes to each row of
`as_pixels_codes_32x32.json` and a master code `REVEAL_ALL` that contains
all codes in row-major order.

Usage:
  py -3 generate_codes_json.py

This writes `codes.json` into the same folder.
"""
import json
import os

INPUT = 'as_pixels_codes_32x32.json'
OUTPUT = 'codes.json'

ROW_LABELS = [chr(ord('A')+i) for i in range(26)] + list('abcdef')

if __name__ == '__main__':
    if not os.path.exists(INPUT):
        print(f'Error: {INPUT} not found in current directory')
        raise SystemExit(1)

    with open(INPUT, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = data.get('rows', {})

    codes_map = {}

    # create 31 row codes: use rows A..Z and a..e (31 rows)
    keys = []
    for r in ROW_LABELS[:31]:
        key = f'ROW_{r.upper()}'
        keys.append((key, r))

    for key, r in keys:
        arr = rows.get(r, [])
        codes_map[key] = arr

    # master code: flatten rows in ROW_LABELS order (only rows present)
    flat = []
    for r in ROW_LABELS:
        arr = rows.get(r)
        if arr:
            flat.extend(arr)
    codes_map['REVEAL_ALL'] = flat

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(codes_map, f, indent=2, ensure_ascii=False)

    print(f'Wrote {OUTPUT} with {len(codes_map)} keys (including REVEAL_ALL)')

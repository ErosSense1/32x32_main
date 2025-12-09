#!/usr/bin/env python3
"""
extract_codes.py

Read a pixel-code JSON like `as_pixels_codes_32x32.json` and write
an extracted JSON containing a flat `codes` array and a `map` of
code => { size, row, col, color }.

Usage:
  py -3 extract_codes.py as_pixels_codes_32x32.json

"""
import argparse
import json
import os
import re

ROW_LABELS = [chr(ord('A')+i) for i in range(26)] + list('abcdef')

CODE_RE = re.compile(r"^\s*(\d+)([A-Za-z])(\d+)_?([A-Za-z0-9#]+)\s*$")


def parse_code(code):
    m = CODE_RE.match(code)
    if not m:
        return None
    size = int(m.group(1))
    row = m.group(2)
    col = int(m.group(3))
    color = m.group(4)
    return {
        'size': size,
        'row': row,
        'col': col,
        'color': color,
    }


def extract(input_path, output_path=None):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = data.get('rows')
    if not rows or not isinstance(rows, dict):
        raise ValueError("Input JSON must contain a top-level 'rows' object")

    codes = []
    mapping = {}

    # iterate rows in ROW_LABELS order where present, otherwise in dict order
    seen = set()
    for r in ROW_LABELS:
        if r in rows:
            row_codes = rows[r]
            for c in row_codes:
                codes.append(c)
                parsed = parse_code(c)
                mapping[c] = parsed
            seen.add(r)

    # add any remaining rows that were not in ROW_LABELS
    for r, row_codes in rows.items():
        if r in seen:
            continue
        for c in row_codes:
            codes.append(c)
            parsed = parse_code(c)
            mapping[c] = parsed

    out = {
        'source': os.path.basename(input_path),
        'count': len(codes),
        'codes': codes,
        'map': mapping,
    }

    if not output_path:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"{base}_codes.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    return output_path


def main():
    parser = argparse.ArgumentParser(description='Extract codes from pixel-code JSON into a separate JSON')
    parser.add_argument('input', help='Path to pixel-code JSON')
    parser.add_argument('--output', '-o', help='Output JSON path (optional)')
    args = parser.parse_args()

    out = extract(args.input, args.output)
    print(f'Wrote extracted codes JSON: {out}')

if __name__ == '__main__':
    main()

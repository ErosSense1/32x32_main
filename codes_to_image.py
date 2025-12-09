#!/usr/bin/env python3
"""
codes_to_image.py

Read a pixel-code JSON (same format produced by `image_to_codes.py`) and
recreate the image (PNG) using a basic color palette mapping.

Usage:
  py -3 codes_to_image.py as_pixels_codes_32x32.json --output recreated.png

"""
import argparse
import json
import os
from PIL import Image

ROW_LABELS = [
    *[chr(ord('A') + i) for i in range(26)],
    'a', 'b', 'c', 'd', 'e', 'f'
]

BASE_BASIC_COLORS = {
    'black': (0, 0, 0, 255),
    'white': (255, 255, 255, 255),
    'red': (255, 0, 0, 255),
    'green': (0, 255, 0, 255),
    'blue': (0, 0, 255, 255),
    'yellow': (255, 255, 0, 255),
    'magenta': (255, 0, 255, 255),
    'cyan': (0, 255, 255, 255),
    'gray': (128, 128, 128, 255),
    'transparent': (0, 0, 0, 0),
}


def parse_code(code):
    """Parse a single pixel code like '32A10white' into (size,row_label,col,color_name)."""
    # read numeric size prefix
    i = 0
    while i < len(code) and code[i].isdigit():
        i += 1
    size = int(code[:i])
    if i >= len(code):
        raise ValueError(f"Invalid code: {code}")
    row_label = code[i]
    i += 1
    # read column digits
    j = i
    while j < len(code) and code[j].isdigit():
        j += 1
    col = int(code[i:j])
    color_name = code[j:]
    # accept an optional leading underscore separating position and color
    if color_name.startswith('_'):
        color_name = color_name[1:]
    return size, row_label, col, color_name


def codes_json_to_image(input_path, output_path=None):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = data.get('rows')
    if not rows:
        raise ValueError('JSON missing "rows" key')

    # determine size from first code encountered
    first_row = next(iter(rows.values()))
    if not first_row:
        raise ValueError('No pixel codes found')
    size, _, _, _ = parse_code(first_row[0])

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    px = img.load()

    for row_label, codes in rows.items():
        if row_label not in ROW_LABELS:
            continue
        y = ROW_LABELS.index(row_label)
        for code in codes:
            _, rlabel, col, color_name = parse_code(code)
            if rlabel != row_label:
                # inconsistent label in this code; skip
                continue
            x = col
            # Accept color as hex (RRGGBB or RRGGBBAA) with or without '#',
            # otherwise fall back to named basic colors.
            cn = str(color_name).strip()
            def hex_to_rgba(s):
                # Normalize and accept many common variants:
                # - with or without '#'
                # - 3-digit (#RGB) -> expand to RRGGBB
                # - 4-digit (#RGBA) -> expand to RRGGBBAA
                # - 6-digit (#RRGGBB)
                # - 8-digit (#RRGGBBAA)
                if not s:
                    return None
                raw = str(s).strip()
                # keep only hex chars
                import re
                hexchars = re.sub(r'[^0-9A-Fa-f]', '', raw)
                if len(hexchars) == 3:
                    # e.g. '0FA' -> '00FFAA'
                    r = int(hexchars[0] * 2, 16)
                    g = int(hexchars[1] * 2, 16)
                    b = int(hexchars[2] * 2, 16)
                    return (r, g, b, 255)
                if len(hexchars) == 4:
                    r = int(hexchars[0] * 2, 16)
                    g = int(hexchars[1] * 2, 16)
                    b = int(hexchars[2] * 2, 16)
                    a = int(hexchars[3] * 2, 16)
                    return (r, g, b, a)
                if len(hexchars) >= 6:
                    # prefer first 6 or first 8 if available
                    r = int(hexchars[0:2], 16)
                    g = int(hexchars[2:4], 16)
                    b = int(hexchars[4:6], 16)
                    if len(hexchars) >= 8:
                        a = int(hexchars[6:8], 16)
                    else:
                        a = 255
                    return (r, g, b, a)
                return None

            rgba = hex_to_rgba(cn)
            if rgba is None:
                rgba = BASE_BASIC_COLORS.get(cn.lower())
            if rgba is None:
                # unknown name, default to magenta to highlight
                rgba = (255, 0, 255, 255)
            if 0 <= x < size and 0 <= y < size:
                px[x, y] = rgba

    if not output_path:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"{base}.png"

    img.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Recreate image from pixel-code JSON')
    # make input optional so we can open a file dialog when omitted
    parser.add_argument('input', nargs='?', help='Path to pixel-code JSON')
    parser.add_argument('--gui', action='store_true', help='Open a file dialog to choose the JSON')
    parser.add_argument('--output', '-o', help='Output PNG path (optional)')
    args = parser.parse_args()

    input_path = args.input
    if not input_path or args.gui:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            filetypes = [("JSON files", "*.json"), ("All files", "*")]
            selected = filedialog.askopenfilename(title="Select pixel-code JSON", filetypes=filetypes)
            root.destroy()
            if selected:
                input_path = selected
        except Exception as e:
            print(f"GUI file dialog failed or unavailable: {e}")

    if not input_path:
        parser.print_help()
        print("\nNo input JSON selected. Exiting.")
        return

    out = codes_json_to_image(input_path, args.output)
    print(f'Wrote image: {out}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
image_to_codes.py

Read a small pixel-image (default 32x32) and convert each pixel into
the project's pixel-code format: <size><Row><Col><HexColor>

Example code for a pixel at row 'H', column 11 with RGB red 255,0,0:
  32H11FF0000

Output JSON structure matches existing `pixels.json` style:
  { "rows": { "A": ["32A0FF0000", ...], ... } }

Usage:
    py -3 image_to_codes.py path/to/image.png --size 32 --output image_pixels_codes.json

Requires: Pillow (pip install pillow)
"""
import argparse
import json
import os
from PIL import Image


def recommend_size_from_image(img):
    """Very small 'AI' heuristic: recommend a target size based on image dimensions.

    Prefer exact square sizes if image already matches one of the allowed sizes.
    Otherwise pick the nearest size from the supported set [8,16,24,32].
    """
    w, h = img.size
    allowed = [8, 16, 24, 32]
    if w == h and w in allowed:
        return w
    target = max(w, h)
    return min(allowed, key=lambda s: abs(s - target))


ROW_LABELS = [
    # 26 uppercase A-Z
    *[chr(ord('A') + i) for i in range(26)],
    # then lowercase a-f to get up to 32 rows total
    'a', 'b', 'c', 'd', 'e', 'f'
]


def color_to_hex(r, g, b, a=None):
    # legacy function kept for compatibility but not used
    if a is None or a == 255:
        return f"{r:02X}{g:02X}{b:02X}"
    return f"{r:02X}{g:02X}{b:02X}{a:02X}"


def color_to_hex(r, g, b, a=None):
    if a is None or a == 255:
        return f"{r:02X}{g:02X}{b:02X}"
    return f"{r:02X}{g:02X}{b:02X}{a:02X}"


# Note: we intentionally emit full hexadecimal color codes per-pixel
# (RRGGBB or RRGGBBAA) so downstream tools get exact colors instead of
# simplified names.


def image_to_codes(path, size=32, output_path=None, resize=True):
    img = Image.open(path).convert('RGBA')
    w, h = img.size
    if (w, h) != (size, size) and resize:
        img = img.resize((size, size), resample=Image.NEAREST)

    rows = {}
    if size > len(ROW_LABELS):
        raise ValueError(f"Requested size {size} is too large for available row labels ({len(ROW_LABELS)})")

    for y in range(size):
        row_label = ROW_LABELS[y]
        codes = []
        for x in range(size):
            r, g, b, a = img.getpixel((x, y))
            hexcol = color_to_hex(r, g, b, a if a != 255 else None)
            # separate color with an underscore for clarity: e.g. 32A0_FFFFFF
            code = f"{size}{row_label}{x}_{hexcol}"
            codes.append(code)
        rows[row_label] = codes

    out = {"rows": rows}
    if not output_path:
        base = os.path.splitext(os.path.basename(path))[0]
        output_path = f"{base}_pixels_codes_{size}x{size}.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert a pixel image into pixel-code JSON.",
        epilog=("Example: py -3 image_to_codes.py path/to/image.png "
                "--size 32 --output image_pixels_codes.json")
    )
    # Make the positional image argument optional so we can open a file dialog when omitted
    parser.add_argument('image', nargs='?', help='Path to input image (PNG/GIF/JPG).')
    parser.add_argument('--gui', action='store_true', help='Open a file dialog to select the image')
    parser.add_argument('--size', '-s', type=int, default=32, help='Target width/height (default 32).')
    parser.add_argument('--output', '-o', help='Output JSON path (optional).')
    parser.add_argument('--no-resize', dest='resize', action='store_false', help='Do not resize input image; require exact size.')
    args = parser.parse_args()

    image_path = args.image

    # If no image provided or user explicitly requested GUI, open a file dialog
    if not image_path or args.gui:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            filetypes = [("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All files", "*")]
            selected = filedialog.askopenfilename(title="Select image", filetypes=filetypes)
            root.destroy()
            if selected:
                image_path = selected
        except Exception as e:
            print(f"GUI file dialog failed or unavailable: {e}")

    if not image_path:
        parser.print_help()
        print("\nNo image selected. Exiting.")
        return

    # Basic AI: open the image and suggest a recommended target size
    try:
        preview_img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        raise

    recommended = recommend_size_from_image(preview_img)
    chosen_size = args.size
    # If user left size at default 32 and AI suggests something different, ask to accept
    if args.size == 32 and recommended != 32:
        accepted = None
        # If tkinter is available, prefer a graphical yes/no dialog
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            accepted = messagebox.askyesno("Size suggestion",
                                           f"Detected image size {preview_img.size}. Recommend using {recommended}x{recommended}. Use recommended size?")
            root.destroy()
        except Exception:
            pass

        if accepted is None:
            resp = input(f"Detected image size {preview_img.size}. Recommend using {recommended}x{recommended}. Use recommended size? [Y/n]: ")
            accepted = (resp.strip() == '' or resp.strip().lower().startswith('y'))

        if accepted:
            chosen_size = recommended

    try:
        out = image_to_codes(image_path, size=chosen_size, output_path=args.output, resize=args.resize)
        print(f"Wrote codes JSON to: {out}")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()

# image_to_codes.py

This small utility converts a pixel image into the project's pixel-code JSON format.

Each pixel becomes a code string formatted as:

  <size><Row><Col><HexColor>

Examples:
- `32H11FF0000` => size 32, row H, column 11, color #FF0000 (red)

Output JSON structure:

  {
    "rows": {
      "A": ["32A0RRGGBB", ...],
      "B": [...],
      ...
    }
  }

Requirements
- Python 3.7+
- Pillow

Installation (PowerShell):

```powershell
py -3 -m pip install --user pillow
```

Run (PowerShell):

```powershell
py -3 image_to_codes.py .\path\to\image.png --size 32 --output .\image_pixels_codes.json
```

Notes
- The default mapping of row indices to labels follows: `A..Z` then `a..f` to support 32 rows.
- Hex color includes alpha if pixel has transparency (RGBA represented as RRGGBBAA).
- If the input image is not the target size and `--no-resize` is not provided, the image will be resized using nearest-neighbor to preserve hard pixels.

If you want a different code format (e.g. color names instead of hex) tell me and I can update the script.

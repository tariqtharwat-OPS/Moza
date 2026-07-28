"""Analyze logo pixel distribution to find optimal transparency threshold."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

img = Image.open("D:\\Moza\\frontend\\public\\logo.png").convert("RGB")
w, h = img.size
pixels = img.load()

# Sample pixels and their characteristics
print("=== LOGO EDGE ANALYSIS ===")
import math
cx, cy = w // 2, h // 2

# At each radius, sample what colors exist
for pct in [0.30, 0.35, 0.40, 0.42, 0.44, 0.46, 0.48]:
    r = min(w, h) * pct
    colors = {}
    for angle in range(0, 360, 5):
        x = int(cx + r * math.cos(math.radians(angle)))
        y = int(cy + r * math.sin(math.radians(angle)))
        if 0 <= x < w and 0 <= y < h:
            px = pixels[x, y]
            # Quantize color
            key = (px[0]//32, px[1]//32, px[2]//32)
            colors[key] = colors.get(key, 0) + 1
    
    bright_pixels = sum(c for k, c in colors.items() if k[0] > 7 and k[1] > 7 and k[2] > 7)
    total = sum(colors.values())
    print(f"  Radius {pct*100:.0f}%: {len(colors)} color groups, {bright_pixels}/{total} bright pixels")

# Find the minimum brightness of any pixel that's NOT white background
# Sample non-white pixels to understand the logo's color range
print("\n=== LOGO COLOR RANGE (sampling non-white pixels) ===")
dark_pixels = []
for y in range(0, h, 10):
    for x in range(0, w, 10):
        r, g, b = pixels[x, y]
        if r < 200 or g < 200 or b < 200:
            dark_pixels.append((r, g, b))
            if len(dark_pixels) >= 50:
                break
    if len(dark_pixels) >= 50:
        break

for r, g, b in dark_pixels[:20]:
    print(f"  ({r:3d},{g:3d},{b:3d}) brightness={(r+g+b)//3}")

# Find what thresholds would catch
print("\n=== THRESHOLD TEST ===")
for th in [200, 210, 220, 230, 235, 240, 245, 250]:
    count = 0
    for y in range(0, h, 5):
        for x in range(0, w, 5):
            r, g, b = pixels[x, y]
            if r > th and g > th and b > th:
                count += 1
    sampled = (w//5) * (h//5)
    print(f"  Threshold {th}: {count}/{sampled} white pixels (est. {count*25*100//(w*h)}%)")

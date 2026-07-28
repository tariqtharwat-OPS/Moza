from PIL import Image
import math

path = "D:\\Moza\\frontend\\public\\logo.png"
img = Image.open(path)
print(f"Size: {img.size}")
print(f"Mode: {img.mode}")

if img.mode != "RGBA":
    img = img.convert("RGBA")

w, h = img.size
pixels = img.load()

# Corner colors
for name, (x, y) in [("TL", (0, 0)), ("TR", (w-1, 0)), ("BL", (0, h-1)), ("BR", (w-1, h-1))]:
    print(f"  {name}: {pixels[x, y]}")

# Center
cx, cy = w // 2, h // 2
print(f"Center ({cx},{cy}): {pixels[cx, cy]}")

# Count white-ish pixels
white = 0
total = w * h
for y in range(h):
    for x in range(w):
        r, g, b, a = pixels[x, y]
        if r > 240 and g > 240 and b > 240 and a > 240:
            white += 1
print(f"White-ish pixels: {white}/{total} ({white*100/total:.1f}%)")

# Check pixels at different radius from center
for pct in [0.2, 0.35, 0.45, 0.5]:
    r = min(w, h) * pct
    print(f"\nRadius {pct*100:.0f}% ({r:.0f}px):")
    for angle in range(0, 360, 45):
        x = int(cx + r * math.cos(math.radians(angle)))
        y = int(cy + r * math.sin(math.radians(angle)))
        if 0 <= x < w and 0 <= y < h:
            px = pixels[x, y]
            if px[3] > 0:
                print(f"  {angle:3d}° ({x},{y}): {px}")

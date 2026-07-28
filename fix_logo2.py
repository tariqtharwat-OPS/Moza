"""Remove white background from MOZA logo - aggressive clean approach."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

path = "D:\\Moza\\frontend\\public\\logo.png"
img = Image.open(path).convert("RGBA")
w, h = img.size
pixels = img.load()

THRESHOLD = 200  # Any pixel with all components > 200 is background

transparent_count = 0
total = w * h

for y in range(h):
    for x in range(w):
        r, g, b, a = pixels[x, y]

        # How white is this pixel? Use max component distance
        # Pure white = all > threshold
        # Anti-aliased edge pixels have one component slightly lower
        is_background = r > THRESHOLD and g > THRESHOLD and b > THRESHOLD

        if is_background:
            pixels[x, y] = (r, g, b, 0)
            transparent_count += 1
        # else: keep as-is (full opacity)

img.save(path, "PNG")

# Verify
img2 = Image.open(path).convert("RGBA")
p2 = img2.load()
trans = semi = opaque = 0
for y in range(h):
    for x in range(w):
        a = p2[x, y][3]
        if a < 10: trans += 1
        elif a < 250: semi += 1
        else: opaque += 1

print(f"File: {path}")
print(f"Size: {img2.size}, Mode: {img2.mode}")
print(f"Transparent (alpha<10): {trans} ({trans*100/total:.1f}%)")
print(f"Edge pixels (alpha 10-249): {semi} ({semi*100/total:.1f}%)")
print(f"Opaque logo content: {opaque} ({opaque*100/total:.1f}%)")

# Check key points
for name, (x, y) in [("TL", (0,0)), ("TR", (w-1,0)), ("BL", (0,h-1)), ("BR", (w-1,h-1)),
                       ("Center", (w//2,h//2))]:
    r, g, b, a = p2[x, y]
    print(f"  {name}: ({r:3d},{g:3d},{b:3d},a={a:3d}) {'TRANSPARENT' if a < 10 else 'SEMI' if a < 250 else 'OPAQUE'}")

# Copy to root
import shutil
shutil.copy2(path, "D:\\Moza\\logo.png")
print("\nCopied to root: D:\\Moza\\logo.png")

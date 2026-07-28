"""Remove white background from MOZA logo, make it transparent."""
from PIL import Image

path = "D:\\Moza\\frontend\\public\\logo.png"
img = Image.open(path).convert("RGBA")
w, h = img.size
pixels = img.load()

# Threshold: pixels brighter than this become transparent
# Logo elements are dark/colored, background is pure white
THRESHOLD = 245
FEATHER = 15  # pixels to feather near the threshold

for y in range(h):
    for x in range(w):
        r, g, b, a = pixels[x, y]

        # How "white" is this pixel?
        brightness = (r + g + b) / 3
        max_component = max(r, g, b)
        min_component = min(r, g, b)

        # Pure white = 255,255,255
        # Logo colors: (29,28,60), (123,4,6), (11,34,75), etc.
        # Use both brightness and closeness-to-white
        is_white = r > THRESHOLD and g > THRESHOLD and b > THRESHOLD

        if is_white:
            # Calculate feathering for smooth edge
            dist = min(255 - r, 255 - g, 255 - b)
            if dist < FEATHER:
                new_alpha = int(max(0, (dist / FEATHER) * 255))
                pixels[x, y] = (r, g, b, new_alpha)
            else:
                pixels[x, y] = (r, g, b, 0)
        else:
            pixels[x, y] = (r, g, b, 255)

img.save(path, "PNG")
print(f"Updated: {path}")
print(f"Size: {img.size}, Mode: {img.mode}")

# Verify: count transparent pixels
transparent = 0
total = w * h
for y in range(h):
    for x in range(w):
        r, g, b, a = pixels[x, y]
        if a < 10:
            transparent += 1
print(f"Transparent pixels: {transparent}/{total} ({transparent*100/total:.1f}%)")

# Check corners
for name, (x, y) in [("TL", (0, 0)), ("TR", (w-1, 0)), ("BL", (0, h-1)), ("BR", (w-1, h-1))]:
    print(f"  {name}: {pixels[x, y]}")

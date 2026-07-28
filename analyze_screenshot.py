"""Analyze moza_headless.png - check logo area for white background."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

img = Image.open("D:\\Moza\\reports\\moza_headless.png").convert("RGB")
w, h = img.size
pixels = img.load()

# Logo is at x=12, y=12, w=225, h=225 (from screenshot_logo.py output)
lx, ly = 12, 12
lw, lh = 225, 225

print(f"Full image: {w}x{h}")
print(f"Logo area: ({lx},{ly})-({lx+lw},{ly+lh})")

# Check the logo bounding box for white pixels
white_bg = 0
total_logo = 0
for y in range(ly, ly+lh):
    for x in range(lx, lx+lw):
        r, g, b = pixels[x, y]
        total_logo += 1
        # A white pixel against dark bg would be >200 brightness
        if r > 200 and g > 200 and b > 200:
            white_bg += 1

print(f"\nWhite-ish pixels in logo area: {white_bg}/{total_logo} ({white_bg*100/total_logo:.1f}%)")

# Check sidebar background color (area right of logo)
print("\n=== Sidebar background (30px right of logo) ===")
for y_pct in [10, 25, 50, 75]:
    y = int(h * y_pct / 100)
    x = lx + lw + 30
    if x < w:
        r, g, b = pixels[x, y]
        print(f"  ({x},{y}): ({r},{g},{b})")

# Check if logo looks circular (transparent bg = dark slate)
print("\n=== Logo corners (should be dark slate if transparent) ===")
# Logo is 225x225 from (12,12)
corners = [("TL", lx, ly), ("TR", lx+lw-1, ly), ("BL", lx, ly+lh-1), ("BR", lx+lw-1, ly+lh-1)]
for name, cx, cy in corners:
    if cx < w and cy < h:
        r, g, b = pixels[cx, cy]
        is_dark = "DARK" if r < 100 else "LIGHT"
        print(f"  {name} ({cx},{cy}): ({r},{g},{b}) [{is_dark}]")

# Check center of logo
cx, cy = lx + lw//2, ly + lh//2
r, g, b = pixels[cx, cy]
print(f"\n  Center ({cx},{cy}): ({r},{g},{b})")

# Overall sidebar brightness analysis
print("\n=== Overall sidebar (left 250px) brightness ===")
bright_sum = 0
pixel_count = 0
for y in range(h):
    for x in range(min(250, w)):
        r2, g2, b2 = pixels[x, y]
        bright_sum += (r2 + g2 + b2) // 3
        pixel_count += 1
avg = bright_sum / pixel_count if pixel_count else 0
print(f"  Average brightness: {avg:.1f} (dark < 100)")
if avg < 100:
    print("  SIDEBAR IS DARK - transparency working!")
else:
    print("  SIDEBAR IS LIGHT - transparency NOT working")

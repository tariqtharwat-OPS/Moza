"""Check the full-page render for sidebar/logo appearance."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

img = Image.open("D:\\Moza\\reports\\moza_final.png").convert("RGB")
w, h = img.size
pixels = img.load()
total = w * h

# Sample the leftmost 200px column (sidebar area) at various heights
print(f"Full page screenshot: {w}x{h}")
print("\n=== Sidebar color samples (left 200px) ===")
for y_pct in [5, 10, 25, 50, 75, 90]:
    y = int(h * y_pct / 100)
    r_sum = g_sum = b_sum = 0
    samples = min(200, w)
    for x in range(samples):
        r, g, b = pixels[x, y]
        r_sum += r
        g_sum += g
        b_sum += b
    print(f"  y={y} (top {y_pct}%): avg=({r_sum//samples},{g_sum//samples},{b_sum//samples})")

# Check specifically the logo area (likely top-left)
print("\n=== Logo area (top 200px, left 200px) ===")
white_px = 0
total_logo = 200 * 200
for y in range(200):
    for x in range(200):
        r, g, b = pixels[x, y]
        if r > 230 and g > 230 and b > 230:
            white_px += 1
print(f"  White-ish pixels in logo area: {white_px}/{total_logo} ({white_px*100/total_logo:.1f}%)")

# Also check a wider area
print("\n=== Logo area (top 300px, left 300px) ===")
white_px = 0
total_wide = 300 * 300
for y in range(300):
    for x in range(300):
        r, g, b = pixels[x, y]
        if r > 230 and g > 230 and b > 230:
            white_px += 1
print(f"  White-ish pixels: {white_px}/{total_wide} ({white_px*100/total_wide:.1f}%)")

# Average brightness of overall image
b_sum = 0
for y in range(0, h, 10):
    for x in range(0, w, 10):
        r, g, b = pixels[x, y]
        b_sum += (r + g + b) // 3
avg_brightness = b_sum // ((w//10) * (h//10))
print(f"\nOverall avg brightness: {avg_brightness}")

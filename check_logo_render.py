"""Check rendered logo screenshot for white halo."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

img = Image.open("D:\\Moza\\reports\\logo_final.png").convert("RGB")
w, h = img.size
pixels = img.load()
total = w * h

# Count how many pixels are white-ish (R>240, G>240, B>240)
white = 0
for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        if r > 240 and g > 240 and b > 240:
            white += 1

print(f"Logo screenshot size: {w}x{h}")
print(f"White-ish pixels (R>240,G>240,B>240): {white}/{total} ({white*100/total:.1f}%)")
if white == 0:
    print("PERFECT: No white pixels at all!")
elif white < 10:
    print(f"EXCELLENT: Only {white} white pixels (likely compression artifacts)")
elif white < 100:
    print(f"GOOD: {white} white pixels - minimal")
else:
    print(f"White pixels present: {white}")

# Check average color of the screenshot
r_sum = g_sum = b_sum = 0
for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        r_sum += r
        g_sum += g
        b_sum += b
avg_r, avg_g, avg_b = r_sum//total, g_sum//total, b_sum//total
print(f"Average color: ({avg_r},{avg_g},{avg_b})")
print(f"Sidebar is bg-slate-900/40 - expected dark slate (~30,40,60)")
if avg_r < 100:
    print("Background is dark - transparency working correctly!")
else:
    print("Background appears light - may still have white halo issue")

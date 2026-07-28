"""Verify logo transparency in rendered UI screenshot."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

# Check the original logo (now with transparency)
logo = Image.open("D:\\Moza\\frontend\\public\\logo.png")
print("=== ORIGINAL LOGO FILE ===")
print(f"Mode: {logo.mode}")
print(f"Size: {logo.size}")

if logo.mode == "RGBA":
    pixels = logo.load()
    w, h = logo.size
    # Check various points
    checks = {
        "Top-left corner (0,0)": (0, 0),
        "Top-right (1023,0)": (1023, 0),
        "Bottom-left (0,1023)": (0, 1023),
        "Bottom-right (1023,1023)": (1023, 1023),
        "Center (512,512)": (512, 512),
        "Mid-left (0,512)": (0, 512),
        "Mid-top (512,0)": (512, 0),
    }
    for name, (x, y) in checks.items():
        r, g, b, a = pixels[x, y]
        status = "TRANSPARENT" if a < 10 else "OPAQUE"
        print(f"  {name}: ({r},{g},{b},{a}) - {status}")

    # Count fully transparent (alpha < 10) vs semi-transparent vs opaque
    trans = semi = opaque = 0
    for y in range(h):
        for x in range(w):
            a = pixels[x, y][3]
            if a < 10: trans += 1
            elif a < 245: semi += 1
            else: opaque += 1
    total = w * h
    print(f"\n  Transparent: {trans} ({trans*100/total:.1f}%)")
    print(f"  Semi-transparent (edge feather): {semi} ({semi*100/total:.1f}%)")
    print(f"  Opaque (logo content): {opaque} ({opaque*100/total:.1f}%)")

# Check the rendered screenshot
import glob
screenshots = list(glob.glob("D:\\Moza\\reports\\*.png"))
print(f"\n=== RENDERED SCREENSHOTS ({len(screenshots)} files) ===")
for sp in sorted(screenshots):
    sz = round(Image.open(sp).size[0] * Image.open(sp).size[1] / 1024)
    print(f"  {sp.split(chr(92))[-1]}: {Image.open(sp).size}")

# Check the actual logo area in the full screenshot
try:
    full = Image.open("D:\\Moza\\reports\\moza_with_logo.png")
    full = full.convert("RGBA")
    fp = full.load()
    fw, fh = full.size
    # The sidebar is the left ~250px
    # Logo is in the sidebar header area (top ~100px)
    # Check a point where the logo circle edge should be
    # and verify there's NO white halo
    print("\n=== CHECKING RENDERED LOGO AREA (left sidebar, top 100px) ===")
    white_halo = 0
    for y in range(0, 100):
        for x in range(0, 250):
            r, g, b, a = fp[x, y]
            if r > 240 and g > 240 and b > 240:
                white_halo += 1
    sidebar_pixels = 250 * 100
    print(f"  Near-white pixels in sidebar logo area: {white_halo}/{sidebar_pixels} ({white_halo*100/sidebar_pixels:.2f}%)")
    if white_halo < 100:
        print("  [OK] No white halo detected - logo transparency is working!")
    else:
        print(f"  [WARN] {white_halo} near-white pixels found - may need adjustment")
except Exception as e:
    print(f"  Could not analyze screenshot: {e}")

import base64
import time
from pathlib import Path
from typing import Optional


async def take_screenshot(page, screenshots_dir: Optional[Path] = None) -> dict:
    png_bytes = await page.screenshot(full_page=False)
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    meta: dict = {"screenshot_base64": b64}

    if screenshots_dir:
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.monotonic() * 1000)
        shot_path = screenshots_dir / f"screenshot_{ts}.png"
        shot_path.write_bytes(png_bytes)
        meta["screenshot_path"] = str(shot_path)

    return meta

"""
Live Browser Research: Red Snapper Importers
Headed mode — watch the browser on screen.
"""

import asyncio
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path("D:/Moza/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Research data store ──────────────────────────────────────────
results: list[dict] = []
all_log: list[dict] = []


async def run():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        page.set_default_timeout(30000)

        # ── Research countries ────────────────────────────────────
        searches = [
            ("Indonesia", "red snapper frozen fish exporter Indonesia site:.id"),
            ("Vietnam", "red snapper frozen fish exporter Vietnam"),
            ("Malaysia", "red snapper frozen fish supplier Malaysia"),
        ]

        for country, query in searches:
            print(f"\n{'='*60}")
            print(f" RESEARCHING: {country}")
            print(f" Query: {query}")
            print(f"{'='*60}")

            # 1. Navigate to Google
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            # 2. Accept cookies if present
            try:
                btn = page.locator("button:has-text('Accept all')").first
                if await btn.is_visible(timeout=3000):
                    await btn.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # 3. Search
            search_box = page.locator("textarea[name='q']").first
            await search_box.fill(query)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            # 4. Collect search results
            links = []
            for i in range(5):
                try:
                    result = page.locator("div.g").nth(i) if page.locator("div.g").count() else None
                    if result is None:
                        continue
                    title_el = result.locator("h3").first
                    link_el = result.locator("a").first
                    snippet_el = result.locator("span.aCOpRe, div.VwiC3b").first
                    title = await title_el.inner_text() if await title_el.count() else ""
                    href = await link_el.get_attribute("href") if await link_el.count() else ""
                    snippet = ""
                    if await snippet_el.count():
                        snippet = await snippet_el.inner_text()
                    if title and href:
                        links.append({"title": title, "url": href, "snippet": snippet[:200]})
                except:
                    continue

            # 5. Visit top 2-3 links
            for link in links[:3]:
                try:
                    print(f"  -> Visiting: {link['title'][:60]}")
                    await page.goto(link["url"], wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(3000)
                    body_text = await page.inner_text("body")
                    # Extract company info
                    record = {
                        "country": country,
                        "company": link["title"],
                        "website": link["url"],
                        "notes": (body_text[:500].replace("\n", " ").strip()),
                        "snippet": link["snippet"],
                    }
                    results.append(record)
                    all_log.append({
                        "country": country,
                        "step": f"Visited {link['title'][:50]}",
                        "url": link["url"],
                        "status": "ok",
                    })
                except Exception as e:
                    all_log.append({
                        "country": country,
                        "step": f"Failed {link['title'][:50]}",
                        "url": link["url"],
                        "status": f"error: {e}",
                    })

        await browser.close()

    # ── Write CSV ─────────────────────────────────────────────────
    csv_path = REPORTS_DIR / "red_snapper_importers.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Country", "Company Name", "Website", "Notes"])
        for r in results:
            writer.writerow([r["country"], r["company"], r["website"], r["notes"][:300]])

    # ── Write HTML Report ─────────────────────────────────────────
    html_path = REPORTS_DIR / "red_snapper_report.html"
    rows_html = ""
    for i, r in enumerate(results, 1):
        rows_html += f"""
        <tr>
            <td>{i}</td>
            <td class="company-name">{r['company']}</td>
            <td><a class="website-link" href="{r['website']}" target="_blank">{r['website'][:50]}</a></td>
            <td>{r['notes'][:200]}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Red Snapper Importers — Live Research Report</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:system-ui,-apple-system,sans-serif; font-size:14px; color:#1e293b; background:#f8fafc; padding:40px; }}
  .page {{ max-width:1000px; margin:0 auto; background:#fff; padding:32px; border-radius:12px; box-shadow:0 1px 3px rgba(0,0,0,.1); }}
  h1 {{ font-size:24px; font-weight:700; color:#0f172a; border-bottom:3px solid #0f172a; padding-bottom:16px; margin-bottom:24px; }}
  .meta {{ font-size:12px; color:#94a3b8; margin-bottom:24px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  thead th {{ background:#0f172a; color:#fff; padding:10px 12px; text-align:left; font-weight:500; }}
  tbody td {{ padding:10px 12px; border-bottom:1px solid #e2e8f0; vertical-align:top; }}
  tbody tr:hover {{ background:#f1f5f9; }}
  .company-name {{ font-weight:600; color:#0f172a; }}
  .website-link {{ color:#2563eb; text-decoration:none; font-size:12px; }}
  .website-link:hover {{ text-decoration:underline; }}
  .footer {{ margin-top:32px; padding-top:12px; border-top:1px solid #e2e8f0; font-size:11px; color:#94a3b8; }}
</style>
</head>
<body>
<div class="page">
  <h1>Red Snapper Importers — Live Browser Research</h1>
  <div class="meta">Generated {datetime.now().strftime('%d %B %Y at %H:%M')} | Research conducted via live Playwright browser in headed mode</div>
  <table>
    <thead><tr><th>#</th><th>Company</th><th>Website</th><th>Notes</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div class="footer">MOZA Intelligence · Live Browser Execution · {len(results)} suppliers across {len(set(r['country'] for r in results))} countries</div>
</div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n{'='*60}")
    print(f" DONE: {len(results)} records collected")
    print(f" CSV: {csv_path}")
    print(f" HTML: {html_path}")
    print(f"{'='*60}")

    # Print logs
    print("\n--- Execution Log ---")
    for log in all_log:
        print(f"  [{log['country']}] {log['step']} — {log['status']}")


if __name__ == "__main__":
    asyncio.run(run())

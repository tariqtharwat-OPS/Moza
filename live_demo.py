"""
Live Browser Demo: Red Snapper Research
Headed mode — watch the browser on screen.
slow_mo=1500 so every action is visible.
"""

import asyncio, csv, time
from datetime import datetime
from pathlib import Path

REPORTS = Path("D:/Moza/reports")
REPORTS.mkdir(parents=True, exist_ok=True)


async def run():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        page = await browser.new_page()

        results = []

        searches = [
            ("Indonesia", "red snapper frozen fish exporter Indonesia"),
            ("Vietnam", "red snapper frozen fish exporter Vietnam"),
            ("Malaysia", "red snapper frozen fish supplier Malaysia"),
        ]

        for country, query in searches:
            print(f"\n>>> RESEARCHING: {country}")
            print(f">>> Query: {query}")

            # Google
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            # Accept cookies if present
            try:
                accept = page.locator("button:has-text('Accept all'), button:has-text('Accept'), button:has-text('I agree')").first
                if await accept.is_visible(timeout=3000):
                    await accept.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # Search
            box = page.locator("textarea[name='q'], input[name='q']").first
            await box.fill(query)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

            # Collect results
            for i in range(5):
                try:
                    cards = page.locator("div.g")
                    if await cards.count() <= i:
                        continue
                    card = cards.nth(i)
                    title = await card.locator("h3").first.inner_text()
                    href = await card.locator("a").first.get_attribute("href") or ""
                    snippet_el = card.locator("div.VwiC3b, span.aCOpRe").first
                    snippet = ""
                    if await snippet_el.count():
                        snippet = await snippet_el.inner_text()
                    if title:
                        results.append({
                            "country": country,
                            "company": title,
                            "website": href,
                            "notes": snippet[:300],
                        })
                        print(f"  [{i+1}] {title[:60]}")
                except:
                    continue

            # Visit top 2
            for rec in results[-5:][:2]:
                if not rec["website"].startswith("http"):
                    continue
                try:
                    print(f"  -> Visiting: {rec['company'][:50]}")
                    await page.goto(rec["website"], wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(3000)
                    body = await page.inner_text("body")
                    rec["notes"] = (body[:400].replace("\n", " ").strip())
                except Exception as e:
                    print(f"  -> SKIP: {e}")

        await browser.close()

    # Write CSV
    csv_path = REPORTS / "red_snapper_importers.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Country", "Company Name", "Website", "Notes"])
        for r in results:
            w.writerow([r["country"], r["company"], r["website"], r["notes"][:300]])

    # Write HTML
    html_path = REPORTS / "red_snapper_report.html"
    rows = ""
    for i, r in enumerate(results, 1):
        rows += f"<tr><td>{i}</td><td class='cname'>{r['company']}</td><td><a class='link' href='{r['website']}'>{r['website'][:50]}</a></td><td>{r['notes'][:200]}</td></tr>\n"

    html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><title>Red Snapper Importers — Live Demo</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;font-size:14px;color:#1e293b;background:#f8fafc;padding:40px}}
.page{{max-width:1000px;margin:0 auto;background:#fff;padding:32px;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
h1{{font-size:24px;font-weight:700;color:#0f172a;border-bottom:3px solid #0f172a;padding-bottom:16px;margin-bottom:24px}}
.meta{{font-size:12px;color:#94a3b8;margin-bottom:24px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#0f172a;color:#fff;padding:10px 12px;text-align:left;font-weight:500}}
td{{padding:10px 12px;border-bottom:1px solid #e2e8f0;vertical-align:top}}
tr:hover{{background:#f1f5f9}}
.cname{{font-weight:600;color:#0f172a}}
.link{{color:#2563eb;text-decoration:none;font-size:12px}}
.footer{{margin-top:32px;padding-top:12px;border-top:1px solid #e2e8f0;font-size:11px;color:#94a3b8}}
</style></head><body><div class="page">
<h1>Red Snapper Importers — Live Browser Research</h1>
<div class="meta">{datetime.now().strftime('%d %B %Y at %H:%M')} | Headed Playwright | slow_mo=1500ms</div>
<table><thead><tr><th>#</th><th>Company</th><th>Website</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table>
<div class="footer">{len(results)} suppliers across {len(set(r['country'] for r in results))} countries</div>
</div></body></html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n{'='*50}")
    print(f" DONE! Files created:")
    print(f"   CSV: {csv_path}")
    print(f"   HTML: {html_path}")
    print(f"   {len(results)} records collected")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(run())

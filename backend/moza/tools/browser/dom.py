async def extract_text(page, selector: str | None = None) -> str:
    if selector:
        elements = await page.query_selector_all(selector)
        texts = []
        for el in elements:
            try:
                text = await el.inner_text()
                texts.append(text)
            except Exception:
                texts.append("")
        return "\n".join(texts)
    return await page.inner_text("body")


async def get_title(page) -> str:
    return await page.title()


def get_url(page) -> str:
    return page.url


async def execute_js(page, script: str) -> str:
    result = await page.evaluate(script)
    return str(result) if result is not None else "(null)"

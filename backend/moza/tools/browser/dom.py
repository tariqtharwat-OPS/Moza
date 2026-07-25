async def extract_text(page, selector: str | None = None) -> str:
    if selector:
        elements = await page.query_selector_all(selector)
        texts = [await el.inner_text() for el in elements]
        return "\n".join(texts)
    return await page.inner_text("body")


async def get_title(page) -> str:
    return await page.title()


async def get_url(page) -> str:
    return page.url


async def execute_js(page, script: str) -> str:
    result = await page.evaluate(script)
    return str(result) if result is not None else "(null)"

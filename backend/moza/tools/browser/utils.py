VALID_ACTIONS = frozenset({
    "navigate", "click", "type", "extract_text", "screenshot",
    "scroll", "back", "forward", "get_url", "execute_js", "close",
})

ACTION_HELP = (
    "Valid actions: navigate, click, type, extract_text, screenshot, "
    "scroll, back, forward, get_url, execute_js, close"
)

SCROLL_TIMEOUT_MS = 300
CLICK_TIMEOUT_MS = 500
BACK_TIMEOUT_MS = 500
FORWARD_TIMEOUT_MS = 500

from typing import Any


def normalize_streaming_chunk(chunk: Any) -> Any:
    """Normalize LLM response chunks to ensure type safety.

    This function handles cases where providers return non-string content
    (e.g., Cloudflare Llama-4-Scout returns numbers instead of strings).

    Args:
        chunk: The raw streaming chunk from the LLM provider.

    Returns:
        The normalized chunk with content coerced to string.
    """
    if isinstance(chunk, dict) and 'choices' in chunk and chunk['choices']:
        delta = chunk['choices'][0].get('delta', {})
        if 'content' in delta and delta['content'] is not None:
            content = delta['content']
            # Normalize numbers to strings (handles Cloudflare's non-standard behavior)
            if isinstance(content, (int, float)):
                delta['content'] = str(content)
    return chunk


def normalize_response_content(content: Any) -> str:
    """Normalize response content to ensure it's a string.

    Args:
        content: The raw content from the LLM response.

    Returns:
        The content as a string.
    """
    if content is None:
        return ""
    if isinstance(content, (int, float)):
        return str(content)
    return str(content)

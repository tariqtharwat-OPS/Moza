#!/usr/bin/env python3
"""
Test the response normalization layer with Cloudflare Llama-4-Scout
"""

from moza.core.response_normalizer import normalize_streaming_chunk, normalize_response_content


def test_normalize_streaming_chunk():
    """Test that numbers are converted to strings in streaming chunks."""
    # Simulate a Cloudflare Llama-4-Scout chunk with number content
    chunk = {
        "choices": [
            {
                "delta": {
                    "content": 30
                }
            }
        ]
    }

    normalized = normalize_streaming_chunk(chunk)

    # Verify content is now a string
    assert isinstance(normalized["choices"][0]["delta"]["content"], str), \
        f"Expected string, got {type(normalized['choices'][0]['delta']['content'])}"
    assert normalized["choices"][0]["delta"]["content"] == "30", \
        f"Expected '30', got {normalized['choices'][0]['delta']['content']}"

    print("[PASS] normalize_streaming_chunk converts numbers to strings")


def test_normalize_response_content():
    """Test that numbers are converted to strings in response content."""
    # Test with number
    content = 123
    normalized = normalize_response_content(content)
    assert isinstance(normalized, str), \
        f"Expected string, got {type(normalized)}"
    assert normalized == "123", \
        f"Expected '123', got {normalized}"

    # Test with float
    content = 45.67
    normalized = normalize_response_content(content)
    assert isinstance(normalized, str), \
        f"Expected string, got {type(normalized)}"
    assert normalized == "45.67", \
        f"Expected '45.67', got {normalized}"

    # Test with string (should remain unchanged)
    content = "Hello World"
    normalized = normalize_response_content(content)
    assert isinstance(normalized, str), \
        f"Expected string, got {type(normalized)}"
    assert normalized == "Hello World", \
        f"Expected 'Hello World', got {normalized}"

    # Test with None
    content = None
    normalized = normalize_response_content(content)
    assert normalized == "", \
        f"Expected empty string, got {normalized}"

    print("[PASS] normalize_response_content converts numbers to strings")


def test_cloudflare_chunk():
    """Test with a realistic Cloudflare chunk."""
    # Simulate a realistic Cloudflare Llama-4-Scout chunk
    chunks = [
        {"choices": [{"delta": {"content": "Hello"}}]},
        {"choices": [{"delta": {"content": 30}}]},  # Number content (Cloudflare bug)
        {"choices": [{"delta": {"content": " World"}}]},
    ]

    for chunk in chunks:
        normalized = normalize_streaming_chunk(chunk)
        content = normalized["choices"][0]["delta"]["content"]
        assert isinstance(content, str), f"Expected string, got {type(content)}"
        print(f"  - Chunk content: {content}")

    print("[PASS] Cloudflare chunk with number content is normalized correctly")


if __name__ == "__main__":
    print("Testing Response Normalization Layer")
    print("=" * 60)
    test_normalize_streaming_chunk()
    test_normalize_response_content()
    test_cloudflare_chunk()
    print("=" * 60)
    print("All tests passed! [PASS]")

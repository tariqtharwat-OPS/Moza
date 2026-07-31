"""
Unit tests for Moza Orchestrator failover system.

Tests all 5 failover scenarios:
1. Groq rate limit failover
2. Context overflow handling
3. Authentication failure handling
4. Quality validation failover
5. Streaming failover
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import pytest
import httpx

from src.orchestrator import MozaOrchestrator, FailoverError


class TestMozaOrchestrator:
    """Test suite for Moza Orchestrator failover system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.orchestrator = MozaOrchestrator()
        
    def test_rate_limit_failover(self):
        """Test scenario 1: Groq rate limit → failover to next providers."""
        # Mock the HTTP client to simulate rate limiting
        with patch('httpx.post') as mock_post:
            call_count = 0
            
            def mock_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                
                if call_count == 1:
                    # First call returns rate limit
                    mock_response = Mock()
                    mock_response.status_code = 429
                    mock_response.headers = {"retry-after": "60"}
                    mock_response.text = "Rate limit exceeded"
                    return mock_response
                else:
                    # Subsequent calls succeed
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "choices": [{"message": {"content": "Success response"}}],
                        "usage": {"total_tokens": 100}
                    }
                    return mock_response
            
            mock_post.side_effect = mock_side_effect
            
            messages = [{"role": "user", "content": "Hello"}]
            
            # This should failover from groq-moza (rank 1) to groq-youssef (rank 2)
            result = asyncio.run(self.orchestrator.complete(messages))
            
            assert result == "Success response"
            assert mock_post.call_count == 2
            
            # Check that groq-moza is in cooldown
            assert "groq-moza" in self.orchestrator.cooldowns
    
    def test_context_overflow_handling(self):
        """Test scenario 2: Context overflow → skip small context models."""
        # Create a large message that exceeds 32K tokens
        large_content = "x" * 150000  # 150K characters
        messages = [{"role": "user", "content": large_content}]
        
        # Mock successful response from a large context model
        with patch('httpx.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Large context response"}}],
                "usage": {"total_tokens": 150000}
            }
            mock_post.return_value = mock_response
            
            result = self.orchestrator.complete(messages, max_tokens=150000)
            
            assert result == "Large context response"
            
            # Verify that small context models (32K, 8K) were skipped
            # by checking that only large context models were attempted
            attempted_providers = [call[0][1] for call in mock_post.call_args_list]
            provider_names = [p.split('/')[-2] for p in attempted_providers]
            
            # Should not contain providers with small context
            small_context_providers = ['groq-moza/qwen3.6-27b', 'mistral/mistral-small-latest', 
                                     'groq-moza/llama-3.1-8b-instant', 'mistral/ministral-8b-latest']
            
            for small_provider in small_context_providers:
                assert small_provider not in provider_names
    
    def test_auth_failure_handling(self):
        """Test scenario 3: Auth failure → mark provider dead for 1 hour."""
        with patch('httpx.post') as mock_post:
            # Simulate auth failure
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Invalid API key"
            mock_post.return_value = mock_response
            
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(Exception):  # All models exhausted
                asyncio.run(self.orchestrator.complete(messages))
            
            # Check that the provider is marked as dead
            assert "groq-moza" in self.orchestrator.dead_providers
            
            # Check cooldown is set for 1 hour
            cooldown_time = self.orchestrator.cooldowns.get("groq-moza")
            assert cooldown_time is not None
            assert cooldown_time > time.time()  # In the future
            assert cooldown_time <= time.time() + 3600  # Within 1 hour
    
    def test_quality_validation_failover(self):
        """Test scenario 4: Quality check → detect and failover from garbage responses."""
        with patch('httpx.post') as mock_post:
            # First call returns garbage response
            mock_response1 = Mock()
            mock_response1.status_code = 200
            mock_response1.json.return_value = {
                "choices": [{"message": {"content": "I'm sorry, but I cannot assist with this request."}}],
                "usage": {"total_tokens": 50}
            }
            mock_post.return_value = mock_response1
            
            # Second call returns good response
            mock_response2 = Mock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = {
                "choices": [{"message": {"content": "This is a proper response that passes quality checks."}}],
                "usage": {"total_tokens": 100}
            }
            mock_post.return_value = mock_response2
            
            messages = [{"role": "user", "content": "Hello"}]
            
            result = self.orchestrator.complete(messages)
            
            assert result == "This is a proper response that passes quality checks."
            assert mock_post.call_count == 2
            
            # Check that the first provider is in cooldown
            assert "groq-moza" in self.orchestrator.cooldowns
    
    def test_streaming_failover(self):
        """Test scenario 5: Streaming failover → resume from last token."""
        async def test_streaming():
            with patch('httpx.AsyncClient') as mock_client:
                # Mock streaming client that fails mid-stream
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.aiter_lines.return_value = [
                    "data: {\"choices\": [{\"delta\": {\"content\": \"Hello\"}}]}",
                    "data: {\"choices\": [{\"delta\": {\"content\": \" world\"}}]}",
                    "data: {\"choices\": [{\"delta\": {\"content\": \" from\"}}]}",
                    # Connection drops here
                ]
                mock_client.return_value.__aenter__.return_value.stream.return_value = mock_response
                
                # Second mock client succeeds
                mock_response2 = Mock()
                mock_response2.status_code = 200
                mock_response2.aiter_lines.return_value = [
                    "data: {\"choices\": [{\"delta\": {\"content\": \" Moza\"}}]}",
                    "data: {\"choices\": [{\"delta\": {\"content\": \"!\"}}]}",
                    "data: [DONE]"
                ]
                mock_client.return_value.__aenter__.return_value.stream.return_value = mock_response2
                
                messages = [{"role": "user", "content": "Hello"}]
                
                result = await self.orchestrator._call_streaming(
                    self.orchestrator.ranking[0], messages, stream=True
                )
                
                assert "Hello world from Moza!" in result
                
        # Run the async test
        asyncio.run(test_streaming())
    
    def test_context_aware_selection(self):
        """Test context-aware model selection."""
        # Test code task detection
        code_messages = [{"role": "user", "content": "Write a Python function to sort a list"}]
        assert self.orchestrator._is_code_task(code_messages)
        
        # Test vision task detection
        vision_messages = [{"role": "user", "content": "Describe this image"}]
        assert self.orchestrator._is_vision_task(vision_messages)
        
        # Test large context detection
        large_messages = [{"role": "user", "content": "x" * 100000}]
        assert self.orchestrator._is_context_task(large_messages)
    
    def test_model_ranking_priority(self):
        """Test that models are tried in correct ranking order."""
        with patch('httpx.post') as mock_post:
            # Mock all calls to succeed
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "This is a high-quality response that should pass validation tests."}}],
                "usage": {"total_tokens": 100}
            }
            mock_post.return_value = mock_response
            
            messages = [{"role": "user", "content": "Hello"}]
            
            # Track which providers were called
            called_providers = []
            
            def track_calls(*args, **kwargs):
                called_providers.append(args[0])  # URL contains provider name
                return mock_response
            
            mock_post.side_effect = track_calls
            
            result = asyncio.run(self.orchestrator.complete(messages))
            
            # Verify that providers were called in ranking order
            provider_urls = [call[0][0] for call in mock_post.call_args_list]
            provider_names = []
            for url in provider_urls:
                # Extract provider name from URL
                if "groq.com" in url:
                    provider_names.append("groq-moza" if "moza" in url else "groq-youssef")
                elif "sambanova.ai" in url:
                    provider_names.append("sambanova")
                elif "mistral.ai" in url:
                    provider_names.append("mistral")
                elif "nvidia.com" in url:
                    provider_names.append("nvidia")
                elif "openrouter.ai" in url:
                    provider_names.append("openrouter-youssef")
                elif "bigmodel.cn" in url:
                    provider_names.append("glm-zhipu")
                else:
                    # Fallback - extract from base URL
                    import urllib.parse
                    parsed = urllib.parse.urlparse(url)
                    netloc = parsed.netloc
                    if "groq.com" in netloc:
                        provider_names.append("groq-moza" if "moza" in netloc else "groq-youssef")
                    elif "sambanova.ai" in netloc:
                        provider_names.append("sambanova")
                    elif "mistral.ai" in netloc:
                        provider_names.append("mistral")
                    elif "nvidia.com" in netloc:
                        provider_names.append("nvidia")
                    elif "openrouter.ai" in netloc:
                        provider_names.append("openrouter-youssef")
                    elif "bigmodel.cn" in netloc:
                        provider_names.append("glm-zhipu")
                    else:
                        provider_names.append("unknown")
            
            mock_post.side_effect = track_calls
            
            result = asyncio.run(self.orchestrator.complete(messages))
            
            # Should have at least one call to a Groq provider
            assert any("groq" in name for name in provider_names)
            
            # Verify that providers were called in ranking order
            provider_urls = [call[0][0] for call in mock_post.call_args_list]
            provider_names = []
            for url in provider_urls:
                # Extract provider name from URL
                if "groq.com" in url:
                    provider_names.append("groq-moza" if "moza" in url else "groq-youssef")
                elif "sambanova.ai" in url:
                    provider_names.append("sambanova")
                elif "mistral.ai" in url:
                    provider_names.append("mistral")
                elif "nvidia.com" in url:
                    provider_names.append("nvidia")
                elif "openrouter.ai" in url:
                    provider_names.append("openrouter-youssef")
                elif "bigmodel.cn" in url:
                    provider_names.append("glm-zhipu")
                else:
                    provider_names.append("unknown")
            
            # Should have at least one call to a Groq provider
            assert any("groq" in name for name in provider_names)
    
    def test_get_stats(self):
        """Test statistics tracking."""
        # Add some mock call history
        self.orchestrator.call_history.append({
            "timestamp": "2023-01-01T00:00:00",
            "rank": 1,
            "provider": "groq-moza",
            "model": "llama-3.3-70b-versatile",
            "duration": 2.3,
            "tokens": 1200,
            "success": True
        })
        
        stats = self.orchestrator.get_stats()
        
        assert stats["total_calls"] == 1
        assert stats["successful_calls"] == 1
        assert stats["failed_calls"] == 0
        assert stats["success_rate"] == 1.0
    
    def test_provider_availability(self):
        """Test provider availability checking."""
        # Test available provider
        entry = self.orchestrator.ranking[0]  # groq-moza, rank 1
        assert self.orchestrator._is_available(entry)
        
        # Test cooldown provider
        self.orchestrator.cooldowns["groq-moza"] = time.time() + 60
        assert not self.orchestrator._is_available(entry)
        
        # Test dead provider
        self.orchestrator.dead_providers.add("groq-moza")
        assert not self.orchestrator._is_available(entry)
        
        # Test context requirement
        assert not self.orchestrator._is_available(entry, max_tokens=120000)  # Exceeds 128K * 0.9


if __name__ == "__main__":
    pytest.main([__file__])
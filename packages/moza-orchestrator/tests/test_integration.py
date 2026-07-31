"""
Integration tests for Moza Orchestrator with existing Moza system.

These tests verify that the orchestrator can be integrated into the
existing Moza backend structure.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

# Mock the existing Moza imports
import sys
from unittest.mock import MagicMock

# Mock moza modules
sys.modules['moza.agents.interfaces'] = MagicMock()
sys.modules['moza.core.context'] = MagicMock()
sys.modules['moza.core.event_bus'] = MagicMock()
sys.modules['moza.core.intent_classifier'] = MagicMock()
sys.modules['moza.core.models'] = MagicMock()
sys.modules['moza.core.state_machine'] = MagicMock()
sys.modules['moza.tools.registry'] = MagicMock()

from moza_orchestrator import MozaOrchestrator


class TestMozaIntegration:
    """Integration tests with Moza system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.orchestrator = MozaOrchestrator()
        
    def test_integration_with_llm_providers(self):
        """Test integration with existing LLM providers structure."""
        # This simulates the integration point in packages/opencode/src/llm/providers.ts
        
        # Mock the existing provider interface
        mock_provider = MagicMock()
        mock_provider.complete = asyncio.coroutine(lambda messages, **kwargs: 
            self.orchestrator.complete(messages, **kwargs))
        
        # Test that the orchestrator can be used as a drop-in replacement
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Hello from Moza Orchestrator!"}}],
                "usage": {"total_tokens": 20}
            }
            mock_post.return_value = mock_response
            
            # Test the integration
            result = asyncio.run(mock_provider.complete(messages))
            assert result == "Hello from Moza Orchestrator!"
    
    def test_context_aware_routing(self):
        """Test that the orchestrator routes based on Moza context."""
        # Simulate different task types from Moza
        
        # Code task
        code_messages = [{"role": "user", "content": "Write a Python function"}]
        assert self.orchestrator._is_code_task(code_messages)
        
        # Context-heavy task
        large_messages = [{"role": "user", "content": "x" * 100000}]
        assert self.orchestrator._is_context_task(large_messages)
        
        # Vision task
        vision_messages = [{"role": "user", "content": "Describe this image"}]
        assert self.orchestrator._is_vision_task(vision_messages)
    
    def test_failover_preserves_context(self):
        """Test that failover preserves conversation context."""
        messages = [
            {"role": "user", "content": "Hello, my name is Alice"},
            {"role": "assistant", "content": "Hello Alice! How can I help you today?"},
            {"role": "user", "content": "What's my name?"}
        ]
        
        with patch('httpx.post') as mock_post:
            # First call fails (rate limit)
            mock_response1 = MagicMock()
            mock_response1.status_code = 429
            mock_response1.headers = {"retry-after": "60"}
            mock_response1.text = "Rate limit"
            
            # Second call succeeds
            mock_response2 = MagicMock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = {
                "choices": [{"message": {"content": "Your name is Alice"}}],
                "usage": {"total_tokens": 15}
            }
            
            mock_post.side_effect = [mock_response1, mock_response2]
            
            result = asyncio.run(self.orchestrator.complete(messages))
            assert result == "Your name is Alice"
            
            # Verify that all messages were passed to the successful provider
            call_args = mock_post.call_args_list[1][0][1]  # Second call's JSON payload
            assert len(call_args['messages']) == 3  # All context preserved
    
    def test_error_handling_compatibility(self):
        """Test error handling compatibility with Moza system."""
        # Test that FailoverError can be handled by Moza's existing error handling
        
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Invalid API key"
            mock_post.return_value = mock_response
            
            # This should raise an exception that Moza can handle
            with pytest.raises(Exception):
                asyncio.run(self.orchestrator.complete(messages))
        
        # Verify that the provider is marked as dead
        assert "groq-moza" in self.orchestrator.dead_providers
    
    def test_telemetry_integration(self):
        """Test that telemetry integrates with Moza's logging system."""
        # Add a successful call to history
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
        
        # Verify stats match what Moza would expect
        assert stats["total_calls"] == 1
        assert stats["successful_calls"] == 1
        assert stats["success_rate"] == 1.0
        assert isinstance(stats["dead_providers"], list)
        assert isinstance(stats["cooldown_providers"], dict)


if __name__ == "__main__":
    pytest.main([__file__])
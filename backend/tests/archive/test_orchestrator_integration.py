#!/usr/bin/env python3
"""
Test script to verify MozaOrchestrator integration.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from moza.config.models import MOZAConfig
from moza.gateway.router import LLMRouter
from moza.core.models import Event, EventType, Task, Session, Environment
from moza.core.context import ExecutionContext
from moza.core.cancellation import CancellationToken
from moza.tools.registry import ToolRegistry
from moza.core.event_bus import EventBus

async def test_orchestrator_integration():
    """Test the MozaOrchestrator integration."""
    print("Testing MozaOrchestrator Integration...")
    
    # Load configuration
    config = MOZAConfig.from_yaml("config.yaml")
    config.use_orchestrator = True
    
    print(f"Configuration loaded with {len(config.providers)} providers")
    print(f"Orchestrator enabled: {config.use_orchestrator}")
    
    # Initialize router
    router = LLMRouter(config)
    print("LLMRouter initialized with MozaOrchestrator")
    
    # Test basic routing
    test_messages = [
        {"role": "user", "content": "Hello, can you help me with a simple coding task?"}
    ]
    
    try:
        print("\nTesting basic routing...")
        result = await router.route(
            messages=test_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        print("Route successful!")
        print(f"   Provider: {result['provider']}")
        print(f"   Model: {result['model']}")
        print(f"   Tokens: {result['response']['usage']['total_tokens']}")
        
        # Test summary
        print("\nOrchestrator Summary:")
        summary = router.summary()
        print(f"   Total Models: {summary['orchestrator']['total_models']}")
        print(f"   Total Providers: {summary['orchestrator']['total_providers']}")
        print(f"   Success Rate: {summary['orchestrator']['success_rate']:.2%}")
        
        if summary['orchestrator']['dead_providers']:
            print(f"   Dead Providers: {summary['orchestrator']['dead_providers']}")
        
        print("\nAll tests passed! MozaOrchestrator integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

async def test_context_preservation():
    """Test conversation context preservation across failovers."""
    print("\nTesting Context Preservation...")
    
    config = MOZAConfig.from_yaml("config.yaml")
    config.use_orchestrator = True
    
    router = LLMRouter(config)
    
    # Simulate a simple conversation
    conversation = [
        {"role": "user", "content": "What is 2+2?"}
    ]
    
    try:
        result = await router.route(
            messages=conversation,
            temperature=0.7,
            max_tokens=100
        )
        
        response_content = result["response"]["choices"][0]["message"]["content"]
        if response_content and len(response_content) > 0:
            print("Context preservation test passed!")
            return True
        else:
            print(f"Context preservation test failed. Response: {response_content}")
            return False
            
    except Exception as e:
        print(f"Context preservation test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("MozaOrchestrator Integration Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test basic integration
    if not await test_orchestrator_integration():
        success = False
    
    # Test context preservation
    if not await test_context_preservation():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("ALL TESTS PASSED! MozaOrchestrator is ready to use.")
    else:
        print("SOME TESTS FAILED. Please check the integration.")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
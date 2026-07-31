#!/usr/bin/env python3
"""Test script to verify MozaOrchestrator integration from backend directory."""

import asyncio
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from moza.config.models import MOZAConfig
from moza.gateway.router import LLMRouter

async def test_orchestrator():
    """Test the MozaOrchestrator integration."""
    print("Testing MozaOrchestrator Integration...")
    
    # Load configuration
    config = MOZAConfig.from_yaml("../../config.yaml")
    config.use_orchestrator = True
    
    print(f"Configuration loaded with {len(config.providers)} providers")
    print(f"Orchestrator enabled: {config.use_orchestrator}")
    
    # Initialize router
    router = LLMRouter(config)
    print("LLMRouter initialized")
    
    # Check if we're using orchestrator
    if router._use_orchestrator:
        print("SUCCESS: Using MozaOrchestrator mode")
        
        # Test basic routing
        test_messages = [
            {"role": "user", "content": "Can you help me write a Python function to calculate the factorial of a number?"}
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
            print(f"   Total Models: {summary['orchestrator'].get('total_models', 'N/A')}")
            print(f"   Total Providers: {summary['orchestrator'].get('total_providers', 'N/A')}")
            print(f"   Success Rate: {summary['orchestrator'].get('success_rate', 0):.2%}")
            
            if summary['orchestrator'].get('dead_providers'):
                print(f"   Dead Providers: {summary['orchestrator']['dead_providers']}")
            
            print("\nAll tests passed! MozaOrchestrator integration is working correctly.")
            return True
            
        except Exception as e:
            print(f"Test failed: {str(e)}")
            return False
    else:
        print("FAILED: Using fallback mode instead of orchestrator")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_orchestrator())
    sys.exit(0 if success else 1)
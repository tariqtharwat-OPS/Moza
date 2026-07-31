"""
Example usage of Moza Orchestrator.

This script demonstrates how to use the orchestrator for different types of requests.
"""

import asyncio
import time
from moza_orchestrator import MozaOrchestrator


async def basic_example():
    """Basic example with a simple request."""
    print("=== Basic Example ===")
    
    orchestrator = MozaOrchestrator()
    
    messages = [
        {"role": "user", "content": "Hello! Can you tell me about Python?"}
    ]
    
    try:
        start_time = time.time()
        response = await orchestrator.complete(messages)
        duration = time.time() - start_time
        
        print(f"Response: {response}")
        print(f"Duration: {duration:.2f}s")
        
        stats = orchestrator.get_stats()
        print(f"Stats: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")


async def code_example():
    """Example with a coding task."""
    print("\n=== Code Example ===")
    
    orchestrator = MozaOrchestrator()
    
    messages = [
        {"role": "user", "content": "Write a Python function to calculate the factorial of a number."}
    ]
    
    try:
        response = await orchestrator.complete(messages)
        print(f"Code response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")


async def large_context_example():
    """Example with a large context request."""
    print("\n=== Large Context Example ===")
    
    orchestrator = MozaOrchestrator()
    
    # Create a large context (simulated)
    large_text = "This is a detailed explanation of machine learning. " * 1000
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": f"Summarize this text: {large_text}"}
    ]
    
    try:
        response = await orchestrator.complete(messages, max_tokens=500)
        print(f"Summary: {response}")
        
    except Exception as e:
        print(f"Error: {e}")


async def streaming_example():
    """Example with streaming response."""
    print("\n=== Streaming Example ===")
    
    orchestrator = MozaOrchestrator()
    
    messages = [
        {"role": "user", "content": "Tell me a story about a robot learning to paint."}
    ]
    
    try:
        # Note: Streaming is handled internally for now
        # In a real implementation, you would get chunks
        response = await orchestrator.complete(messages, stream=True)
        print(f"Story: {response}")
        
    except Exception as e:
        print(f"Error: {e}")


async def failover_demo():
    """Demonstrate failover behavior."""
    print("\n=== Failover Demo ===")
    
    orchestrator = MozaOrchestrator()
    
    # This will likely trigger failover if the first provider is rate limited
    messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    try:
        # Make multiple rapid requests to trigger rate limiting
        for i in range(5):
            print(f"Request {i+1}")
            response = await orchestrator.complete(messages)
            print(f"Response: {response}")
            time.sleep(0.1)  # Small delay between requests
            
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all examples."""
    print("Moza Orchestrator Examples")
    print("=" * 50)
    
    await basic_example()
    await code_example()
    await large_context_example()
    await streaming_example()
    await failover_demo()
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
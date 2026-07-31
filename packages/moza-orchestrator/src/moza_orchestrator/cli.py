"""
Command-line interface for Moza Orchestrator.
"""

import argparse
import asyncio
import json
import sys
from typing import List, Dict, Any

from moza_orchestrator import MozaOrchestrator


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)


async def chat_mode(orchestrator: MozaOrchestrator):
    """Interactive chat mode."""
    print("Moza Orchestrator Chat Mode")
    print("Type 'quit' or 'exit' to end the conversation")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                break
            
            messages = [{"role": "user", "content": user_input}]
            
            response = await orchestrator.complete(messages)
            print(f"Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


async def single_request(orchestrator: MozaOrchestrator, message: str):
    """Make a single request."""
    try:
        messages = [{"role": "user", "content": message}]
        response = await orchestrator.complete(messages)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")


async def stats_mode(orchestrator: MozaOrchestrator):
    """Show statistics mode."""
    stats = orchestrator.get_stats()
    print("Moza Orchestrator Statistics")
    print("=" * 30)
    print(f"Total calls: {stats['total_calls']}")
    print(f"Successful calls: {stats['successful_calls']}")
    print(f"Failed calls: {stats['failed_calls']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    
    if stats['dead_providers']:
        print(f"Dead providers: {', '.join(stats['dead_providers'])}")
    
    if stats['cooldown_providers']:
        print("Providers in cooldown:")
        for provider, remaining in stats['cooldown_providers'].items():
            print(f"  {provider}: {remaining}s remaining")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Moza Orchestrator CLI")
    parser.add_argument("--config", "-c", default="config.json", 
                       help="Configuration file path")
    parser.add_argument("--message", "-m", 
                       help="Message to send (single request mode)")
    parser.add_argument("--stats", "-s", action="store_true",
                       help="Show statistics")
    parser.add_argument("--chat", action="store_true",
                       help="Interactive chat mode")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize orchestrator
    orchestrator = MozaOrchestrator(config)
    
    # Run appropriate mode
    if args.stats:
        asyncio.run(stats_mode(orchestrator))
    elif args.message:
        asyncio.run(single_request(orchestrator, args.message))
    elif args.chat:
        asyncio.run(chat_mode(orchestrator))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script to verify LLM context logging is working
"""

from llms.llm_models import LLMModels
import sys
import os
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Configure logging to see the output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_llm_context_logging():
    """Test that LLM calls are properly logged with context"""

    print("[TEST] Testing LLM context logging...")

    # Initialize LLM client
    llm = LLMModels()

    # Test different contexts
    test_cases = [
        {
            "prompt": "Analyze the trending topic: AI in education",
            "context": "content_strategy_analysis",
            "description": "Content Strategy Analysis"
        },
        {
            "prompt": "Generate suggestions for engaging social media posts",
            "context": "content_suggestions",
            "description": "Content Suggestions"
        },
        {
            "prompt": "Format this data for Discord display",
            "context": "discord_embed_formatting",
            "description": "Discord Formatting"
        }
    ]

    print(f"[INFO] Running {len(test_cases)} test cases...")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test_case['description']}")
        print(f"[CONTEXT] {test_case['context']}")

        try:
            # This should trigger the context logging
            response = llm.call_openai(
                prompt=test_case["prompt"],
                system_prompt="You are a helpful assistant.",
                model="gpt-4o-mini",
                max_tokens=100,
                context=test_case["context"]
            )

            if response:
                print(
                    f"[SUCCESS] Response received (length: {len(response)} chars)")
            else:
                print(f"[WARNING] No response received")

        except Exception as e:
            print(f"[ERROR] Test failed: {e}")

    print(f"\n[COMPLETE] LLM context logging test completed!")
    print("[INFO] Check the logs above for [LLM_REQUEST] and [LLM_SUCCESS] entries")


if __name__ == "__main__":
    test_llm_context_logging()

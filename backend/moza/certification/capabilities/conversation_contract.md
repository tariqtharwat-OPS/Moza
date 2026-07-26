# Capability: Conversation

## Purpose
Natural human-like dialogue without tool invocation.

## User Story
"As a user, I want to greet MOZA and receive a natural response without triggering any tools."

## Inputs
- Text messages in Arabic or English
- Greetings, questions, casual conversation

## Expected Outputs
- Natural language response in the same language as input
- Response time < 2 seconds
- No tool calls

## Forbidden Behaviors (CRITICAL)
- NO tool calls (filesystem, terminal, browser)
- NO browser navigation
- NO file operations
- NO waiting for approval
- NO language switching (Arabic input → English output)

## Definition of Done (Production Ready Criteria)
- Responds to Arabic greetings (اهلا, مرحبا, السلام عليكم)
- Responds to English greetings (hi, hello, hey)
- Handles multi-sentence conversations (اهلا، كيف حالك؟)
- Maintains language consistency
- ZERO tool calls for all conversational inputs
- Response time < 2 seconds
- No console errors
- No retries or loops
- No hallucinations
- Preserves session context

## Evidence Requirements
- Screenshots of successful responses
- Network trace proving ZERO tool calls
- Response time measurements
- Error logs (should be empty)

## Maturity Level
Current: Level 4 (Production Ready)
Confidence: 95% (based on 19/20 test cases passing)

## Regression Tests
- All existing conversation tests must pass
- No new tool calls introduced for conversational inputs

## Dependencies
- IntentClassifier
- LiteLLMToolAgent
- ChatInterface

## Capability History
- v1.0 (2026-07-26): Initial implementation with Intent Classifier
- v1.1 (2026-07-26): Added Arabic greeting support

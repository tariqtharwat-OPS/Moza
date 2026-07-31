"""
Executive Mind: Deterministic Intent Classification

Bypasses the LLM tool-calling loop entirely for conversational input.
The Orchestrator MUST call classify_intent() BEFORE dispatching to any agent.
"""

import random
import re
from enum import Enum
from typing import Any


class IntentType(str, Enum):
    CONVERSATIONAL = "conversational"
    TASK = "task"


_WH_WORDS: set[str] = {
    "what", "who", "when", "where", "why", "how", "which",
}

_SHORT_ACK: set[str] = {
    "yes", "no", "sure", "ok", "okay", "thanks", "thank you",
    "thanks!", "thank you!",
}

_GREETING_EN: set[str] = {
    "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
    "good evening", "howdy", "sup", "yo", "hi there", "hello there",
    "hey there",
}

_GREETING_AR: set[str] = {
    "اهلا", "اهلاً", "مرحبا", "مرحباً", "السلام عليكم",
    "سلام", "هلا", "هلا وغلا", "أهلا", "أهلاً", "صباح الخير",
    "مساء الخير", "تحياتي",
}

_GREETING_PREFIX_EN: set[str] = {
    "say hello", "say hi", "tell hi", "greet me",
}

_GREETING_PREFIX_AR: set[str] = {
    "قل مرحبا", "قل مرحباً", "قل اهلا", "قل أهلا",
    "قل السلام عليكم", "حيه", "رحب", "سلم",
}

_CONVERSATIONAL_PHRASES: set[str] = {
    "how are you", "how's it going", "what's up", "whats up",
    "how are you doing", "how do you do", "nice to meet you",
    "how are things", "what's happening",
    "كيف حالك", "كيفك", "كيف الحال", "عامل ايه",
    "شلونك", "ازيك", "اخبارك", "شو اخبارك",
}


def _is_direct_greeting(text: str) -> bool:
    text_lower = text.lower().strip().rstrip("?!.,;:")
    return text_lower in _GREETING_EN or text_lower in _GREETING_AR


def _is_wh_question(text: str) -> bool:
    text_lower = text.lower().strip()
    for w in _WH_WORDS:
        if text_lower.startswith(w) and (len(text_lower) == len(w) or not text_lower[len(w)].isalpha()):
            return True
    return False


def _is_short_ack(text: str) -> bool:
    return text.lower().strip().rstrip("?!.,;:") in _SHORT_ACK


def _is_conversational_phrase(text: str) -> bool:
    text_lower = text.lower().strip().rstrip("?!.,;:")
    for phrase in _CONVERSATIONAL_PHRASES:
        if phrase in text_lower:
            return True
    return False


def _has_greeting_prefix(text: str) -> bool:
    text_lower = text.lower().strip()
    for prefix in _GREETING_PREFIX_EN:
        if text_lower.startswith(prefix):
            return True
    for prefix in _GREETING_PREFIX_AR:
        try:
            if text.startswith(prefix):
                return True
        except Exception:
            pass
    return False


def _has_arabic_greeting(text: str) -> bool:
    for g in _GREETING_AR:
        try:
            if g in text:
                return True
        except Exception:
            pass
    return False


def _is_very_short_utterance(text: str) -> bool:
    cleaned = text.strip().rstrip("?!.,;:")
    word_count = len(cleaned.split())
    return word_count <= 4


_ARABIC_REPLIES: list[str] = [
    "أهلاً بك! كيف يمكنني مساعدتك اليوم؟",
    "مرحباً! أنا هنا لمساعدتك.",
    "السلام عليكم! كيف أستطيع مساعدتك؟",
]

_HOW_ARE_YOU_REPLIES: list[str] = [
    "I'm doing great, thanks for asking! What can I help you with today?",
    "All good here! Ready to help. What do you need?",
    "I'm doing well! How can I assist you?",
]

_RETURN_GREETING_REPLIES: list[str] = [
    "Nice to see you again! What would you like to work on today?",
    "Welcome back! How can I assist you this time?",
    "Good to see you! What's on your mind?",
]

_ENGLISH_REPLIES: list[str] = [
    "Hello! How can I help you today?",
    "Hi there! I'm MOZA, your AI operating system. What can I do for you?",
    "Hey! Ready to help. What would you like to work on?",
]


def classify_intent(user_input: str) -> IntentType:
    text = user_input.strip()
    if not text:
        return IntentType.CONVERSATIONAL

    if _has_greeting_prefix(text):
        return IntentType.CONVERSATIONAL
    if _is_direct_greeting(text):
        return IntentType.CONVERSATIONAL
    if _is_conversational_phrase(text):
        return IntentType.CONVERSATIONAL
    if _has_arabic_greeting(text):
        return IntentType.CONVERSATIONAL
    if _is_short_ack(text):
        return IntentType.CONVERSATIONAL
    if _is_wh_question(text) and _is_very_short_utterance(text):
        return IntentType.CONVERSATIONAL

    return IntentType.TASK


def _prior_user_messages(history: list[Any]) -> list[str]:
    """Extract user messages from execution history."""
    msgs: list[str] = []
    for ev in history:
        if ev is None:
            continue
        if isinstance(ev, dict):
            payload = ev.get("payload", {}) or {}
        else:
            payload = getattr(ev, "payload", {}) or {}
        desc = payload.get("description")
        if isinstance(desc, str) and desc.strip():
            msgs.append(desc)
    return msgs


def _has_prior_greeting(history: list[Any]) -> bool:
    """Check if there's a prior greeting in the history (excluding the current message)."""
    prior = _prior_user_messages(history)
    if not prior:
        return False
    # Check all but the last (which is the current message)
    for msg in prior[:-1]:
        if _is_direct_greeting(msg) or _is_conversational_phrase(msg) or _has_arabic_greeting(msg):
            return True
    return False


def get_conversational_reply(user_input: str, history: list[Any] | None = None) -> str:
    """Return a contextual conversational reply."""
    text = user_input.strip()
    lower = text.lower()

    # Arabic greeting
    for g in _GREETING_AR:
        try:
            if g in text:
                return random.choice(_ARABIC_REPLIES)
        except Exception:
            pass

    # "how are you" variants → respond about self, then offer help
    if any(p in lower for p in (
        "how are you", "how's it going", "how are things", "how are you doing",
        "كيف حالك", "كيفك", "كيف الحال", "عامل ايه", "شلونك", "ازيك", "اخبارك", "شو اخبارك"
    )):
        return random.choice(_HOW_ARE_YOU_REPLIES)

    # Return greeting (prior greeting in this session)
    if history and _has_prior_greeting(history):
        return random.choice(_RETURN_GREETING_REPLIES)

    # Direct greeting / short ack / conversational phrase
    if _is_direct_greeting(text) or _is_short_ack(text) or _is_conversational_phrase(text):
        return random.choice(_ENGLISH_REPLIES)

    # Fallback
    return random.choice(_ENGLISH_REPLIES)

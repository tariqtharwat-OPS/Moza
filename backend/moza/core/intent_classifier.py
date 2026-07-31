"""
Executive Mind: Deterministic Intent Classification

Bypasses the LLM tool-calling loop entirely for conversational input.
The Orchestrator MUST call classify_intent() BEFORE dispatching to any agent.
"""

import re
from enum import Enum


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


def get_conversational_reply(user_input: str) -> str:
    text = user_input.strip()
    for g in _GREETING_AR:
        try:
            if g in text:
                return _ARABIC_REPLIES[0]
        except Exception:
            pass
    return _ENGLISH_REPLIES[0]

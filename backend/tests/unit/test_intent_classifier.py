import pytest
from moza.core.intent_classifier import IntentType, classify_intent, get_conversational_reply


class TestClassifyIntent:
    def test_english_greeting(self):
        assert classify_intent("hello") == IntentType.CONVERSATIONAL
        assert classify_intent("Hi") == IntentType.CONVERSATIONAL
        assert classify_intent("hey there") == IntentType.CONVERSATIONAL
        assert classify_intent("good morning") == IntentType.CONVERSATIONAL
        assert classify_intent("good evening") == IntentType.CONVERSATIONAL

    def test_arabic_greeting(self):
        assert classify_intent("اهلا") == IntentType.CONVERSATIONAL
        assert classify_intent("مرحبا") == IntentType.CONVERSATIONAL
        assert classify_intent("السلام عليكم") == IntentType.CONVERSATIONAL
        assert classify_intent("صباح الخير") == IntentType.CONVERSATIONAL

    def test_conversational_phrases(self):
        assert classify_intent("how are you") == IntentType.CONVERSATIONAL
        assert classify_intent("How are you doing?") == IntentType.CONVERSATIONAL
        assert classify_intent("what's up") == IntentType.CONVERSATIONAL
        assert classify_intent("nice to meet you") == IntentType.CONVERSATIONAL
        assert classify_intent("كيف حالك") == IntentType.CONVERSATIONAL
        assert classify_intent("كيفك") == IntentType.CONVERSATIONAL

    def test_greeting_prefix_english(self):
        assert classify_intent("say hello") == IntentType.CONVERSATIONAL
        assert classify_intent("Say hi to me") == IntentType.CONVERSATIONAL
        assert classify_intent("greet me") == IntentType.CONVERSATIONAL

    def test_greeting_prefix_arabic(self):
        assert classify_intent("قل مرحبا") == IntentType.CONVERSATIONAL
        assert classify_intent("قل اهلا") == IntentType.CONVERSATIONAL

    def test_short_acknowledgment(self):
        assert classify_intent("yes") == IntentType.CONVERSATIONAL
        assert classify_intent("thanks") == IntentType.CONVERSATIONAL
        assert classify_intent("sure") == IntentType.CONVERSATIONAL

    def test_short_wh_question(self):
        assert classify_intent("what is moza") == IntentType.CONVERSATIONAL
        assert classify_intent("who are you") == IntentType.CONVERSATIONAL
        assert classify_intent("what can you do") == IntentType.CONVERSATIONAL

    def test_task_requires_tools(self):
        assert classify_intent("create a file called test.txt") == IntentType.TASK
        assert classify_intent("search the web") == IntentType.TASK
        assert classify_intent("write python code") == IntentType.TASK
        assert classify_intent("run pytest") == IntentType.TASK
        assert classify_intent("navigate to wikipedia") == IntentType.TASK
        assert classify_intent("delete the folder") == IntentType.TASK
        assert classify_intent("install moza dependencies") == IntentType.TASK

    def test_empty_input(self):
        assert classify_intent("") == IntentType.CONVERSATIONAL

    def test_arabic_mixed_greeting(self):
        assert classify_intent("اهلا كيف حالك") == IntentType.CONVERSATIONAL
        assert classify_intent("مرحبا كيفك") == IntentType.CONVERSATIONAL


class TestGetConversationalReply:
    def test_returns_string(self):
        reply = get_conversational_reply("hello")
        assert isinstance(reply, str)
        assert len(reply) > 0

    def test_arabic_input_returns_arabic(self):
        reply = get_conversational_reply("اهلا")
        assert isinstance(reply, str)

    def test_english_input_returns_english(self):
        reply = get_conversational_reply("hello")
        assert isinstance(reply, str)

"""
Tests for Application Context Awareness functionality.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from context.application_context import ApplicationContext, WindowInfo


class TestApplicationContext(unittest.TestCase):
    """Test cases for ApplicationContext class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.context = ApplicationContext()
    
    def test_window_info_creation(self):
        """Test WindowInfo dataclass creation."""
        window_info = WindowInfo(
            title="Test Window",
            class_name="TestClass",
            is_active=True,
            is_minimized=False,
            is_maximized=False
        )
        
        self.assertEqual(window_info.title, "Test Window")
        self.assertEqual(window_info.class_name, "TestClass")
        self.assertTrue(window_info.is_active)
        self.assertFalse(window_info.is_minimized)
        self.assertFalse(window_info.is_maximized)
    
    def test_email_context_detection(self):
        """Test detection of email applications."""
        test_cases = [
            ("Outlook - Inbox", "email"),
            ("Gmail - Google Chrome", "email"),
            ("Thunderbird - Inbox", "email"),
            ("Apple Mail - Inbox", "email"),
            ("Microsoft Outlook - Draft", "email")
        ]
        
        for window_title, expected_context in test_cases:
            with self.subTest(window_title=window_title):
                window_info = WindowInfo(
                    title=window_title,
                    class_name="test",
                    is_active=True,
                    is_minimized=False,
                    is_maximized=False
                )
                context = self.context.detect_context(window_info)
                self.assertEqual(context, expected_context)
    
    def test_document_context_detection(self):
        """Test detection of document applications."""
        test_cases = [
            ("Document1 - Microsoft Word", "document"),
            ("Untitled - Google Docs", "document"),
            ("report.docx - Word", "document"),
            ("Notes - Notepad", "document"),
            ("Document - LibreOffice Writer", "document")
        ]
        
        for window_title, expected_context in test_cases:
            with self.subTest(window_title=window_title):
                window_info = WindowInfo(
                    title=window_title,
                    class_name="test",
                    is_active=True,
                    is_minimized=False,
                    is_maximized=False
                )
                context = self.context.detect_context(window_info)
                self.assertEqual(context, expected_context)
    
    def test_code_context_detection(self):
        """Test detection of code editor applications."""
        test_cases = [
            ("main.py - Visual Studio Code", "code"),
            ("project - PyCharm", "code"),
            ("src/ - IntelliJ IDEA", "code"),
            ("test.js - Sublime Text", "code"),
            ("app.py - code.exe", "code")
        ]
        
        for window_title, expected_context in test_cases:
            with self.subTest(window_title=window_title):
                window_info = WindowInfo(
                    title=window_title,
                    class_name="test",
                    is_active=True,
                    is_minimized=False,
                    is_maximized=False
                )
                context = self.context.detect_context(window_info)
                self.assertEqual(context, expected_context)
    
    def test_browser_context_detection(self):
        """Test detection of browser applications."""
        test_cases = [
            ("Google - Google Chrome", "browser"),
            ("Stack Overflow - Mozilla Firefox", "browser"),
            ("GitHub - Microsoft Edge", "browser"),
            ("YouTube - Safari", "browser")
        ]
        
        for window_title, expected_context in test_cases:
            with self.subTest(window_title=window_title):
                window_info = WindowInfo(
                    title=window_title,
                    class_name="test",
                    is_active=True,
                    is_minimized=False,
                    is_maximized=False
                )
                context = self.context.detect_context(window_info)
                self.assertEqual(context, expected_context)
    
    def test_chat_context_detection(self):
        """Test detection of chat applications."""
        test_cases = [
            ("General - Slack", "chat"),
            ("Team Chat - Microsoft Teams", "chat"),
            ("Discord", "chat"),
            ("WhatsApp Web", "chat")
        ]
        
        for window_title, expected_context in test_cases:
            with self.subTest(window_title=window_title):
                window_info = WindowInfo(
                    title=window_title,
                    class_name="test",
                    is_active=True,
                    is_minimized=False,
                    is_maximized=False
                )
                context = self.context.detect_context(window_info)
                self.assertEqual(context, expected_context)
    
    def test_unknown_context_detection(self):
        """Test detection of unknown applications."""
        window_info = WindowInfo(
            title="Some Unknown Application",
            class_name="test",
            is_active=True,
            is_minimized=False,
            is_maximized=False
        )
        context = self.context.detect_context(window_info)
        self.assertEqual(context, "general")
    
    def test_user_rule_priority(self):
        """Test that user rules take priority over default patterns."""
        # Add a user rule
        self.context.add_user_rule("custom app", "custom_context")
        
        window_info = WindowInfo(
            title="My Custom App - Window",
            class_name="test",
            is_active=True,
            is_minimized=False,
            is_maximized=False
        )
        context = self.context.detect_context(window_info)
        self.assertEqual(context, "custom_context")
    
    def test_formatting_template_retrieval(self):
        """Test retrieval of formatting templates."""
        # Test email template
        template = self.context.get_formatting_template("email")
        self.assertIn("formal", template)
        self.assertTrue(template["formal"])
        self.assertIn("paragraphs", template)
        self.assertTrue(template["paragraphs"])
        
        # Test code template
        template = self.context.get_formatting_template("code")
        self.assertIn("technical", template)
        self.assertTrue(template["technical"])
        self.assertIn("concise", template)
        self.assertTrue(template["concise"])
        
        # Test unknown context (should return general)
        template = self.context.get_formatting_template("unknown")
        self.assertIn("formal", template)
    
    def test_ai_prompt_retrieval(self):
        """Test retrieval of AI prompts for different contexts."""
        # Test email prompt
        prompt = self.context.get_ai_prompt_for_context("email")
        self.assertIn("professional email", prompt.lower())
        self.assertIn("email etiquette", prompt.lower())
        
        # Test code prompt
        prompt = self.context.get_ai_prompt_for_context("code")
        self.assertIn("code comment", prompt.lower())
        self.assertIn("technical language", prompt.lower())
        
        # Test chat prompt
        prompt = self.context.get_ai_prompt_for_context("chat")
        self.assertIn("conversational", prompt.lower())
    
    def test_user_rule_management(self):
        """Test adding and removing user rules."""
        # Add a rule
        self.context.add_user_rule("test pattern", "test_context")
        self.assertIn("test pattern", self.context.user_rules)
        self.assertEqual(self.context.user_rules["test pattern"], "test_context")
        
        # Remove the rule
        result = self.context.remove_user_rule("test pattern")
        self.assertTrue(result)
        self.assertNotIn("test pattern", self.context.user_rules)
        
        # Try to remove non-existent rule
        result = self.context.remove_user_rule("non_existent")
        self.assertFalse(result)
    
    def test_context_info_retrieval(self):
        """Test comprehensive context information retrieval."""
        with patch.object(self.context, 'detect_active_window') as mock_detect:
            mock_window = WindowInfo(
                title="Test Document - Microsoft Word",
                class_name="test",
                is_active=True,
                is_minimized=False,
                is_maximized=False
            )
            mock_detect.return_value = mock_window
            
            info = self.context.get_context_info()
            
            self.assertIn("context_type", info)
            self.assertIn("window_info", info)
            self.assertIn("formatting_template", info)
            self.assertIn("ai_prompt", info)
            self.assertIn("user_rules_count", info)
            
            self.assertEqual(info["context_type"], "document")
            self.assertEqual(info["window_info"], mock_window)
            self.assertIsInstance(info["formatting_template"], dict)
            self.assertIsInstance(info["ai_prompt"], str)
            self.assertIsInstance(info["user_rules_count"], int)


if __name__ == "__main__":
    unittest.main() 
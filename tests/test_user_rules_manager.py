"""
Tests for User Rules Manager functionality.
"""

import unittest
import tempfile
import json
import os
import sys
from unittest.mock import patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from context.user_rules_manager import UserRulesManager


class TestUserRulesManager(unittest.TestCase):
    """Test cases for UserRulesManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.rules_manager = UserRulesManager(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_add_context_mapping(self):
        """Test adding context mapping rules."""
        # Add a context mapping
        result = self.rules_manager.add_context_mapping("custom_app", "document", 2)
        self.assertTrue(result)
        
        # Verify the mapping was added
        mappings = self.rules_manager.get_context_mappings()
        self.assertIn("custom_app", mappings)
        self.assertEqual(mappings["custom_app"]["context_type"], "document")
        self.assertEqual(mappings["custom_app"]["priority"], 2)
    
    def test_remove_context_mapping(self):
        """Test removing context mapping rules."""
        # Add a mapping first
        self.rules_manager.add_context_mapping("test_app", "email")
        
        # Remove the mapping
        result = self.rules_manager.remove_context_mapping("test_app")
        self.assertTrue(result)
        
        # Verify it was removed
        mappings = self.rules_manager.get_context_mappings()
        self.assertNotIn("test_app", mappings)
    
    def test_add_formatting_template(self):
        """Test adding formatting templates."""
        template = {
            'formal': True,
            'paragraphs': True,
            'capitalization': 'sentence'
        }
        
        result = self.rules_manager.add_formatting_template("custom_context", template)
        self.assertTrue(result)
        
        # Verify the template was added
        retrieved_template = self.rules_manager.get_formatting_template("custom_context")
        self.assertEqual(retrieved_template, template)
    
    def test_update_formatting_template(self):
        """Test updating formatting templates."""
        # Add initial template
        initial_template = {'formal': True}
        self.rules_manager.add_formatting_template("test_context", initial_template)
        
        # Update template
        updated_template = {'formal': True, 'paragraphs': True}
        result = self.rules_manager.update_formatting_template("test_context", updated_template)
        self.assertTrue(result)
        
        # Verify the template was updated
        retrieved_template = self.rules_manager.get_formatting_template("test_context")
        self.assertEqual(retrieved_template, updated_template)
    
    def test_add_correction(self):
        """Test adding user corrections for learning."""
        # Add a correction
        self.rules_manager.add_correction(
            "Microsoft Word - Document.docx",
            "general",
            "document",
            0.9
        )
        
        # Verify correction was added
        stats = self.rules_manager.get_accuracy_stats()
        self.assertEqual(stats['total_corrections'], 1)
    
    def test_get_learning_suggestions(self):
        """Test getting learning suggestions."""
        # Add some corrections
        self.rules_manager.add_correction("Microsoft Word - Doc1.docx", "general", "document")
        self.rules_manager.add_correction("Microsoft Word - Doc2.docx", "general", "document")
        self.rules_manager.add_correction("Microsoft Word - Doc3.docx", "general", "email")
        
        # Get suggestions for a similar window title
        suggestions = self.rules_manager.get_learning_suggestions("Microsoft Word - NewDoc.docx")
        
        # Should have suggestions based on "word" pattern
        self.assertGreater(len(suggestions), 0)
        
        # Check that suggestions are sorted by confidence
        if len(suggestions) > 1:
            self.assertGreaterEqual(suggestions[0][1], suggestions[1][1])
    
    def test_get_accuracy_stats(self):
        """Test getting accuracy statistics."""
        # Add some corrections
        self.rules_manager.add_correction("App1", "general", "document")
        self.rules_manager.add_correction("App2", "general", "document")
        self.rules_manager.add_correction("App3", "document", "email")  # Wrong detection
        
        stats = self.rules_manager.get_accuracy_stats()
        
        self.assertEqual(stats['total_corrections'], 3)
        self.assertIn('general', stats['accuracy_by_context'])
        self.assertIn('document', stats['accuracy_by_context'])
        
        # General context should have 0% accuracy (2 wrong out of 2)
        self.assertEqual(stats['accuracy_by_context']['general'], 0.0)
    
    def test_export_import_rules(self):
        """Test exporting and importing rules."""
        # Add some rules
        self.rules_manager.add_context_mapping("test_app", "document")
        self.rules_manager.add_formatting_template("test_context", {'formal': True})
        
        # Export rules
        export_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        export_file.close()
        
        try:
            result = self.rules_manager.export_rules(export_file.name)
            self.assertTrue(result)
            
            # Create new manager and import rules
            new_manager = UserRulesManager()
            result = new_manager.import_rules(export_file.name)
            self.assertTrue(result)
            
            # Verify rules were imported
            mappings = new_manager.get_context_mappings()
            self.assertIn("test_app", mappings)
            
            template = new_manager.get_formatting_template("test_context")
            self.assertEqual(template, {'formal': True})
            
        finally:
            if os.path.exists(export_file.name):
                os.unlink(export_file.name)
    
    def test_reset_rules(self):
        """Test resetting all rules."""
        # Add some rules
        self.rules_manager.add_context_mapping("test_app", "document")
        self.rules_manager.add_formatting_template("test_context", {'formal': True})
        
        # Reset rules
        result = self.rules_manager.reset_rules()
        self.assertTrue(result)
        
        # Verify rules were reset
        mappings = self.rules_manager.get_context_mappings()
        self.assertEqual(len(mappings), 0)
        
        template = self.rules_manager.get_formatting_template("test_context")
        self.assertIsNone(template)
    
    def test_extract_pattern_from_title(self):
        """Test pattern extraction from window titles."""
        # Test with known patterns
        patterns = [
            ("Microsoft Word - Document.docx", "word"),
            ("Outlook - Inbox", "outlook"),
            ("Chrome - Google", "chrome"),
            ("Visual Studio Code", "code"),
            ("Slack - Workspace", "slack")
        ]
        
        for title, expected_pattern in patterns:
            pattern = self.rules_manager._extract_pattern_from_title(title)
            self.assertEqual(pattern, expected_pattern)
        
        # Test with unknown pattern
        pattern = self.rules_manager._extract_pattern_from_title("Unknown Application")
        self.assertIsNone(pattern)
    
    def test_file_persistence(self):
        """Test that rules are persisted to file."""
        # Add a rule
        self.rules_manager.add_context_mapping("persistent_app", "email")
        
        # Create new manager with same file
        new_manager = UserRulesManager(self.temp_file.name)
        
        # Verify rule was loaded
        mappings = new_manager.get_context_mappings()
        self.assertIn("persistent_app", mappings)
        self.assertEqual(mappings["persistent_app"]["context_type"], "email")


if __name__ == '__main__':
    unittest.main() 
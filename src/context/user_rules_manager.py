"""
User Rules Manager for Context Customization

This module provides functionality for users to customize context mappings
and formatting templates, with learning capability to improve context detection.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class UserRulesManager:
    """
    Manages user-defined context rules and learning capabilities.
    
    This class allows users to customize context mappings and formatting
    templates, and provides a feedback system for learning from user corrections.
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize the user rules manager.
        
        Args:
            rules_file: Path to the rules file, or None for default location
        """
        self.rules_file = rules_file or ".taskmaster/user_rules.json"
        self.rules_path = Path(self.rules_file)
        
        # User-defined context rules
        self.user_rules = {
            'context_mappings': {},  # pattern -> context_type
            'formatting_templates': {},  # context_type -> template
            'learning_data': {
                'corrections': [],
                'frequency': {},
                'accuracy': {}
            }
        }
        
        # Load existing rules
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load user rules from file."""
        try:
            if self.rules_path.exists():
                with open(self.rules_path, 'r') as f:
                    self.user_rules = json.load(f)
                logger.info(f"Loaded user rules from {self.rules_path}")
            else:
                logger.info("No existing user rules found, starting with defaults")
        except Exception as e:
            logger.error(f"Error loading user rules: {e}")
    
    def _save_rules(self) -> None:
        """Save user rules to file."""
        try:
            # Ensure directory exists
            self.rules_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.rules_path, 'w') as f:
                json.dump(self.user_rules, f, indent=2)
            logger.info(f"Saved user rules to {self.rules_path}")
        except Exception as e:
            logger.error(f"Error saving user rules: {e}")
    
    def add_context_mapping(self, pattern: str, context_type: str, priority: int = 1) -> bool:
        """
        Add a user-defined context mapping rule.
        
        Args:
            pattern: Pattern to match in window title
            context_type: Context type to assign
            priority: Priority level (higher = more important)
            
        Returns:
            True if rule was added successfully
        """
        try:
            self.user_rules['context_mappings'][pattern] = {
                'context_type': context_type,
                'priority': priority,
                'created': datetime.now().isoformat()
            }
            self._save_rules()
            logger.info(f"Added context mapping: {pattern} -> {context_type}")
            return True
        except Exception as e:
            logger.error(f"Error adding context mapping: {e}")
            return False
    
    def remove_context_mapping(self, pattern: str) -> bool:
        """
        Remove a user-defined context mapping rule.
        
        Args:
            pattern: Pattern to remove
            
        Returns:
            True if rule was removed successfully
        """
        try:
            if pattern in self.user_rules['context_mappings']:
                del self.user_rules['context_mappings'][pattern]
                self._save_rules()
                logger.info(f"Removed context mapping: {pattern}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing context mapping: {e}")
            return False
    
    def get_context_mappings(self) -> Dict[str, Any]:
        """
        Get all user-defined context mappings.
        
        Returns:
            Dictionary of context mappings
        """
        return self.user_rules['context_mappings'].copy()
    
    def add_formatting_template(self, context_type: str, template: Dict[str, Any]) -> bool:
        """
        Add or update a user-defined formatting template.
        
        Args:
            context_type: Context type for the template
            template: Formatting template dictionary
            
        Returns:
            True if template was added successfully
        """
        try:
            self.user_rules['formatting_templates'][context_type] = {
                'template': template,
                'created': datetime.now().isoformat(),
                'updated': datetime.now().isoformat()
            }
            self._save_rules()
            logger.info(f"Added formatting template for context: {context_type}")
            return True
        except Exception as e:
            logger.error(f"Error adding formatting template: {e}")
            return False
    
    def update_formatting_template(self, context_type: str, template: Dict[str, Any]) -> bool:
        """
        Update an existing formatting template.
        
        Args:
            context_type: Context type for the template
            template: Updated formatting template dictionary
            
        Returns:
            True if template was updated successfully
        """
        try:
            if context_type in self.user_rules['formatting_templates']:
                self.user_rules['formatting_templates'][context_type]['template'] = template
                self.user_rules['formatting_templates'][context_type]['updated'] = datetime.now().isoformat()
                self._save_rules()
                logger.info(f"Updated formatting template for context: {context_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating formatting template: {e}")
            return False
    
    def get_formatting_template(self, context_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a user-defined formatting template.
        
        Args:
            context_type: Context type to get template for
            
        Returns:
            Formatting template or None if not found
        """
        if context_type in self.user_rules['formatting_templates']:
            return self.user_rules['formatting_templates'][context_type]['template']
        return None
    
    def get_all_formatting_templates(self) -> Dict[str, Any]:
        """
        Get all user-defined formatting templates.
        
        Returns:
            Dictionary of formatting templates
        """
        return {
            context: data['template'] 
            for context, data in self.user_rules['formatting_templates'].items()
        }
    
    def add_correction(self, window_title: str, detected_context: str, 
                      corrected_context: str, confidence: float = 1.0) -> None:
        """
        Add a user correction for learning purposes.
        
        Args:
            window_title: Window title that was misclassified
            detected_context: Context that was incorrectly detected
            corrected_context: Correct context that should have been detected
            confidence: User's confidence in the correction (0.0-1.0)
        """
        correction = {
            'window_title': window_title,
            'detected_context': detected_context,
            'corrected_context': corrected_context,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        self.user_rules['learning_data']['corrections'].append(correction)
        
        # Update frequency data
        pattern = self._extract_pattern_from_title(window_title)
        if pattern:
            if pattern not in self.user_rules['learning_data']['frequency']:
                self.user_rules['learning_data']['frequency'][pattern] = {}
            
            if corrected_context not in self.user_rules['learning_data']['frequency'][pattern]:
                self.user_rules['learning_data']['frequency'][pattern][corrected_context] = 0
            
            self.user_rules['learning_data']['frequency'][pattern][corrected_context] += 1
        
        self._save_rules()
        logger.info(f"Added correction: {detected_context} -> {corrected_context}")
    
    def _extract_pattern_from_title(self, title: str) -> Optional[str]:
        """
        Extract a pattern from a window title for learning.
        
        Args:
            title: Window title
            
        Returns:
            Extracted pattern or None
        """
        # Simple pattern extraction - could be enhanced
        title_lower = title.lower()
        
        # Look for common application indicators
        patterns = [
            'outlook', 'word', 'excel', 'powerpoint', 'chrome', 'firefox',
            'code', 'visual studio', 'pycharm', 'intellij', 'slack', 'teams'
        ]
        
        for pattern in patterns:
            if pattern in title_lower:
                return pattern
        
        return None
    
    def get_learning_suggestions(self, window_title: str) -> List[Tuple[str, float]]:
        """
        Get context suggestions based on learning data.
        
        Args:
            window_title: Window title to get suggestions for
            
        Returns:
            List of (context_type, confidence) tuples
        """
        pattern = self._extract_pattern_from_title(window_title)
        if not pattern or pattern not in self.user_rules['learning_data']['frequency']:
            return []
        
        frequency_data = self.user_rules['learning_data']['frequency'][pattern]
        total = sum(frequency_data.values())
        
        suggestions = []
        for context_type, count in frequency_data.items():
            confidence = count / total
            suggestions.append((context_type, confidence))
        
        # Sort by confidence (highest first)
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions
    
    def get_accuracy_stats(self) -> Dict[str, Any]:
        """
        Get accuracy statistics for learning data.
        
        Returns:
            Dictionary with accuracy statistics
        """
        corrections = self.user_rules['learning_data']['corrections']
        
        if not corrections:
            return {'total_corrections': 0, 'accuracy_by_context': {}}
        
        # Calculate accuracy by context
        context_stats = {}
        for correction in corrections:
            detected = correction['detected_context']
            corrected = correction['corrected_context']
            
            if detected not in context_stats:
                context_stats[detected] = {'total': 0, 'correct': 0}
            
            context_stats[detected]['total'] += 1
            if detected == corrected:
                context_stats[detected]['correct'] += 1
        
        # Calculate accuracy percentages
        accuracy_by_context = {}
        for context, stats in context_stats.items():
            accuracy_by_context[context] = stats['correct'] / stats['total']
        
        return {
            'total_corrections': len(corrections),
            'accuracy_by_context': accuracy_by_context,
            'overall_accuracy': sum(stats['correct'] for stats in context_stats.values()) / 
                               sum(stats['total'] for stats in context_stats.values())
        }
    
    def export_rules(self, export_file: str) -> bool:
        """
        Export user rules to a file.
        
        Args:
            export_file: Path to export file
            
        Returns:
            True if export was successful
        """
        try:
            with open(export_file, 'w') as f:
                json.dump(self.user_rules, f, indent=2)
            logger.info(f"Exported user rules to {export_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting user rules: {e}")
            return False
    
    def import_rules(self, import_file: str) -> bool:
        """
        Import user rules from a file.
        
        Args:
            import_file: Path to import file
            
        Returns:
            True if import was successful
        """
        try:
            with open(import_file, 'r') as f:
                imported_rules = json.load(f)
            
            # Merge with existing rules
            self.user_rules['context_mappings'].update(imported_rules.get('context_mappings', {}))
            self.user_rules['formatting_templates'].update(imported_rules.get('formatting_templates', {}))
            
            self._save_rules()
            logger.info(f"Imported user rules from {import_file}")
            return True
        except Exception as e:
            logger.error(f"Error importing user rules: {e}")
            return False
    
    def reset_rules(self) -> bool:
        """
        Reset all user rules to defaults.
        
        Returns:
            True if reset was successful
        """
        try:
            self.user_rules = {
                'context_mappings': {},
                'formatting_templates': {},
                'learning_data': {
                    'corrections': [],
                    'frequency': {},
                    'accuracy': {}
                }
            }
            self._save_rules()
            logger.info("Reset all user rules to defaults")
            return True
        except Exception as e:
            logger.error(f"Error resetting user rules: {e}")
            return False 
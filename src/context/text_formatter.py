"""
Text Formatter for Context-Specific Formatting

This module provides functionality to format text according to the detected
application context, applying appropriate formatting rules and styles.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from .application_context import ApplicationContext

logger = logging.getLogger(__name__)


class ContextTextFormatter:
    """
    Formats text according to context-specific rules and templates.
    
    This class applies formatting rules based on the detected application
    context to ensure text is appropriately formatted for the target application.
    """
    
    def __init__(self, context: ApplicationContext):
        """
        Initialize the formatter with an application context.
        
        Args:
            context: ApplicationContext instance for context detection
        """
        self.context = context
        
        # Define formatting functions for different rules
        self.formatting_functions = {
            'formal': self._apply_formal_formatting,
            'paragraphs': self._apply_paragraph_formatting,
            'greeting': self._apply_greeting_formatting,
            'signature': self._apply_signature_formatting,
            'academic': self._apply_academic_formatting,
            'comment_style': self._apply_comment_formatting,
            'technical': self._apply_technical_formatting,
            'concise': self._apply_concise_formatting,
            'conversational': self._apply_conversational_formatting,
            'bullet_points': self._apply_bullet_point_formatting,
            'creative': self._apply_creative_formatting,
            'command_style': self._apply_command_formatting,
            'line_breaks': self._apply_line_break_formatting,
            'capitalization': self._apply_capitalization_formatting
        }
    
    def format_text(self, text: str, context_type: Optional[str] = None) -> str:
        """
        Format text according to the detected or specified context.
        
        Args:
            text: Raw text to format
            context_type: Specific context type, or None to detect automatically
            
        Returns:
            Formatted text according to context rules
        """
        if not text.strip():
            return text
        
        # Get context and formatting template
        if not context_type:
            context_type = self.context.detect_context()
        
        template = self.context.get_formatting_template(context_type)
        logger.debug(f"Formatting text for context: {context_type}")
        
        # Apply formatting rules in order
        formatted_text = text
        
        # Apply other formatting rules first
        for rule, value in template.items():
            if rule == 'capitalization':
                continue  # Apply capitalization last
            
            if value and rule in self.formatting_functions:
                formatted_text = self.formatting_functions[rule](formatted_text, value)
        
        # Apply capitalization last to ensure proper case after all other formatting
        if 'capitalization' in template:
            formatted_text = self._apply_capitalization_formatting(
                formatted_text, template['capitalization']
            )
        
        return formatted_text
    
    def _apply_formal_formatting(self, text: str, value: bool) -> str:
        """Apply formal formatting rules."""
        if not value:
            return text
        
        # Remove casual language and contractions
        replacements = {
            "don't": "do not",
            "can't": "cannot",
            "won't": "will not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "hasn't": "has not",
            "haven't": "have not",
            "hadn't": "had not",
            "doesn't": "does not",
            "didn't": "did not",
            "wouldn't": "would not",
            "couldn't": "could not",
            "shouldn't": "should not",
            "mightn't": "might not",
            "mustn't": "must not",
            "it's": "it is"
        }
        
        for casual, formal in replacements.items():
            # Use case-insensitive replacement
            text = re.sub(r'\b' + re.escape(casual) + r'\b', formal, text, flags=re.IGNORECASE)
        
        return text
    
    def _apply_paragraph_formatting(self, text: str, value: bool) -> str:
        """Apply paragraph formatting rules."""
        if not value:
            return text
        
        # Ensure proper paragraph structure
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Ensure proper sentence structure
                if not line.endswith(('.', '!', '?')):
                    line += '.'
                formatted_lines.append(line)
        
        return '\n\n'.join(formatted_lines)
    
    def _apply_greeting_formatting(self, text: str, value: bool) -> str:
        """Apply greeting formatting for emails."""
        if not value:
            return text
        
        # Check if there's already a professional greeting
        professional_greetings = ['dear']
        text_lower = text.lower()
        
        has_professional_greeting = any(greeting in text_lower for greeting in professional_greetings)
        
        if not has_professional_greeting:
            # Add professional greeting (in practice, this would be more sophisticated)
            return f"Dear [Recipient],\n\n{text}"
        
        return text
    
    def _apply_signature_formatting(self, text: str, value: bool) -> str:
        """Apply signature formatting."""
        if not value:
            return text
        
        # Check if signature already exists
        signature_indicators = ['best regards', 'sincerely', 'yours truly']
        text_lower = text.lower()
        
        has_signature = any(indicator in text_lower for indicator in signature_indicators)
        
        if not has_signature:
            return f"{text}\n\nBest regards,\n[Your Name]"
        
        return text
    
    def _apply_academic_formatting(self, text: str, value: bool) -> str:
        """Apply academic formatting rules."""
        if not value:
            return text
        
        # Remove informal language and ensure academic tone
        informal_words = ['gonna', 'wanna', 'gotta', 'kinda', 'sorta', 'yeah', 'okay']
        
        for word in informal_words:
            text = re.sub(r'\b' + re.escape(word) + r'\b', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _apply_comment_formatting(self, text: str, value: bool) -> str:
        """Apply code comment formatting."""
        if not value:
            return text
        
        # Format as code comment
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Add comment prefix if not present
                if not line.startswith(('#', '//', '/*', '--')):
                    # Don't capitalize here - let the capitalization formatter handle it
                    line = f"# {line}"
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _apply_technical_formatting(self, text: str, value: bool) -> str:
        """Apply technical language formatting."""
        if not value:
            return text
        
        # Ensure technical terms are properly capitalized
        technical_terms = ['api', 'url', 'http', 'https', 'json', 'xml', 'sql', 'html', 'css', 'js']
        
        for term in technical_terms:
            pattern = r'\b' + re.escape(term) + r'\b'
            replacement = term.upper()
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _apply_concise_formatting(self, text: str, value: bool) -> str:
        """Apply concise formatting rules."""
        if not value:
            return text
        
        # Remove unnecessary words and phrases
        verbose_phrases = [
            'in order to', 'due to the fact that', 'at this point in time',
            'in the event that', 'as a matter of fact', 'it is important to note that'
        ]
        
        for phrase in verbose_phrases:
            text = re.sub(r'\b' + re.escape(phrase) + r'\b', '', text, flags=re.IGNORECASE)
        
        # Remove redundant words
        redundant_words = ['very', 'really', 'quite', 'rather', 'somewhat']
        
        for word in redundant_words:
            text = re.sub(r'\b' + re.escape(word) + r'\b', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _apply_conversational_formatting(self, text: str, value: bool) -> str:
        """Apply conversational formatting rules."""
        if not value:
            return text
        
        # Make text more conversational
        formal_to_casual = {
            'therefore': 'so',
            'however': 'but',
            'furthermore': 'also',
            'moreover': 'plus',
            'subsequently': 'then',
            'consequently': 'so'
        }
        
        for formal, casual in formal_to_casual.items():
            text = re.sub(r'\b' + re.escape(formal) + r'\b', casual, text, flags=re.IGNORECASE)
        
        return text
    
    def _apply_bullet_point_formatting(self, text: str, value: bool) -> str:
        """Apply bullet point formatting."""
        if not value:
            return text
        
        # Convert text to bullet points if it contains multiple sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) > 1:
            bullet_points = []
            for sentence in sentences:
                if sentence:
                    bullet_points.append(f"• {sentence}")
            return '\n'.join(bullet_points)
        
        return text
    
    def _apply_creative_formatting(self, text: str, value: bool) -> str:
        """Apply creative formatting rules."""
        if not value:
            return text
        
        # Allow more creative language and formatting
        # This is a placeholder for creative formatting rules
        return text
    
    def _apply_command_formatting(self, text: str, value: bool) -> str:
        """Apply command-line formatting."""
        if not value:
            return text
        
        # Format as command-line text
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Add command prompt if not present
                if not line.startswith(('$', '>', 'C:\\', '/', '#')):
                    line = f"$ {line}"
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _apply_line_break_formatting(self, text: str, value: bool) -> str:
        """Apply line break formatting."""
        if not value:
            return text
        
        # Ensure proper line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excessive line breaks
        text = re.sub(r' +', ' ', text)  # Remove excessive spaces
        
        return text
    
    def _apply_capitalization_formatting(self, text: str, style: str) -> str:
        """Apply capitalization formatting."""
        if style == 'sentence':
            # Sentence case: First letter of each sentence capitalized
            sentences = re.split(r'([.!?]+\s*)', text)
            formatted_sentences = []
            
            for i, part in enumerate(sentences):
                if i % 2 == 0:  # Text part
                    if part.strip():
                        part = part.strip()
                        if part:
                            # Handle greetings and other special cases
                            if part.lower().startswith('dear '):
                                # Keep "Dear" capitalized and don't modify the greeting
                                formatted_sentences.append(part)
                            else:
                                # Only capitalize the first letter, preserve the rest
                                part = part[0].upper() + part[1:]
                                formatted_sentences.append(part)
                    else:
                        formatted_sentences.append(part)
                else:  # Punctuation part
                    formatted_sentences.append(part)
            
            return ''.join(formatted_sentences)
        
        elif style == 'title':
            # Title case: Capitalize important words
            words = text.split()
            formatted_words = []
            
            # Words to not capitalize (unless first or last)
            minor_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 'of', 'on', 'or', 'the', 'to', 'up'}
            
            for i, word in enumerate(words):
                if i == 0 or i == len(words) - 1 or word.lower() not in minor_words:
                    word = word.capitalize()
                else:
                    word = word.lower()
                formatted_words.append(word)
            
            return ' '.join(formatted_words)
        
        elif style == 'lowercase':
            # All lowercase
            return text.lower()
        
        elif style == 'uppercase':
            # All uppercase
            return text.upper()
        
        elif style == 'mixed':
            # Mixed case (preserve original)
            return text
        
        return text
    
    def get_formatting_summary(self, context_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of the formatting rules for a context.
        
        Args:
            context_type: Context type, or None to detect automatically
            
        Returns:
            Dictionary with formatting rules summary
        """
        if not context_type:
            context_type = self.context.detect_context()
        
        template = self.context.get_formatting_template(context_type)
        
        return {
            'context_type': context_type,
            'formatting_rules': template,
            'rules_count': len(template),
            'active_rules': [rule for rule, value in template.items() if value]
        } 
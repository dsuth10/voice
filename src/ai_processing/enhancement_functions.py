"""
Specialized Text Enhancement Functions

This module provides modular functions for specific text enhancement tasks
that can be used independently or in combination with the AITextProcessor.
"""

import re
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

from .text_enhancement import AITextProcessor, EnhancementResult


@dataclass
class EnhancementFunction:
    """Represents a text enhancement function with metadata."""
    name: str
    description: str
    function: Callable
    requires_ai: bool = False
    context_specific: bool = False


class EnhancementFunctions:
    """
    Collection of specialized text enhancement functions.
    
    Provides modular functions for grammar correction, punctuation,
    filler word removal, and other text improvements.
    """
    
    def __init__(self, ai_processor: Optional[AITextProcessor] = None):
        """
        Initialize enhancement functions.
        
        Args:
            ai_processor: Optional AITextProcessor for AI-powered enhancements
        """
        self.ai_processor = ai_processor
        self.functions: Dict[str, EnhancementFunction] = {}
        self._register_functions()
    
    def _register_functions(self):
        """Register all available enhancement functions."""
        # Rule-based functions (no AI required)
        self.functions.update({
            "remove_filler_words": EnhancementFunction(
                name="remove_filler_words",
                description="Remove common filler words and phrases",
                function=self.remove_filler_words,
                requires_ai=False
            ),
            "fix_basic_punctuation": EnhancementFunction(
                name="fix_basic_punctuation",
                description="Add basic punctuation where missing",
                function=self.fix_basic_punctuation,
                requires_ai=False
            ),
            "capitalize_proper_nouns": EnhancementFunction(
                name="capitalize_proper_nouns",
                description="Capitalize common proper nouns",
                function=self.capitalize_proper_nouns,
                requires_ai=False
            ),
            "fix_common_contractions": EnhancementFunction(
                name="fix_common_contractions",
                description="Fix common contraction errors",
                function=self.fix_common_contractions,
                requires_ai=False
            )
        })
        
        # AI-powered functions
        if self.ai_processor:
            self.functions.update({
                "ai_grammar_correction": EnhancementFunction(
                    name="ai_grammar_correction",
                    description="AI-powered grammar correction",
                    function=self.ai_grammar_correction,
                    requires_ai=True
                ),
                "ai_punctuation_enhancement": EnhancementFunction(
                    name="ai_punctuation_enhancement",
                    description="AI-powered punctuation enhancement",
                    function=self.ai_punctuation_enhancement,
                    requires_ai=True
                ),
                "ai_sentence_structure": EnhancementFunction(
                    name="ai_sentence_structure",
                    description="AI-powered sentence structure improvement",
                    function=self.ai_sentence_structure,
                    requires_ai=True
                )
            })
    
    def remove_filler_words(self, text: str) -> str:
        """
        Remove common filler words and phrases from text.
        
        Args:
            text: Input text
            
        Returns:
            Text with filler words removed
        """
        # Common filler words and phrases
        filler_patterns = [
            r'\b(um|uh|ah|er|hmm|like|you know|i mean|basically|actually|literally)\b',
            r'\b(sort of|kind of|type of|i guess|i think)\b',
            r'\b(so|well|right|okay|ok)\b(?=\s|$)',  # At end of sentences
            r'\b(just|really|very|quite|pretty)\b(?=\s+very|really|quite)',  # Redundant intensifiers
        ]
        
        enhanced_text = text
        for pattern in filler_patterns:
            enhanced_text = re.sub(pattern, '', enhanced_text, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        enhanced_text = re.sub(r'\s+', ' ', enhanced_text)
        enhanced_text = enhanced_text.strip()
        
        return enhanced_text
    
    def fix_basic_punctuation(self, text: str) -> str:
        """
        Add basic punctuation where missing.
        
        Args:
            text: Input text
            
        Returns:
            Text with basic punctuation added
        """
        # Add periods to sentences that don't end with punctuation
        sentences = re.split(r'([.!?]+)', text)
        enhanced_sentences = []
        
        for i, sentence in enumerate(sentences):
            if i % 2 == 0:  # Text part
                sentence = sentence.strip()
                if sentence and not sentence.endswith(('.', '!', '?')):
                    # Check if it looks like a complete sentence
                    if re.search(r'\b(and|but|or|so|because|however|therefore)\b', sentence, re.IGNORECASE):
                        # Likely a continuation, don't add period
                        pass
                    elif len(sentence.split()) > 3:  # Likely a complete sentence
                        sentence += '.'
            else:  # Punctuation part
                pass
            
            enhanced_sentences.append(sentence)
        
        enhanced_text = ''.join(enhanced_sentences)
        
        # Fix common punctuation issues
        enhanced_text = re.sub(r'\s+([.!?])', r'\1', enhanced_text)  # Remove spaces before punctuation
        enhanced_text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', enhanced_text)  # Add space after punctuation
        
        return enhanced_text
    
    def capitalize_proper_nouns(self, text: str) -> str:
        """
        Capitalize common proper nouns.
        
        Args:
            text: Input text
            
        Returns:
            Text with proper nouns capitalized
        """
        # Common proper nouns that should be capitalized
        proper_nouns = [
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
            'september', 'october', 'november', 'december',
            'javascript', 'python', 'java', 'c++', 'html', 'css', 'sql', 'react',
            'node.js', 'express', 'django', 'flask', 'angular', 'vue', 'typescript',
            'github', 'git', 'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'iphone', 'android', 'windows', 'mac', 'linux', 'ubuntu', 'centos',
            'microsoft', 'apple', 'google', 'amazon', 'facebook', 'twitter', 'linkedin'
        ]
        
        enhanced_text = text
        
        # Capitalize proper nouns
        for noun in proper_nouns:
            pattern = r'\b' + re.escape(noun) + r'\b'
            enhanced_text = re.sub(pattern, noun.title(), enhanced_text, flags=re.IGNORECASE)
        
        # Capitalize "I" when used as pronoun
        enhanced_text = re.sub(r'\bi\b', 'I', enhanced_text)
        
        return enhanced_text
    
    def fix_common_contractions(self, text: str) -> str:
        """
        Fix common contraction errors.
        
        Args:
            text: Input text
            
        Returns:
            Text with contraction errors fixed
        """
        # Common contraction fixes
        contraction_fixes = [
            (r'\b(cant)\b', "can't"),
            (r'\b(dont)\b', "don't"),
            (r'\b(wont)\b', "won't"),
            (r'\b(havent)\b', "haven't"),
            (r'\b(hasnt)\b', "hasn't"),
            (r'\b(hadnt)\b', "hadn't"),
            (r'\b(isnt)\b', "isn't"),
            (r'\b(arent)\b', "aren't"),
            (r'\b(werent)\b', "weren't"),
            (r'\b(shouldnt)\b', "shouldn't"),
            (r'\b(couldnt)\b', "couldn't"),
            (r'\b(wouldnt)\b', "wouldn't"),
            (r'\b(im)\b', "I'm"),
            (r'\b(youre)\b', "you're"),
            (r'\b(hes)\b', "he's"),
            (r'\b(shes)\b', "she's"),
            (r'\b(its)\b', "it's"),
            (r'\b(theyre)\b', "they're"),
            (r'\b(weve)\b', "we've"),
            (r'\b(youve)\b', "you've"),
            (r'\b(theyve)\b', "they've"),
        ]
        
        enhanced_text = text
        for pattern, replacement in contraction_fixes:
            enhanced_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
        
        return enhanced_text
    
    def ai_grammar_correction(self, text: str, context: Optional[str] = None) -> EnhancementResult:
        """
        AI-powered grammar correction.
        
        Args:
            text: Input text
            context: Optional context for processing
            
        Returns:
            EnhancementResult with corrected text
        """
        if not self.ai_processor:
            raise RuntimeError("AI processor not available")
        
        custom_instructions = "Focus specifically on grammar correction. Fix subject-verb agreement, verb tense consistency, and sentence structure errors."
        
        return self.ai_processor.enhance_text(
            text=text,
            context=context,
            custom_instructions=custom_instructions
        )
    
    def ai_punctuation_enhancement(self, text: str, context: Optional[str] = None) -> EnhancementResult:
        """
        AI-powered punctuation enhancement.
        
        Args:
            text: Input text
            context: Optional context for processing
            
        Returns:
            EnhancementResult with enhanced punctuation
        """
        if not self.ai_processor:
            raise RuntimeError("AI processor not available")
        
        custom_instructions = "Focus specifically on punctuation. Add missing commas, semicolons, colons, and other punctuation marks where appropriate. Ensure proper sentence ending punctuation."
        
        return self.ai_processor.enhance_text(
            text=text,
            context=context,
            custom_instructions=custom_instructions
        )
    
    def ai_sentence_structure(self, text: str, context: Optional[str] = None) -> EnhancementResult:
        """
        AI-powered sentence structure improvement.
        
        Args:
            text: Input text
            context: Optional context for processing
            
        Returns:
            EnhancementResult with improved sentence structure
        """
        if not self.ai_processor:
            raise RuntimeError("AI processor not available")
        
        custom_instructions = "Focus on improving sentence structure and flow. Break up run-on sentences, combine short choppy sentences where appropriate, and improve overall readability while maintaining the original meaning."
        
        return self.ai_processor.enhance_text(
            text=text,
            context=context,
            custom_instructions=custom_instructions
        )
    
    def apply_enhancement_chain(self, text: str, enhancement_names: List[str], 
                              context: Optional[str] = None) -> str:
        """
        Apply a chain of enhancement functions to text.
        
        Args:
            text: Input text
            enhancement_names: List of enhancement function names to apply
            context: Optional context for processing
            
        Returns:
            Enhanced text after applying all functions
        """
        enhanced_text = text
        
        for name in enhancement_names:
            if name not in self.functions:
                raise ValueError(f"Unknown enhancement function: {name}")
            
            func = self.functions[name]
            
            if func.requires_ai and not self.ai_processor:
                raise RuntimeError(f"AI processor required for {name} but not available")
            
            if func.requires_ai:
                # AI functions return EnhancementResult
                result = func.function(enhanced_text, context)
                enhanced_text = result.enhanced_text
            else:
                # Rule-based functions return string
                enhanced_text = func.function(enhanced_text)
        
        return enhanced_text
    
    def get_available_functions(self) -> List[str]:
        """Get list of available enhancement function names."""
        return list(self.functions.keys())
    
    def get_function_info(self, name: str) -> Optional[EnhancementFunction]:
        """Get information about a specific enhancement function."""
        return self.functions.get(name) 
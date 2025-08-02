"""
Context-Aware Text Processing

This module provides context-aware text enhancement that adapts processing
strategies based on the application context (email, document, code, etc.).
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from enum import Enum

from .text_enhancement import AITextProcessor, EnhancementResult
from .enhancement_functions import EnhancementFunctions


class ContextType(Enum):
    """Supported application contexts."""
    EMAIL = "email"
    DOCUMENT = "document"
    CODE = "code"
    CHAT = "chat"
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CREATIVE = "creative"


@dataclass
class ContextConfig:
    """Configuration for a specific context."""
    context_type: ContextType
    description: str
    enhancement_chain: List[str]
    custom_instructions: Optional[str] = None
    tone_adjustment: Optional[str] = None
    formatting_rules: Optional[Dict[str, Any]] = None


class ContextProcessor:
    """
    Context-aware text processor that adapts enhancement strategies
    based on the application context.
    """
    
    def __init__(self, ai_processor: AITextProcessor):
        """
        Initialize the context processor.
        
        Args:
            ai_processor: AITextProcessor instance for AI-powered enhancements
        """
        self.ai_processor = ai_processor
        self.enhancement_functions = EnhancementFunctions(ai_processor)
        self.context_configs: Dict[ContextType, ContextConfig] = {}
        self._initialize_context_configs()
    
    def _initialize_context_configs(self):
        """Initialize default context configurations."""
        self.context_configs = {
            ContextType.EMAIL: ContextConfig(
                context_type=ContextType.EMAIL,
                description="Professional email communication",
                enhancement_chain=[
                    "remove_filler_words",
                    "fix_basic_punctuation",
                    "capitalize_proper_nouns",
                    "fix_common_contractions"
                ],
                custom_instructions="Maintain a professional tone suitable for email communication. Ensure proper greeting and closing structure if present.",
                tone_adjustment="professional"
            ),
            
            ContextType.DOCUMENT: ContextConfig(
                context_type=ContextType.DOCUMENT,
                description="Formal document writing",
                enhancement_chain=[
                    "remove_filler_words",
                    "fix_basic_punctuation",
                    "capitalize_proper_nouns",
                    "fix_common_contractions",
                    "ai_grammar_correction"
                ],
                custom_instructions="Ensure formal document structure with proper paragraph breaks and professional language.",
                tone_adjustment="formal"
            ),
            
            ContextType.CODE: ContextConfig(
                context_type=ContextType.CODE,
                description="Code comments and documentation",
                enhancement_chain=[
                    "remove_filler_words",
                    "fix_basic_punctuation",
                    "capitalize_proper_nouns"
                ],
                custom_instructions="Keep code comments concise and technical. Preserve code-related terminology and formatting.",
                tone_adjustment="technical"
            ),
            
            ContextType.CHAT: ContextConfig(
                context_type=ContextType.CHAT,
                description="Casual chat and messaging",
                enhancement_chain=[
                    "remove_filler_words",
                    "fix_basic_punctuation",
                    "fix_common_contractions"
                ],
                custom_instructions="Maintain conversational tone while improving clarity. Preserve casual language and emojis if present.",
                tone_adjustment="casual"
            ),
            
            ContextType.FORMAL: ContextConfig(
                context_type=ContextType.FORMAL,
                description="Formal writing and presentations",
                enhancement_chain=[
                    "remove_filler_words",
                    "fix_basic_punctuation",
                    "capitalize_proper_nouns",
                    "fix_common_contractions",
                    "ai_grammar_correction",
                    "ai_sentence_structure"
                ],
                custom_instructions="Ensure formal academic or business writing standards. Use sophisticated vocabulary and complex sentence structures where appropriate.",
                tone_adjustment="formal"
            ),
            
            ContextType.CASUAL: ContextConfig(
                context_type=ContextType.CASUAL,
                description="Casual and informal writing",
                enhancement_chain=[
                    "remove_filler_words",
                    "fix_basic_punctuation",
                    "fix_common_contractions"
                ],
                custom_instructions="Maintain casual, friendly tone while improving readability. Preserve informal language and expressions.",
                tone_adjustment="casual"
            ),
            
            ContextType.TECHNICAL: ContextConfig(
                context_type=ContextType.TECHNICAL,
                description="Technical documentation and writing",
                enhancement_chain=[
                    "remove_filler_words",
                    "fix_basic_punctuation",
                    "capitalize_proper_nouns",
                    "ai_grammar_correction"
                ],
                custom_instructions="Maintain technical accuracy while improving clarity. Preserve technical terminology and ensure precise language.",
                tone_adjustment="technical"
            ),
            
            ContextType.CREATIVE: ContextConfig(
                context_type=ContextType.CREATIVE,
                description="Creative writing and storytelling",
                enhancement_chain=[
                    "fix_basic_punctuation",
                    "capitalize_proper_nouns",
                    "fix_common_contractions"
                ],
                custom_instructions="Preserve creative expression and artistic language while improving basic grammar and punctuation. Maintain the author's voice and style.",
                tone_adjustment="creative"
            )
        }
    
    def process_with_context(self, text: str, context: ContextType, 
                           custom_instructions: Optional[str] = None) -> EnhancementResult:
        """
        Process text with context-aware enhancement.
        
        Args:
            text: Input text to enhance
            context: Application context type
            custom_instructions: Optional additional instructions
            
        Returns:
            EnhancementResult with context-appropriate enhancements
        """
        if context not in self.context_configs:
            raise ValueError(f"Unknown context type: {context}")
        
        config = self.context_configs[context]
        
        # Apply rule-based enhancements first
        enhanced_text = self.enhancement_functions.apply_enhancement_chain(
            text=text,
            enhancement_names=config.enhancement_chain,
            context=context.value
        )
        
        # Combine custom instructions
        final_instructions = config.custom_instructions
        if custom_instructions:
            if final_instructions:
                final_instructions += f" {custom_instructions}"
            else:
                final_instructions = custom_instructions
        
        # Apply AI enhancement with context-specific instructions
        result = self.ai_processor.enhance_text(
            text=enhanced_text,
            context=context.value,
            custom_instructions=final_instructions
        )
        
        return result
    
    def add_context_config(self, context_type: ContextType, config: ContextConfig):
        """
        Add or update a context configuration.
        
        Args:
            context_type: The context type
            config: Configuration for the context
        """
        self.context_configs[context_type] = config
    
    def get_context_config(self, context_type: ContextType) -> Optional[ContextConfig]:
        """
        Get configuration for a specific context.
        
        Args:
            context_type: The context type
            
        Returns:
            ContextConfig if available, None otherwise
        """
        return self.context_configs.get(context_type)
    
    def get_available_contexts(self) -> List[ContextType]:
        """Get list of available context types."""
        return list(self.context_configs.keys())
    
    def get_context_description(self, context_type: ContextType) -> Optional[str]:
        """
        Get description for a context type.
        
        Args:
            context_type: The context type
            
        Returns:
            Description string if available, None otherwise
        """
        config = self.get_context_config(context_type)
        return config.description if config else None
    
    def create_custom_context(self, name: str, enhancement_chain: List[str],
                            custom_instructions: Optional[str] = None,
                            description: Optional[str] = None) -> ContextType:
        """
        Create a custom context type.
        
        Args:
            name: Name for the custom context
            enhancement_chain: List of enhancement function names to apply
            custom_instructions: Optional custom instructions
            description: Optional description
            
        Returns:
            New ContextType enum value
        """
        # Create a new enum value dynamically
        context_type = ContextType(name.lower())
        
        config = ContextConfig(
            context_type=context_type,
            description=description or f"Custom context: {name}",
            enhancement_chain=enhancement_chain,
            custom_instructions=custom_instructions
        )
        
        self.add_context_config(context_type, config)
        return context_type
    
    def get_enhancement_chain_for_context(self, context_type: ContextType) -> List[str]:
        """
        Get the enhancement chain for a specific context.
        
        Args:
            context_type: The context type
            
        Returns:
            List of enhancement function names
        """
        config = self.get_context_config(context_type)
        return config.enhancement_chain if config else []
    
    def validate_enhancement_chain(self, enhancement_chain: List[str]) -> bool:
        """
        Validate that all enhancement functions in a chain are available.
        
        Args:
            enhancement_chain: List of enhancement function names
            
        Returns:
            True if all functions are available, False otherwise
        """
        available_functions = self.enhancement_functions.get_available_functions()
        return all(func in available_functions for func in enhancement_chain) 
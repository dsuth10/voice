"""
AI Text Enhancement Engine

This module provides the AITextProcessor class for enhancing transcribed text
using OpenAI GPT models with grammar correction, punctuation, and filler word removal.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

import openai
from openai import OpenAI

from ..utils.logger import get_logger
from .prompt_templates import PromptTemplateManager
from .cache_manager import CacheManager

logger = get_logger(__name__)


@dataclass
class EnhancementResult:
    """Result of text enhancement processing."""
    original_text: str
    enhanced_text: str
    model_used: str
    tokens_used: int
    processing_time: float
    context: Optional[str] = None
    custom_instructions: Optional[str] = None


class AITextProcessor:
    """
    AI-powered text enhancement processor using OpenAI GPT models.
    
    Provides grammar correction, punctuation insertion, filler word removal,
    and context-aware text improvement.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize the AI text processor.
        
        Args:
            api_key: OpenAI API key
            model: Primary model to use (default: gpt-4o-mini)
        """
        self.client = OpenAI(api_key=api_key)
        self.primary_model = model
        self.fallback_model = "gpt-3.5-turbo"
        # Initialize cache manager
        self.cache_manager = CacheManager()
        
        # Initialize prompt template manager
        self.template_manager = PromptTemplateManager()
        
        # Base prompt for text enhancement
        self.base_prompt = """You are an expert text enhancement assistant. Your task is to improve transcribed text by:

1. Correcting grammar and spelling errors
2. Adding appropriate punctuation where missing
3. Removing filler words (um, ah, like, you know, etc.)
4. Improving sentence structure and clarity
5. Capitalizing proper nouns correctly
6. Maintaining the original meaning and tone

Return only the enhanced text without explanations or markdown formatting."""

        logger.info(f"AITextProcessor initialized with model: {self.primary_model}")
    
    def _generate_cache_key(self, text: str, context: Optional[str] = None, 
                           custom_instructions: Optional[str] = None, 
                           template_name: Optional[str] = None) -> str:
        """Generate a cache key for the given input parameters."""
        return self.cache_manager.generate_cache_key(text, context, custom_instructions, template_name)
    
    def _build_prompt(self, text: str, context: Optional[str] = None,
                     custom_instructions: Optional[str] = None, 
                     template_name: Optional[str] = None) -> str:
        """Build the complete prompt for text enhancement."""
        if template_name:
            # Use custom template
            try:
                prompt = self.template_manager.render_template(
                    template_name,
                    context=context or "general",
                    custom_instructions=custom_instructions or ""
                )
                return prompt
            except Exception as e:
                logger.warning(f"Failed to render template '{template_name}': {e}, falling back to base prompt")
        
        # Use base prompt
        prompt = self.base_prompt
        
        if context:
            prompt += f"\n\nContext: This text will be used in a {context} context."
        
        if custom_instructions:
            prompt += f"\n\nAdditional instructions: {custom_instructions}"
        
        return prompt
    
    def _call_openai_api(self, prompt: str, text: str, model: str) -> tuple[str, int]:
        """
        Make API call to OpenAI with error handling and fallback.
        
        Returns:
            Tuple of (enhanced_text, tokens_used)
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=1024
            )
            
            enhanced_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            logger.info(f"API call successful using model {model}, tokens used: {tokens_used}")
            return enhanced_text, tokens_used
            
        except openai.RateLimitError:
            logger.warning(f"Rate limit hit for model {model}, trying fallback")
            raise
        except openai.APIError as e:
            logger.error(f"API error with model {model}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error with model {model}: {e}")
            raise
    
    def enhance_text(self, text: str, context: Optional[str] = None,
                    custom_instructions: Optional[str] = None,
                    use_cache: bool = True, template_name: Optional[str] = None) -> EnhancementResult:
        """
        Enhance text using AI processing.
        
        Args:
            text: The text to enhance
            context: Optional context (e.g., 'email', 'document', 'code')
            custom_instructions: Optional custom enhancement instructions
            use_cache: Whether to use caching (default: True)
            template_name: Optional template name to use for prompt generation
            
        Returns:
            EnhancementResult with enhanced text and metadata
        """
        import time
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            cache_key = self._generate_cache_key(text, context, custom_instructions, template_name)
            cached_entry = self.cache_manager.get(cache_key)
            if cached_entry:
                logger.info("Cache hit - returning cached result")
                return EnhancementResult(
                    original_text=cached_entry.original_text,
                    enhanced_text=cached_entry.enhanced_text,
                    model_used=cached_entry.model_used,
                    tokens_used=cached_entry.tokens_used,
                    processing_time=cached_entry.processing_time,
                    context=cached_entry.context,
                    custom_instructions=cached_entry.custom_instructions
                )
        
        # Build prompt
        prompt = self._build_prompt(text, context, custom_instructions, template_name)
        
        # Try primary model first
        model_used = self.primary_model
        try:
            enhanced_text, tokens_used = self._call_openai_api(prompt, text, self.primary_model)
        except (openai.RateLimitError, openai.APIError):
            # Fallback to secondary model
            logger.info(f"Falling back to {self.fallback_model}")
            try:
                enhanced_text, tokens_used = self._call_openai_api(prompt, text, self.fallback_model)
                model_used = self.fallback_model
            except Exception as e:
                logger.error(f"Both models failed: {e}")
                raise RuntimeError(f"Text enhancement failed: {e}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create result
        result = EnhancementResult(
            original_text=text,
            enhanced_text=enhanced_text,
            model_used=model_used,
            tokens_used=tokens_used,
            processing_time=processing_time,
            context=context,
            custom_instructions=custom_instructions
        )
        
        # Cache the result and update token usage
        if use_cache:
            cache_key = self._generate_cache_key(text, context, custom_instructions, template_name)
            from .cache_manager import CacheEntry
            cache_entry = CacheEntry(
                key=cache_key,
                original_text=result.original_text,
                enhanced_text=result.enhanced_text,
                model_used=result.model_used,
                tokens_used=result.tokens_used,
                processing_time=result.processing_time,
                context=result.context,
                custom_instructions=result.custom_instructions,
                template_name=template_name
            )
            self.cache_manager.put(cache_entry)
            self.cache_manager.update_token_usage(model_used, tokens_used)
        
        logger.info(f"Text enhancement completed in {processing_time:.2f}s using {model_used}")
        return result
    
    def get_token_usage(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get token usage statistics by model."""
        return self.cache_manager.get_token_usage(model)
    
    def clear_cache(self) -> None:
        """Clear the enhancement cache."""
        self.cache_manager.clear_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache_manager.get_cache_stats()
    
    def get_total_cost(self, model: Optional[str] = None) -> float:
        """Get total estimated cost for token usage."""
        return self.cache_manager.get_total_cost(model) 
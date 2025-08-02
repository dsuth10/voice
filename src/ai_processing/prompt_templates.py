"""
Customizable Prompt Template System

This module provides a template system for AI prompts that users can modify
and extend for different enhancement scenarios.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import re

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PromptTemplate:
    """Represents a customizable prompt template."""
    name: str
    description: str
    template: str
    variables: List[str]
    category: str
    is_default: bool = False
    version: str = "1.0"
    
    def __post_init__(self):
        """Extract variables from template after initialization."""
        if not self.variables:
            self.variables = self._extract_variables()
    
    def _extract_variables(self) -> List[str]:
        """Extract variable names from template using {{variable}} syntax."""
        pattern = r'\{\{(\w+)\}\}'
        return list(set(re.findall(pattern, self.template)))
    
    def render(self, **kwargs) -> str:
        """
        Render the template with provided variables.
        
        Args:
            **kwargs: Variables to substitute in the template
            
        Returns:
            Rendered template string
        """
        rendered = self.template
        
        for var_name, value in kwargs.items():
            placeholder = f"{{{{{var_name}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered
    
    def validate_variables(self, **kwargs) -> bool:
        """
        Validate that all required variables are provided.
        
        Args:
            **kwargs: Variables to validate
            
        Returns:
            True if all required variables are provided, False otherwise
        """
        provided_vars = set(kwargs.keys())
        required_vars = set(self.variables)
        return required_vars.issubset(provided_vars)


class PromptTemplateManager:
    """
    Manager for customizable prompt templates.
    
    Provides template creation, modification, selection, and validation.
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the prompt template manager.
        
        Args:
            templates_dir: Directory to store custom templates (optional)
        """
        self.templates_dir = templates_dir or ".templates"
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
        self._load_custom_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates."""
        default_templates = [
            PromptTemplate(
                name="basic_enhancement",
                description="Basic text enhancement with grammar and punctuation",
                template="""You are an expert text enhancement assistant. Your task is to improve transcribed text by:

1. Correcting grammar and spelling errors
2. Adding appropriate punctuation where missing
3. Removing filler words (um, ah, like, you know, etc.)
4. Improving sentence structure and clarity
5. Capitalizing proper nouns correctly
6. Maintaining the original meaning and tone

Context: {{context}}
Additional instructions: {{custom_instructions}}

Return only the enhanced text without explanations or markdown formatting.""",
                variables=["context", "custom_instructions"],
                category="general",
                is_default=True
            ),
            
            PromptTemplate(
                name="formal_writing",
                description="Formal writing enhancement for business and academic contexts",
                template="""You are an expert in formal writing enhancement. Improve the following text for formal business or academic contexts by:

1. Ensuring professional tone and vocabulary
2. Correcting grammar and punctuation
3. Improving sentence structure and flow
4. Removing informal language and filler words
5. Maintaining clarity and precision
6. Following formal writing conventions

Context: {{context}}
Tone: Formal and professional
Additional instructions: {{custom_instructions}}

Return only the enhanced text without explanations.""",
                variables=["context", "custom_instructions"],
                category="formal",
                is_default=True
            ),
            
            PromptTemplate(
                name="technical_documentation",
                description="Technical documentation enhancement",
                template="""You are an expert in technical documentation. Enhance the following text for technical contexts by:

1. Maintaining technical accuracy and precision
2. Using appropriate technical terminology
3. Ensuring clear and concise explanations
4. Correcting grammar and punctuation
5. Improving readability for technical audiences
6. Preserving code-related terminology and formatting

Context: {{context}}
Technical level: {{technical_level}}
Additional instructions: {{custom_instructions}}

Return only the enhanced text without explanations.""",
                variables=["context", "technical_level", "custom_instructions"],
                category="technical",
                is_default=True
            ),
            
            PromptTemplate(
                name="creative_writing",
                description="Creative writing enhancement that preserves artistic expression",
                template="""You are an expert in creative writing enhancement. Improve the following text while preserving creative expression by:

1. Maintaining the author's voice and style
2. Preserving artistic language and metaphors
3. Improving basic grammar and punctuation
4. Enhancing flow and rhythm
5. Keeping creative elements intact
6. Avoiding over-formalization

Context: {{context}}
Style: {{writing_style}}
Additional instructions: {{custom_instructions}}

Return only the enhanced text without explanations.""",
                variables=["context", "writing_style", "custom_instructions"],
                category="creative",
                is_default=True
            ),
            
            PromptTemplate(
                name="casual_conversation",
                description="Casual conversation enhancement for chat and messaging",
                template="""You are an expert in casual conversation enhancement. Improve the following text for casual contexts by:

1. Maintaining conversational tone
2. Preserving casual language and expressions
3. Removing excessive filler words
4. Improving basic grammar and punctuation
5. Keeping the friendly, approachable style
6. Preserving emojis and informal elements

Context: {{context}}
Tone: Casual and friendly
Additional instructions: {{custom_instructions}}

Return only the enhanced text without explanations.""",
                variables=["context", "custom_instructions"],
                category="casual",
                is_default=True
            )
        ]
        
        for template in default_templates:
            self.templates[template.name] = template
    
    def _load_custom_templates(self):
        """Load custom templates from the templates directory."""
        if not os.path.exists(self.templates_dir):
            return
        
        templates_path = Path(self.templates_dir)
        for template_file in templates_path.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    template = PromptTemplate(**template_data)
                    self.templates[template.name] = template
                    logger.info(f"Loaded custom template: {template.name}")
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")
    
    def create_template(self, name: str, description: str, template: str,
                       category: str = "custom", **kwargs) -> PromptTemplate:
        """
        Create a new prompt template.
        
        Args:
            name: Template name
            description: Template description
            template: Template string with {{variable}} placeholders
            category: Template category
            **kwargs: Additional template properties
            
        Returns:
            Created PromptTemplate instance
        """
        if name in self.templates:
            raise ValueError(f"Template '{name}' already exists")
        
        prompt_template = PromptTemplate(
            name=name,
            description=description,
            template=template,
            variables=[],  # Will be auto-extracted
            category=category,
            **kwargs
        )
        
        self.templates[name] = prompt_template
        self._save_custom_template(prompt_template)
        
        logger.info(f"Created custom template: {name}")
        return prompt_template
    
    def _save_custom_template(self, template: PromptTemplate):
        """Save a custom template to file."""
        if template.is_default:
            return  # Don't save default templates
        
        os.makedirs(self.templates_dir, exist_ok=True)
        template_file = Path(self.templates_dir) / f"{template.name}.json"
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(template), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save template {template.name}: {e}")
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            PromptTemplate if found, None otherwise
        """
        return self.templates.get(name)
    
    def list_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """
        List available templates, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of PromptTemplate instances
        """
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def update_template(self, name: str, **kwargs) -> PromptTemplate:
        """
        Update an existing template.
        
        Args:
            name: Template name
            **kwargs: Properties to update
            
        Returns:
            Updated PromptTemplate instance
        """
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        
        template = self.templates[name]
        
        # Update template properties
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        # Re-extract variables if template changed
        if 'template' in kwargs:
            template.variables = template._extract_variables()
        
        self._save_custom_template(template)
        logger.info(f"Updated template: {name}")
        
        return template
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a custom template.
        
        Args:
            name: Template name
            
        Returns:
            True if deleted, False if not found or is default
        """
        if name not in self.templates:
            return False
        
        template = self.templates[name]
        if template.is_default:
            logger.warning(f"Cannot delete default template: {name}")
            return False
        
        # Remove from memory
        del self.templates[name]
        
        # Remove from file system
        template_file = Path(self.templates_dir) / f"{name}.json"
        if template_file.exists():
            template_file.unlink()
        
        logger.info(f"Deleted template: {name}")
        return True
    
    def render_template(self, name: str, **kwargs) -> str:
        """
        Render a template with provided variables.
        
        Args:
            name: Template name
            **kwargs: Variables to substitute
            
        Returns:
            Rendered template string
        """
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")
        
        if not template.validate_variables(**kwargs):
            missing_vars = set(template.variables) - set(kwargs.keys())
            raise ValueError(f"Missing required variables: {missing_vars}")
        
        return template.render(**kwargs)
    
    def get_categories(self) -> List[str]:
        """Get list of available template categories."""
        categories = set(template.category for template in self.templates.values())
        return sorted(list(categories))
    
    def validate_template(self, template_string: str) -> bool:
        """
        Validate a template string for proper syntax.
        
        Args:
            template_string: Template string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check for balanced braces
            brace_count = template_string.count('{{') - template_string.count('}}')
            if brace_count != 0:
                return False
            
            # Check for valid variable names
            pattern = r'\{\{(\w+)\}\}'
            variables = re.findall(pattern, template_string)
            
            for var in variables:
                if not var.isidentifier():
                    return False
            
            return True
        except Exception:
            return False 
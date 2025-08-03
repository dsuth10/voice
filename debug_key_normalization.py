#!/usr/bin/env python3
"""
Debug Key Normalization
"""

def normalize_key_combination(key_combination: str) -> str:
    """Debug key normalization"""
    # Convert to lowercase and remove extra spaces
    normalized = key_combination.lower().strip()
    
    print(f"Original: '{key_combination}'")
    print(f"After lowercase: '{normalized}'")
    
    # Replace common variations with global-hotkeys compatible names
    replacements = {
        'ctrl': 'control',
        'control': 'control',
        'alt': 'alt',
        'shift': 'shift',
        'win': 'window',
        'windows': 'window',
        'space': 'space',
        'spacebar': 'space'
    }
    
    # Apply replacements
    for old, new in replacements.items():
        if old in normalized:
            print(f"Replacing '{old}' with '{new}'")
            normalized = normalized.replace(old, new)
            print(f"After replacement: '{normalized}'")
    
    return normalized

# Test the normalization
test_keys = ['win+alt', 'window+alt', 'ctrl+win+space']
for key in test_keys:
    result = normalize_key_combination(key)
    print(f"Final result for '{key}': '{result}'")
    print("-" * 40) 
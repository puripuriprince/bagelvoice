#!/usr/bin/env python3
"""
Quick fix script for the Gemini embedding model name issue.
"""
import os
import re
import shutil

def fix_embedding_model_issue():
    """Fix the embedding model name in vector_store.py"""
    file_path = os.path.join("models", "vector_store.py")

    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        return False

    # Create a backup
    backup_path = file_path + ".model.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    # Fix the model name in the __init__ method
    init_pattern = r'self\.embedding_model = embedding_model or "models/text-embedding-gecko"'
    init_replacement = 'self.embedding_model = embedding_model or "embedding-001"'
    content = content.replace(init_pattern, init_replacement)

    # Fix the embed_content function to ignore the passed model parameter
    embed_pattern = r"def embed_content\(model, content, task_type\):.*?result = genai\.embed_content\("
    embed_replacement = """def embed_content(model, content, task_type):
                result = genai.embed_content(
                    model="embedding-001",  # Use the correct model name"""

    content = re.sub(embed_pattern, embed_replacement, content, flags=re.DOTALL)

    with open(file_path, 'w') as f:
        f.write(content)

    print(f"Updated embedding model name in {file_path}")
    return True

if __name__ == "__main__":
    print("Fixing Gemini embedding model name issue...")
    if fix_embedding_model_issue():
        print("Fix complete! Please restart your Flask application.")
    else:
        print("Fix failed. Please update the model name manually.")

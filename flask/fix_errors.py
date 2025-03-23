#!/usr/bin/env python3
"""
Script to fix common errors in the notebook application.
Run this script to install missing dependencies and update configuration.
"""

import os
import sys
import subprocess
import re

def install_missing_packages():
    """Install packages that are reported as missing"""
    print("Installing missing packages...")
    packages = ["PyPDF2", "google-generativeai"]

    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    print("Package installation complete!")

def fix_embedding_model_name():
    """Fix the embedding model name in vector_store.py"""
    vector_store_path = os.path.join("models", "vector_store.py")

    if not os.path.exists(vector_store_path):
        print(f"Error: Could not find {vector_store_path}")
        return False

    with open(vector_store_path, 'r') as f:
        content = f.read()

    # Look for embedding model definitions
    if "embedding-001" in content:
        updated_content = content.replace(
            "embedding-001",
            "models/text-embedding-gecko"
        )

        # Also check for other potential embedding model declaration patterns
        updated_content = re.sub(
            r"self\.embedding_model\s*=\s*['\"]([^'\"]*)['\"]",
            r"self.embedding_model = \"models/text-embedding-gecko\"",
            updated_content
        )

        with open(vector_store_path, 'w') as f:
            f.write(updated_content)

        print("Updated embedding model name in vector_store.py")
        return True
    else:
        print("Could not find 'embedding-001' in vector_store.py")
        print("Please manually update the embedding model name to 'models/text-embedding-gecko'")
        return False

if __name__ == "__main__":
    print("=== Flask App Error Fixer ===")

    # Install missing packages
    try:
        install_missing_packages()
    except Exception as e:
        print(f"Error installing packages: {e}")

    # Fix embedding model name
    try:
        if fix_embedding_model_name():
            print("\n✅ Embedding model name fixed successfully!")
        else:
            print("\n⚠️ Couldn't automatically fix embedding model name.")
            print("Please check models/vector_store.py and update the embedding model name manually.")
    except Exception as e:
        print(f"Error fixing embedding model name: {e}")

    print("\n=== Fix Process Complete ===")
    print("Please restart your Flask application to apply these changes.")

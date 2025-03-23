#!/usr/bin/env python3
"""
Quick fix script for vector_store.py embedding client issues.
"""
import os
import re
import sys
import shutil

def fix_vector_store_file():
    """Fix the issues in vector_store.py"""
    # Path to the vector_store.py file
    file_path = os.path.join("models", "vector_store.py")

    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        return False

    # Create a backup
    backup_path = file_path + ".bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")

    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()

    # Fix the __init__ method to initialize embedding_client first
    init_pattern = r"def __init__\(self, db_config=None, embedding_model=None\):.*?self\.setup_database\(\)"
    init_replacement = """def __init__(self, db_config=None, embedding_model=None):
        \"\"\"
        Initialize the VectorStore with database connection and embedding model.

        Args:
            db_config (dict, optional): PostgreSQL connection parameters. If None, will use environment variables.
            embedding_model (str, optional): Name of the embedding model to use
        \"\"\"
        self.embedding_model = embedding_model or "models/text-embedding-gecko"

        # First, initialize the embedding client
        self._init_embedding_client()

        # Set up database connection
        self.db_config = db_config or {
            'host': os.environ.get('POSTGRES_HOST', 'localhost'),
            'port': os.environ.get('POSTGRES_PORT', '5432'),
            'database': os.environ.get('POSTGRES_DB', 'notebook'),
            'user': os.environ.get('POSTGRES_USER', 'postgres'),
            'password': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        }

        # Connect to database
        self.conn = None
        self.setup_database()"""

    content = re.sub(init_pattern, init_replacement, content, flags=re.DOTALL)

    # Fix the _init_embedding_client method
    client_pattern = r"def _init_embedding_client\(self\):.*?raise"
    client_replacement = """def _init_embedding_client(self):
        \"\"\"Initialize the embedding client (Google's Generative AI).\"\"\"
        try:
            import google.generativeai as genai

            # Configure genai with API key
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set")

            genai.configure(api_key=api_key)

            # Define the embedding function
            def embed_content(model, content, task_type):
                result = genai.embed_content(
                    model=model,
                    content=content,
                    task_type=task_type
                )
                return result

            # Store the embedding function
            self.embedding_client = embed_content

            print(f"Google embedding client initialized successfully")

        except ImportError:
            print("Error: google-generativeai package not installed")
            print("Please install it with: pip install google-generativeai")
            raise
        except Exception as e:
            print(f"Error initializing embedding client: {e}")
            traceback.print_exc()
            raise"""

    content = re.sub(client_pattern, client_replacement, content, flags=re.DOTALL)

    # Fix the _create_tables method to handle embedding dimension failures
    tables_pattern = r"def _create_tables\(self, cursor\):.*?raise"
    tables_replacement = """def _create_tables(self, cursor):
        \"\"\"Create necessary tables for storing documents and embeddings.\"\"\"
        try:
            # Create documents table
            cursor.execute(\"""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR(255) UNIQUE NOT NULL,
                    session_id VARCHAR(255),
                    title VARCHAR(255),
                    source_path TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            \""")

            # Try to get embedding dimension by generating a test embedding
            embedding_dim = 768  # Default dimension for most embedding models
            try:
                test_text = "This is a test sentence for embedding dimension."
                test_embedding = self.generate_embedding(test_text)
                if test_embedding:
                    embedding_dim = len(test_embedding)
            except Exception as e:
                print(f"Warning: Could not determine embedding dimension: {e}")
                print("Using default dimension of 768")

            print(f"Using embedding dimension: {embedding_dim}")

            # Create chunks table with vector support and correct dimension
            cursor.execute(f\"""
                CREATE TABLE IF NOT EXISTS chunks (
                    id SERIAL PRIMARY KEY,
                    chunk_id VARCHAR(255) UNIQUE NOT NULL,
                    document_id VARCHAR(255) REFERENCES documents(document_id),
                    content TEXT NOT NULL,
                    embedding vector({embedding_dim}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            \""")

            # Create index on document_id for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)")

            # Create vector index for cosine similarity search
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_chunks_embedding_cosine ON chunks USING ivfflat (embedding vector_cosine_ops)")

            print("Tables created successfully")

        except Exception as e:
            print(f"Error creating tables: {e}")
            traceback.print_exc()
            raise"""

    content = re.sub(tables_pattern, tables_replacement, content, flags=re.DOTALL)

    # Write the updated file
    with open(file_path, 'w') as f:
        f.write(content)

    print(f"Successfully updated {file_path}")
    return True

if __name__ == "__main__":
    print("Fixing vector_store.py embedding client issues...")
    if fix_vector_store_file():
        print("Fix complete! Please restart your Flask application.")
    else:
        print("Fix failed. Please manually update your vector_store.py file.")

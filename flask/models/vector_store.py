import os
import sys
import json
import traceback
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VectorStore:
    """
    VectorStore class for storing and retrieving document embeddings using PostgreSQL with pgvector.
    Uses Google's embedding model for generating embeddings.
    """
    def __init__(self, db_config=None, embedding_model=None):
        """
        Initialize the VectorStore with database connection and embedding model.

        Args:
            db_config (dict, optional): PostgreSQL connection parameters. If None, will use environment variables.
            embedding_model (str, optional): Name of the embedding model to use
        """
        self.embedding_model = embedding_model or "models/embedding-001"

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
        self.setup_database()

    def _init_embedding_client(self):
        """Initialize the embedding client (Google's Generative AI)."""
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
                    model="models/embedding-001",  # Use the correct model name
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
            raise

    def setup_database(self):
        """Set up PostgreSQL connection and initialize pgvector if needed."""
        try:
            import psycopg2
            from psycopg2 import sql
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

            # Connect to PostgreSQL
            print(f"Connecting to PostgreSQL at {self.db_config['host']}:{self.db_config['port']}...")

            # First try connecting to the specified database
            try:
                self.conn = psycopg2.connect(**self.db_config)
                self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            except psycopg2.OperationalError:
                # If the database doesn't exist, connect to 'postgres' and create it
                temp_config = self.db_config.copy()
                temp_config['database'] = 'postgres'

                temp_conn = psycopg2.connect(**temp_config)
                temp_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                temp_cursor = temp_conn.cursor()

                # Create the database if it doesn't exist
                temp_cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(self.db_config['database'])
                    )
                )

                temp_cursor.close()
                temp_conn.close()

                # Now connect to the newly created database
                self.conn = psycopg2.connect(**self.db_config)
                self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            # Create a cursor
            cursor = self.conn.cursor()

            # Check if pgvector extension is installed
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            if cursor.fetchone() is None:
                print("Installing pgvector extension...")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create necessary tables if they don't exist
            self._create_tables(cursor)

            cursor.close()
            print("Database setup completed successfully")

        except ImportError:
            print("Error: psycopg2 package not installed")
            print("Please install it with: pip install psycopg2-binary")
            raise
        except Exception as e:
            print(f"Error setting up database: {e}")
            traceback.print_exc()
            raise

    def _create_tables(self, cursor):
        """Create necessary tables for storing documents and embeddings."""
        try:
            # Create documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR(255) UNIQUE NOT NULL,
                    session_id VARCHAR(255),
                    title VARCHAR(255),
                    source_path TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

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
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS chunks (
                    id SERIAL PRIMARY KEY,
                    chunk_id VARCHAR(255) UNIQUE NOT NULL,
                    document_id VARCHAR(255) REFERENCES documents(document_id),
                    content TEXT NOT NULL,
                    embedding vector({embedding_dim}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index on document_id for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)")

            # Create vector index for cosine similarity search
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_chunks_embedding_cosine ON chunks USING ivfflat (embedding vector_cosine_ops)")

            print("Tables created successfully")

        except Exception as e:
            print(f"Error creating tables: {e}")
            traceback.print_exc()
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a given text using Google's embedding model.

        Args:
            text (str): The text to embed

        Returns:
            List[float]: The embedding vector
        """
        try:
            # Clean and truncate text if necessary
            if len(text) > 25000:  # Approximate limit
                text = text[:25000]

            # Generate embedding
            embedding_result = self.embedding_client(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )

            # Extract the embedding vector
            embedding = embedding_result["embedding"]

            # Make sure the embedding is a list of floats (not numpy array)
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()

            return embedding

        except Exception as e:
            print(f"Error generating embedding: {e}")
            traceback.print_exc()
            return None

    def add_document(self,
                    document_id: str,
                    title: str,
                    content: str,
                    source_path: str = None,
                    session_id: str = None,
                    metadata: Dict = None,
                    chunk_size: int = 1000,
                    chunk_overlap: int = 200) -> bool:
        """
        Add a document to the vector store by chunking it and storing embeddings.

        Args:
            document_id (str): Unique identifier for the document
            title (str): Document title
            content (str): Full text content of the document
            source_path (str, optional): Path to the source file
            session_id (str, optional): Session ID for user association
            metadata (dict, optional): Additional metadata
            chunk_size (int): Size of each chunk in characters
            chunk_overlap (int): Overlap between chunks in characters

        Returns:
            bool: Success status
        """
        try:
            # If no cursor, create one
            if not hasattr(self, 'conn') or self.conn is None:
                self.setup_database()

            cursor = self.conn.cursor()

            # Insert document record
            cursor.execute("""
                INSERT INTO documents
                (document_id, title, source_path, session_id, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (document_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    source_path = EXCLUDED.source_path,
                    session_id = EXCLUDED.session_id,
                    metadata = EXCLUDED.metadata
                RETURNING id
            """, (
                document_id,
                title,
                source_path,
                session_id,
                json.dumps(metadata) if metadata else None
            ))

            # Get chunks from the content
            chunks = self._chunk_text(content, chunk_size, chunk_overlap)
            print(f"Document chunked into {len(chunks)} parts")

            # Process each chunk
            for i, chunk in enumerate(chunks):
                # Create a unique ID for the chunk
                chunk_id = f"{document_id}_chunk_{i}"

                # Generate embedding for the chunk
                embedding = self.generate_embedding(chunk)

                if embedding:
                    # Create chunk metadata
                    chunk_metadata = {
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "document_title": title
                    }

                    # Add any additional metadata
                    if metadata:
                        chunk_metadata.update(metadata)

                    # Insert chunk with embedding - use ARRAY constructor for PostgreSQL
                    cursor.execute("""
                        INSERT INTO chunks
                        (chunk_id, document_id, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s::vector, %s)
                        ON CONFLICT (chunk_id)
                        DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                    """, (
                        chunk_id,
                        document_id,
                        chunk,
                        embedding,  # This will be explicitly cast to vector type
                        json.dumps(chunk_metadata)
                    ))
                else:
                    print(f"Warning: Failed to generate embedding for chunk {i} of document {document_id}")

            self.conn.commit()
            cursor.close()

            print(f"Document {document_id} added to vector store with {len(chunks)} chunks")
            return True

        except Exception as e:
            print(f"Error adding document: {e}")
            traceback.print_exc()
            return False

    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text (str): Text to split
            chunk_size (int): Size of each chunk
            chunk_overlap (int): Overlap between chunks

        Returns:
            List[str]: List of text chunks
        """
        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            # Extract chunk
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]

            # Add to chunks
            chunks.append(chunk)

            # Move start position, accounting for overlap
            start = end - chunk_overlap

            # If we're at the end of the text, break
            if start + chunk_size >= len(text):
                # Add the final chunk only if we haven't reached the end yet
                if end < len(text):
                    chunks.append(text[start:])
                break

        return chunks

    def search_similar(self,
                     query: str,
                     limit: int = 5,
                     session_id: str = None,
                     document_id: str = None) -> List[Dict]:
        """
        Search for chunks similar to the query.

        Args:
            query (str): Query text
            limit (int): Maximum number of results
            session_id (str, optional): Filter by session ID
            document_id (str, optional): Filter by document ID

        Returns:
            List[Dict]: List of chunks with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)

            if not query_embedding:
                print("Error: Failed to generate embedding for query")
                return []

            # Create a cursor
            cursor = self.conn.cursor()

            # Build the query based on filters - use the <#> operator (cosine distance)
            base_query = """
                SELECT
                    c.chunk_id,
                    c.content,
                    c.metadata,
                    d.title,
                    d.document_id,
                    1 - (c.embedding <#> %s::vector) AS similarity
                FROM
                    chunks c
                JOIN
                    documents d ON c.document_id = d.document_id
                WHERE 1=1
            """

            params = [query_embedding]

            # Add filters if provided
            if session_id:
                base_query += " AND d.session_id = %s"
                params.append(session_id)

            if document_id:
                base_query += " AND d.document_id = %s"
                params.append(document_id)

            # Add order and limit
            base_query += " ORDER BY similarity DESC LIMIT %s"  # Note: Changed to DESC as higher similarity is better
            params.append(limit)

            # Execute the query
            cursor.execute(base_query, params)

            # Process results
            results = []
            for row in cursor.fetchall():
                chunk_id, content, metadata_str, title, doc_id, similarity = row

                # Parse metadata if available
                metadata = json.loads(metadata_str) if metadata_str else {}

                results.append({
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "title": title,
                    "content": content,
                    "metadata": metadata,
                    "similarity": similarity
                })

            cursor.close()
            return results

        except Exception as e:
            print(f"Error searching similar documents: {e}")
            traceback.print_exc()
            # Fall back to simple text search when vector search fails
            return self._perform_simple_text_search(query, limit, document_id)

    # Add a fallback search method
    def _perform_simple_text_search(self, query, limit=5, document_id=None):
        """Fallback to simple text search when vector search fails"""
        try:
            cursor = self.conn.cursor()

            # Convert query to lowercase for case-insensitive matching
            query_lower = query.lower()
            query_terms = query_lower.split()

            # Build a simple text search query using ILIKE for PostgreSQL
            base_query = """
                SELECT
                    c.chunk_id,
                    c.content,
                    c.metadata,
                    d.title,
                    d.document_id
                FROM
                    chunks c
                JOIN
                    documents d ON c.document_id = d.document_id
                WHERE 1=1
            """

            params = []

            # Add content search terms
            for term in query_terms:
                base_query += f" AND c.content ILIKE %s"
                params.append(f"%{term}%")

            # Add filters if provided
            if document_id:
                base_query += " AND d.document_id = %s"
                params.append(document_id)

            # Add limit
            base_query += " LIMIT %s"
            params.append(limit)

            # Execute the query
            cursor.execute(base_query, params)

            # Process results
            results = []
            for row in cursor.fetchall():
                chunk_id, content, metadata_str, title, doc_id = row

                # Calculate a simple relevance score
                score = 0
                content_lower = content.lower()
                for term in query_terms:
                    score += content_lower.count(term)

                # Normalize score
                similarity = min(score / (len(query_terms) + 0.1), 1.0)

                # Parse metadata if available
                metadata = json.loads(metadata_str) if metadata_str else {}

                results.append({
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "title": title,
                    "content": content,
                    "metadata": metadata,
                    "similarity": similarity,
                    "search_type": "text"  # Indicate this is from text search
                })

            # Sort by similarity score
            results.sort(key=lambda x: x["similarity"], reverse=True)
            cursor.close()

            print(f"Fallback text search returned {len(results)} results")
            return results

        except Exception as e:
            print(f"Error in fallback text search: {e}")
            traceback.print_exc()
            return []

    def get_document_chunks(self, document_id: str) -> List[Dict]:
        """
        Get all chunks for a specific document.

        Args:
            document_id (str): Unique document identifier

        Returns:
            List[Dict]: List of chunks for the document
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT
                    c.chunk_id,
                    c.content,
                    c.metadata,
                    d.title
                FROM
                    chunks c
                JOIN
                    documents d ON c.document_id = d.document_id
                WHERE
                    c.document_id = %s
                ORDER BY
                    (c.metadata->>'chunk_index')::int
            """, (document_id,))

            results = []
            for row in cursor.fetchall():
                chunk_id, content, metadata_str, title = row

                # Parse metadata if available
                metadata = json.loads(metadata_str) if metadata_str else {}

                results.append({
                    "chunk_id": chunk_id,
                    "content": content,
                    "metadata": metadata,
                    "title": title
                })

            cursor.close()
            return results

        except Exception as e:
            print(f"Error getting document chunks: {e}")
            traceback.print_exc()
            return []

    def get_documents_by_session(self, session_id: str) -> List[Dict]:
        """
        Get all documents for a specific session.

        Args:
            session_id (str): Session identifier

        Returns:
            List[Dict]: List of documents
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                SELECT
                    document_id,
                    title,
                    source_path,
                    metadata,
                    created_at
                FROM
                    documents
                WHERE
                    session_id = %s
                ORDER BY
                    created_at DESC
            """, (session_id,))

            results = []
            for row in cursor.fetchall():
                doc_id, title, source_path, metadata_str, created_at = row

                # Parse metadata if available
                metadata = json.loads(metadata_str) if metadata_str else {}

                results.append({
                    "document_id": doc_id,
                    "title": title,
                    "source_path": source_path,
                    "metadata": metadata,
                    "created_at": created_at.isoformat()
                })

            cursor.close()
            return results

        except Exception as e:
            print(f"Error getting documents by session: {e}")
            traceback.print_exc()
            return []

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks.

        Args:
            document_id (str): Document identifier

        Returns:
            bool: Success status
        """
        try:
            cursor = self.conn.cursor()

            # First delete associated chunks
            cursor.execute("""
                DELETE FROM chunks
                WHERE document_id = %s
            """, (document_id,))

            # Then delete the document
            cursor.execute("""
                DELETE FROM documents
                WHERE document_id = %s
            """, (document_id,))

            self.conn.commit()
            cursor.close()

            return True

        except Exception as e:
            print(f"Error deleting document: {e}")
            traceback.print_exc()
            return False

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# Test the VectorStore functionality if this file is run directly
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    print("\n===== Testing Vector Store with Google Embeddings =====")

    try:
        # Initialize the vector store
        print("Initializing VectorStore...")
        vector_store = VectorStore()
        print("VectorStore initialized!")

        # Test document processing
        test_doc = """
        # Queues and Deques

        A queue is a linear data structure that follows the First In, First Out (FIFO) principle:
        elements are added at the rear (enqueue) and removed from the front (dequeue).

        Common queue operations:
        - Enqueue: Add an element to the end of the queue
        - Dequeue: Remove an element from the front of the queue
        - Peek: View the front element without removing it
        - isEmpty: Check if the queue is empty

        A deque (double-ended queue) allows insertion and deletion at both ends:
        - addFirst/removeFirst: Add/remove at the front
        - addLast/removeLast: Add/remove at the end

        Queues are used in various scenarios including task scheduling, print job management,
        and implementing breadth-first search algorithms in graph traversal.
        """

        # Generate a unique document ID
        document_id = f"test_doc_{int(datetime.now().timestamp())}"

        # Add the document to the vector store
        print("\nAdding test document to vector store...")
        success = vector_store.add_document(
            document_id=document_id,
            title="Queue Data Structure",
            content=test_doc,
            session_id="test_session",
            metadata={"subject": "Data Structures", "level": "Intermediate"}
        )

        if success:
            print(f"Document added successfully with ID: {document_id}")

            # Test similarity search
            print("\nTesting similarity search...")
            test_queries = [
                "What is FIFO?",
                "How do deques work?",
                "What are queues used for?"
            ]

            for query in test_queries:
                print(f"\nSearching for: '{query}'")
                results = vector_store.search_similar(query, limit=2)

                print(f"Found {len(results)} results:")
                for i, result in enumerate(results):
                    print(f"\nResult {i+1} (similarity: {result['similarity']:.4f}):")
                    print(f"Title: {result['title']}")
                    print(f"Content excerpt: {result['content'][:100]}...")

            # Test document chunk retrieval
            print("\nRetrieving all chunks for the document...")
            chunks = vector_store.get_document_chunks(document_id)
            print(f"Retrieved {len(chunks)} chunks")

            # Test document deletion
            print("\nDeleting test document...")
            if vector_store.delete_document(document_id):
                print("Document deleted successfully")
            else:
                print("Failed to delete document")
        else:
            print("Failed to add document to vector store")

        # Clean up
        vector_store.close()
        print("\nVectorStore test completed!")

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nDetailed traceback:")
        traceback.print_exc()

import os
import sys
import json
import traceback
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

from dotenv import load_dotenv
import fitz 
import uuid

from langchain_astradb import AstraDBVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain import hub
from langchain.agents import AgentExecutor
from google.generativeai.types import HarmCategory, HarmBlockThreshold



# Load environment variables
load_dotenv()

def connect_to_vstore():
    embeddings = HuggingFaceEmbeddings()
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")

    vstore = AstraDBVectorStore(
        embedding=embeddings,
        collection_name="Doc",
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        token=ASTRA_DB_APPLICATION_TOKEN,
        namespace="MedDocs",
    )
    return vstore

def add_documents_to_vstore(texts: list):
    try:
        vstore = connect_to_vstore()

        for text in texts:
            id=f"doc_{uuid.uuid4().hex[:10]}",
            document = Document(
                id=id,
                page_content=text, 
            )

<<<<<<< HEAD
            vstore.add_documents([document]) 
        
        return True, id
    
=======
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
                try:
                    if metadata_str is None:
                        metadata = {}
                    elif isinstance(metadata_str, dict):
                        # Already a dictionary, no need to parse
                        metadata = metadata_str
                    else:
                        # Parse JSON string into dictionary
                        metadata = json.loads(metadata_str)
                except Exception as e:
                    print(f"Error parsing metadata: {e}, using empty dict")
                    metadata = {}

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
                try:
                    if metadata_str is None:
                        metadata = {}
                    elif isinstance(metadata_str, dict):
                        # Already a dictionary, no need to parse
                        metadata = metadata_str
                    else:
                        # Parse JSON string into dictionary
                        metadata = json.loads(metadata_str)
                except Exception as e:
                    print(f"Error parsing metadata: {e}, using empty dict")
                    metadata = {}

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
                try:
                    if metadata_str is None:
                        metadata = {}
                    elif isinstance(metadata_str, dict):
                        # Already a dictionary, no need to parse
                        metadata = metadata_str
                    else:
                        # Parse JSON string into dictionary
                        metadata = json.loads(metadata_str)
                except Exception as e:
                    print(f"Error parsing metadata: {e}, using empty dict")
                    metadata = {}

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
                try:
                    if metadata_str is None:
                        metadata = {}
                    elif isinstance(metadata_str, dict):
                        # Already a dictionary, no need to parse
                        metadata = metadata_str
                    else:
                        # Parse JSON string into dictionary
                        metadata = json.loads(metadata_str)
                except Exception as e:
                    print(f"Error parsing metadata: {e}, using empty dict")
                    metadata = {}

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

>>>>>>> origin/main
    except Exception as e:
        print(f"Error: {e}")
        return False, 0

def query_database(query, k=1):
    vstore = connect_to_vstore()
    retriever = vstore.as_retriever(search_kwargs={"k": k})
    
    retrieved_data = retriever.get_relevant_documents(query)
    context = "\n".join([doc.page_content for doc in retrieved_data]) if retrieved_data else "No relevant context available."

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    prompt_template = ( 
        "You are a helpful teaching assistant answering students' questions based on the provided context.\n"
        "Answer the query using the context information.\n"
        "Make sure your answer responds to the user's question.\n\n"
        "Query: {query}\n"
        "Context: {context}"
    )

    result = llm.invoke(prompt_template.format(query=query, context=context))

    return result

def get_documents_by_session(self, session_id: str) -> List[Dict]:
    """
    Get all documents for a specific session.

    Args:
        session_id (str): Session identifier

    Returns:
        List[Dict]: List of documents
    """
    pass

def delete_document(self, document_id: str) -> bool:
    """
    Delete a document and all its chunks.

    Args:
        document_id (str): Document identifier

    Returns:
        bool: Success status
    """
    pass

def close(self):
    """Close the database connection."""
    pass

def summarizer(text):
    """Summarize the text using the Google Generative AI model."""

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    prompt_template = ( 
        "You are a helpful assistant that summarizes text. "
        "Make sure your answer summarizes the query information.\n"
        "Query: {text}\n"
    )

    result = llm.invoke(prompt_template.format(text=text))
    
    return result


if __name__ == "__main__":
    pass
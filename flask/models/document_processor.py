import os
import hashlib
from datetime import datetime
import json
from config import CHUNK_SIZE, CHUNK_OVERLAP, PDF_FOLDER
from utils.pdf_utils import chunk_text #, extract_text_from_pdf,

class DocumentProcessor:
    """
    Processes documents for RAG operations.
    Handles PDF extraction, chunking, and storing processed documents.
    """
    def __init__(self, cohere_client):
        self.cohere_client = cohere_client
        self.document_store = {}  # In-memory store for document data

        # Ensure PDF folder exists
        os.makedirs(PDF_FOLDER, exist_ok=True)

        # Try to load existing document store
        store_path = os.path.join(PDF_FOLDER, 'document_store.json')
        if os.path.exists(store_path):
            try:
                with open(store_path, 'r') as f:
                    self.document_store = json.load(f)
                print(f"Loaded {len(self.document_store)} documents from store")
            except Exception as e:
                print(f"Error loading document store: {e}")

    def save_document_store(self):
        """Save the document store to disk"""
        store_path = os.path.join(PDF_FOLDER, 'document_store.json')
        try:
            with open(store_path, 'w') as f:
                json.dump(self.document_store, f)
            print(f"Saved {len(self.document_store)} documents to store")
        except Exception as e:
            print(f"Error saving document store: {e}")

    def process_pdf(self, file_path, file_name=None, session_id=None):
        """
        Process a PDF file: extract text, chunk it, and store metadata.

        Args:
            file_path (str): Path to the PDF file
            file_name (str, optional): Name to use for the file
            session_id (str, optional): Session ID to associate with this document

        Returns:
            str: Document ID
        """
        # Generate a unique document ID based on content and timestamp
        file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
        doc_id = f"doc_{file_hash[:10]}_{int(datetime.now().timestamp())}"

        # Use provided filename or extract from path
        if not file_name:
            file_name = os.path.basename(file_path)

        try:
            # Extract text from PDF
            text = extract_text_from_pdf(file_path)

            # Chunk the text
            chunks = chunk_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

            # Prepare chunked documents for Cohere format
            chunked_docs = []
            for i, chunk in enumerate(chunks):
                chunked_docs.append({
                    "id": f"{doc_id}_chunk_{i}",
                    "text": chunk,
                    "source": file_name,
                    "page": i // 2  # Rough estimate of page number
                })

            # Store document metadata
            self.document_store[doc_id] = {
                'filename': file_name,
                'path': file_path,
                'upload_time': datetime.now().isoformat(),
                'chunk_count': len(chunks),
                'file_hash': file_hash,
                'session_id': session_id,
                'chunks': chunked_docs
            }

            # Save the updated document store
            self.save_document_store()

            print(f"Processed document {doc_id} with {len(chunks)} chunks")
            return doc_id

        except Exception as e:
            print(f"Error processing PDF {file_path}: {e}")
            raise

    def get_document_chunks(self, doc_ids=None, session_id=None):
        """
        Retrieve chunks for specified documents or session.

        Args:
            doc_ids (list, optional): List of document IDs to retrieve
            session_id (str, optional): Session ID to filter documents

        Returns:
            list: List of document chunks
        """
        chunks = []

        # If specific document IDs are provided, retrieve those
        if doc_ids:
            for doc_id in doc_ids:
                if doc_id in self.document_store:
                    chunks.extend(self.document_store[doc_id].get('chunks', []))

        # If session ID is provided, retrieve all documents for that session
        elif session_id:
            for doc_id, doc_data in self.document_store.items():
                if doc_data.get('session_id') == session_id:
                    chunks.extend(doc_data.get('chunks', []))

        # If neither is provided, return all chunks
        else:
            for doc_data in self.document_store.values():
                chunks.extend(doc_data.get('chunks', []))

        return chunks

    def retrieve_relevant_chunks(self, query, doc_ids=None, session_id=None, top_n=5):
        """
        Retrieve the most relevant document chunks for a query.

        Args:
            query (str): The user query
            doc_ids (list, optional): List of document IDs to search within
            session_id (str, optional): Session ID to filter documents
            top_n (int): Number of chunks to retrieve

        Returns:
            list: List of relevant text chunks in Cohere format
        """
        # Get all document chunks that match the criteria
        all_chunks = self.get_document_chunks(doc_ids, session_id)

        if not all_chunks:
            return []

        # Use Cohere's rerank to find relevant chunks
        reranked_chunks = self.cohere_client.rerank_chunks(query, all_chunks, top_n=top_n)

        # Format for Cohere's RAG
        cohere_docs = []
        for chunk in reranked_chunks:
            cohere_docs.append({
                "id": chunk["id"],
                "data": {
                    "text": chunk["text"],
                    "source": chunk.get("source", "Unknown source"),
                    "score": chunk.get("score", 1.0)
                }
            })

        return cohere_docs

    def get_session_documents(self, session_id):
        """
        Get information about all documents in a session.

        Args:
            session_id (str): The session ID to query

        Returns:
            dict: Dictionary of document metadata for the session
        """
        session_docs = {}
        for doc_id, doc_data in self.document_store.items():
            if doc_data.get('session_id') == session_id:
                # Create a copy without the chunks to reduce size
                doc_info = doc_data.copy()
                if 'chunks' in doc_info:
                    del doc_info['chunks']
                session_docs[doc_id] = doc_info

        return session_docs

    def process_text(self, text_content, title, session_id=None, file_path=None):
        """
        Process raw text: chunk it and store metadata.

        Args:
            text_content (str): The text content to process
            title (str): Title or name for the text
            session_id (str, optional): Session ID to associate with this document
            file_path (str, optional): Path to the saved text file if applicable

        Returns:
            str: Document ID
        """
        # Generate a unique document ID
        content_hash = hashlib.md5(text_content.encode('utf-8')).hexdigest()
        doc_id = f"doc_{content_hash[:10]}_{int(datetime.now().timestamp())}"

        try:
            # Chunk the text
            chunks = chunk_text(text_content, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

            # Prepare chunked documents
            chunked_docs = []
            for i, chunk in enumerate(chunks):
                chunked_docs.append({
                    "id": f"{doc_id}_chunk_{i}",
                    "text": chunk,
                    "source": title,
                    "section": i  # Simple sequential section numbering
                })

            # Store document metadata
            self.document_store[doc_id] = {
                'filename': os.path.basename(file_path) if file_path else f"{title}.txt",
                'path': file_path,
                'title': title,
                'upload_time': datetime.now().isoformat(),
                'chunk_count': len(chunks),
                'content_hash': content_hash,
                'session_id': session_id,
                'chunks': chunked_docs,
                'type': 'text'
            }

            # Save the updated document store
            self.save_document_store()

            print(f"Processed text document {doc_id} with {len(chunks)} chunks")
            return doc_id

        except Exception as e:
            print(f"Error processing text: {e}")
            raise

# Test functionality if this file is run directly
if __name__ == "__main__":
    import os
    import sys
    import tempfile

    print("\n===== Manual Testing for DocumentProcessor =====")

    # Create a simple mock for CoherClient
    class MockCohereClient:
        def rerank_chunks(self, query, chunks, top_n=5):
            # Simulate reranking by returning top_n chunks with mock scores
            return [
                {
                    "text": chunk["text"],
                    "score": 0.9 - (i * 0.1),  # Descending scores for demonstration
                    "id": chunk["id"]
                }
                for i, chunk in enumerate(chunks[:top_n])
            ]

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize processor with mock client
        processor = DocumentProcessor(MockCohereClient())

        # Menu for interactive testing
        while True:
            print("\nChoose a test option:")
            print("1. Process text input")
            print("2. Process PDF file")
            print("3. Retrieve document chunks")
            print("4. Get relevant chunks for a query")
            print("5. List session documents")
            print("q. Quit")

            choice = input("\nEnter your choice: ").strip().lower()

            if choice == 'q':
                break

            elif choice == '1':
                # Test text processing
                print("\n----- Testing Text Processing -----")
                user_text = input("Enter text to process (or press Enter for sample text): ")

                if not user_text:
                    user_text = "This is a sample text document for testing purposes. " * 10

                title = input("Enter a title for the text: ") or "Sample Text"
                session_id = input("Enter a session ID (or press Enter for default): ") or "test_session_123"

                print(f"Processing text ({len(user_text)} characters)...")
                doc_id = processor.process_text(user_text, title, session_id)

                print(f"Text processed successfully!")
                print(f"Document ID: {doc_id}")
                print(f"Chunk count: {processor.document_store[doc_id]['chunk_count']}")
                print(f"First chunk: {processor.document_store[doc_id]['chunks'][0]['text'][:50]}...")

            elif choice == '2':
                # Test PDF processing
                print("\n----- Testing PDF Processing -----")

                pdf_path = input("Enter path to a PDF file (or press Enter for a mock PDF): ")

                if not pdf_path:
                    # Create a mock PDF for testing
                    mock_pdf = os.path.join(temp_dir, "mock_document.pdf")
                    with open(mock_pdf, "wb") as f:
                        f.write(b"%PDF-1.5\nThis is not a real PDF but works for testing")
                    pdf_path = mock_pdf
                    print(f"Created mock PDF at {pdf_path}")

                if not os.path.exists(pdf_path):
                    print(f"Error: File {pdf_path} does not exist")
                    continue

                session_id = input("Enter a session ID (or press Enter for default): ") or "test_session_123"

                print(f"Processing PDF file: {pdf_path}...")
                doc_id = processor.process_pdf(pdf_path, os.path.basename(pdf_path), session_id)

                print(f"PDF processed successfully!")
                print(f"Document ID: {doc_id}")
                print(f"Chunk count: {processor.document_store[doc_id]['chunk_count']}")

            elif choice == '3':
                # Test document chunk retrieval
                print("\n----- Testing Chunk Retrieval -----")

                if not processor.document_store:
                    print("No documents in store. Please process a document first.")
                    continue

                retrieval_type = input("Retrieve by (1) document ID, (2) session ID, or (3) all: ")

                if retrieval_type == '1':
                    # List available document IDs
                    print("\nAvailable document IDs:")
                    for i, doc_id in enumerate(processor.document_store.keys()):
                        print(f"{i+1}. {doc_id}")

                    doc_index = input("Enter the number of the document to retrieve: ")
                    try:
                        selected_doc = list(processor.document_store.keys())[int(doc_index) - 1]
                        chunks = processor.get_document_chunks([selected_doc])
                        print(f"Retrieved {len(chunks)} chunks from document {selected_doc}")
                        print(f"First chunk: {chunks[0]['text'][:50]}...")
                    except (ValueError, IndexError):
                        print("Invalid selection")

                elif retrieval_type == '2':
                    session_id = input("Enter session ID: ") or "test_session_123"
                    chunks = processor.get_document_chunks(session_id=session_id)
                    print(f"Retrieved {len(chunks)} chunks from session {session_id}")
                    if chunks:
                        print(f"First chunk: {chunks[0]['text'][:50]}...")

                elif retrieval_type == '3':
                    chunks = processor.get_document_chunks()
                    print(f"Retrieved {len(chunks)} chunks from all documents")
                    if chunks:
                        print(f"First chunk: {chunks[0]['text'][:50]}...")

                else:
                    print("Invalid choice")

            elif choice == '4':
                # Test relevant chunk retrieval
                print("\n----- Testing Relevant Chunk Retrieval -----")

                if not processor.document_store:
                    print("No documents in store. Please process a document first.")
                    continue

                query = input("Enter a query: ") or "sample text"
                session_id = input("Enter session ID (or press Enter for all documents): ") or None

                print(f"Finding relevant chunks for query: {query}")
                relevant_chunks = processor.retrieve_relevant_chunks(
                    query,
                    session_id=session_id
                )

                print(f"Retrieved {len(relevant_chunks)} relevant chunks")
                for i, chunk in enumerate(relevant_chunks):
                    print(f"{i+1}. ID: {chunk['id']}")
                    print(f"   Text: {chunk['data']['text'][:50]}...")
                    print(f"   Score: {chunk['data'].get('score', 'N/A')}")
                    print()

            elif choice == '5':
                # Test session document listing
                print("\n----- Testing Session Document Listing -----")

                if not processor.document_store:
                    print("No documents in store. Please process a document first.")
                    continue

                session_id = input("Enter session ID: ") or "test_session_123"

                session_docs = processor.get_session_documents(session_id)
                print(f"Found {len(session_docs)} documents in session {session_id}")

                for doc_id, doc_info in session_docs.items():
                    print(f"\nDocument ID: {doc_id}")
                    print(f"Filename: {doc_info.get('filename', 'N/A')}")
                    print(f"Uploaded: {doc_info.get('upload_time', 'N/A')}")
                    print(f"Chunk count: {doc_info.get('chunk_count', 0)}")

            else:
                print("Invalid choice. Please try again.")

        print("\nTesting complete!")

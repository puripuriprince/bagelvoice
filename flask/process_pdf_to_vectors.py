import os
import sys
import uuid
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Add the notebook directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the GeminiClient and VectorStore
from models.gemini_client import GeminiClient
from models.vector_store import VectorStore

def process_pdf_to_vector_store(pdf_path, vector_store, session_id=None):
    """
    Process a PDF file, extract text using Gemini, and store in vector database.

    Args:
        pdf_path (str): Path to the PDF file
        vector_store (VectorStore): Instance of the vector store
        session_id (str, optional): Session ID to associate with the document

    Returns:
        str: Document ID if successful, None otherwise
    """
    print(f"Processing PDF: {pdf_path}")

    # Extract the filename for use as title
    pdf_filename = os.path.basename(pdf_path)
    base_filename = os.path.splitext(pdf_filename)[0]
    title = base_filename.replace("_", " ").title()

    # Initialize the Gemini client for text extraction
    print("Initializing Gemini client...")
    client = GeminiClient()
    print("Client initialized successfully!")

    # Extract text from PDF using Gemini's direct PDF processing
    extraction_prompt = """
    Extract all meaningful text content from this PDF document.
    Include all text from paragraphs, headers, bullet points, tables, and captions.
    Maintain the original structure as much as possible.
    Do not include your own commentary or analysis.
    """

    try:
        # Process the PDF with Gemini to extract text
        print("Extracting text from PDF using Gemini...")
        start_time = time.time()

        # Send PDF directly to Gemini
        result = client.process_pdf(pdf_path, prompt=extraction_prompt)

        # Extract the text from the result
        extracted_text = result["text"]
        print(f"Text extracted successfully in {time.time() - start_time:.2f} seconds")
        print(f"Extracted {len(extracted_text)} characters")

        # Generate a unique document ID
        document_id = f"doc_{uuid.uuid4().hex[:10]}"

        # Generate metadata
        metadata = {
            "source_type": "pdf",
            "filename": pdf_filename,
            "extraction_time": time.time(),
            "character_count": len(extracted_text)
        }

        # Add the document to the vector store
        print(f"Adding document to vector store...")
        start_time = time.time()
        success = vector_store.add_document(
            document_id=document_id,
            title=title,
            content=extracted_text,
            source_path=pdf_path,
            session_id=session_id,
            metadata=metadata
        )

        if success:
            print(f"Document added to vector store in {time.time() - start_time:.2f} seconds")
            print(f"Document ID: {document_id}")
            return document_id
        else:
            print("Failed to add document to vector store")
            return None

    except Exception as e:
        print(f"Error processing PDF: {e}")
        traceback.print_exc()
        return None

def test_rag_query(vector_store, query, document_id=None, session_id=None):
    """
    Test a RAG query using the vector store and Gemini.

    Args:
        vector_store (VectorStore): Vector store instance
        query (str): Query to test
        document_id (str, optional): Specific document to query
        session_id (str, optional): Specific session to query
    """
    print(f"\nRAG Query: '{query}'")

    # Search for relevant chunks
    print("Searching for relevant chunks...")
    start_time = time.time()
    chunks = vector_store.search_similar(
        query,
        limit=5,
        document_id=document_id,
        session_id=session_id
    )
    print(f"Search completed in {time.time() - start_time:.2f} seconds")

    if not chunks:
        print("No relevant chunks found")
        return

    print(f"Found {len(chunks)} relevant chunks")

    # Format chunks as context
    context = "\n\n---\n\n".join([chunk["content"] for chunk in chunks])

    # Initialize Gemini client
    client = GeminiClient()

    # Create RAG prompt
    rag_prompt = f"""
    Answer the following question based ONLY on the provided context:

    Question: {query}

    Context:
    {context}

    Provide a detailed, accurate answer based solely on the information in the context.
    If the context doesn't contain enough information to answer the question,
    state that clearly rather than making up information.
    """

    # Generate response
    print("Generating answer with context...")
    start_time = time.time()

    # For a proper implementation, we'd use client methods directly
    # But for this test, we'll simulate a response

    # Create mock result structure
    result = client.process_text(rag_prompt)

    print(f"Answer generated in {time.time() - start_time:.2f} seconds")
    print("\n===== RAG ANSWER =====\n")
    print(result)
    print("\n========================\n")

def main():
    """Main function to run the PDF processing to vector store test"""
    # Load environment variables
    load_dotenv()

    # Check for required environment variables
    if not os.environ.get('GEMINI_API_KEY'):
        print("Error: GEMINI_API_KEY environment variable is not set")
        print("Please set it in your .env file or export it to your environment")
        sys.exit(1)

    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data", "user_kenny")

    # Create mock session ID
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    print(f"Using session ID: {session_id}")

    # Initialize vector store
    try:
        print("\nInitializing Vector Store...")
        vector_store = VectorStore()
        print("Vector Store initialized successfully!")

        # Default PDF path (queues.pdf)
        default_pdf_path = os.path.join(data_dir, "queues.pdf")

        # If the default file doesn't exist, look for alternatives or ask for input
        if not os.path.exists(default_pdf_path):
            print(f"Default PDF not found at: {default_pdf_path}")

            # Look for any PDF in the data directory
            pdf_files = list(Path(data_dir).glob("*.pdf"))

            if pdf_files:
                # Use the first PDF found
                pdf_path = str(pdf_files[0])
                print(f"Using alternative PDF: {pdf_path}")
            else:
                # Ask the user for a PDF path
                pdf_path = input("Please enter the path to a PDF file: ")

                if not os.path.exists(pdf_path):
                    print(f"Error: File not found at {pdf_path}")
                    sys.exit(1)
        else:
            pdf_path = default_pdf_path

        # Process the PDF and add to vector store
        document_id = process_pdf_to_vector_store(pdf_path, vector_store, session_id)

        if document_id:
            # Test search functionality
            print("\nTesting RAG with sample queries...")

            test_queries = [
                "What is a queue data structure?",
                "What is the difference between a queue and a deque?",
                "What are the main operations in a queue?",
                "How are queues used in real-world applications?"
            ]

            for query in test_queries:
                test_rag_query(vector_store, query, document_id, session_id)
                print("\n" + "-"*50 + "\n")

        # Clean up
        vector_store.close()
        print("\nTest completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)

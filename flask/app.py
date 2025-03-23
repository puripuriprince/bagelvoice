import os
import sys
import io
import json
import uuid
import time
import traceback
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import numpy as np
import re
from urllib.parse import quote

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Import custom modules
try:
    from utils import vid
    HAS_VIDEO_MODULE = True
except ImportError:
    print("Video module not available. Video-related endpoints will be disabled.")
    HAS_VIDEO_MODULE = False

from dotenv import load_dotenv
from pathlib import Path
import traceback
from datetime import datetime

# Load environment variables at the very beginning
load_dotenv()

# Load our modules
from config import (
    DEBUG, SECRET_KEY, UPLOAD_FOLDER, PDF_FOLDER, AUDIO_FOLDER,
    ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
)
from models.cohere_client import CohereClient
from models.document_processor import DocumentProcessor
from models.audio_processor import AudioProcessor
from utils.session_manager import SessionManager
from models.gemini_client import GeminiClient
from models.vector_store import VectorStore

from vs_store import query_database, connect_to_vstore, add_documents_to_vstore, add_pdf_to_vstore

# Create Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Configure static folders for file storage
app.config['PDF_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'pdfs')
app.config['TEXT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'texts')
app.config['TEMP_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'temp')

# Create necessary folders
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEXT_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

print(f"PDF uploads will be stored in: {app.config['PDF_FOLDER']}")
print(f"Text files will be stored in: {app.config['TEXT_FOLDER']}")

# Enable CORS for all routes
CORS(app)

# Initialize clients and managers
cohere_client = CohereClient()
document_processor = DocumentProcessor(cohere_client)
audio_processor = AudioProcessor()
session_manager = SessionManager(session_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions'))

# Check if COHERE_API_KEY is loaded
if not os.environ.get('COHERE_API_KEY'):
    print("Warning: COHERE_API_KEY not found in environment variables")
    # You could set a default or raise an error here

try:
    gemini_client = GeminiClient()
    print("Gemini client initialized successfully")
except Exception as e:
    print(f"Warning: Failed to initialize Gemini client: {e}")
    gemini_client = None

try:
    vector_store = VectorStore()
    print("Vector store initialized successfully")
except Exception as e:
    print(f"Warning: Vector store initialization failed: {e}")
    vector_store = None

def allowed_file(filename, file_type):
    """
    Check if a file has an allowed extension

    Args:
        filename (str): The filename to check
        file_type (str or list): File type(s) to check against, can be a single string or a list of strings

    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    if not filename or '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()

    # Handle both string and list file_type
    if isinstance(file_type, list):
        # If file_type is a list, check against each type in the list
        allowed_extensions = set()
        for ftype in file_type:
            allowed_extensions.update(ALLOWED_EXTENSIONS.get(ftype, set()))
        return extension in allowed_extensions
    else:
        # If file_type is a string, check against that type only
        return extension in ALLOWED_EXTENSIONS.get(file_type, set())

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Notebook RAG API is running"})

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new session"""
    data = request.get_json() or {}

    # Get user info from request data
    user_info = {
        'name': data.get('user_name', 'Anonymous'),
        'email': data.get('user_email', ''),
        'topic': data.get('session_topic', 'General')
    }

    # Create a new session
    session_id = session_manager.create_session(user_info)

    return jsonify({
        "success": True,
        "message": "Session created successfully",
        "session_id": session_id,
        "user_info": user_info
    })

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information"""
    session_data = session_manager.get_session(session_id)

    if not session_data:
        return jsonify({"error": "Session not found"}), 404

    # Get associated documents
    session_documents = document_processor.get_session_documents(session_id)

    # Get conversation history
    conversation = session_manager.get_conversation(session_id)

    return jsonify({
        "session_id": session_id,
        "user_info": session_data.get('user_info', {}),
        "documents": session_documents,
        "conversation": conversation
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file and process it for RAG"""
    # Check if session_id is provided
    session_id = request.form.get('session_id')
    if not session_id or not session_manager.get_session(session_id):
        return jsonify({"error": "Invalid or missing session_id"}), 400

    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Check if it's an allowed format
    if not allowed_file(file.filename, ['pdf', 'txt']):
        return jsonify({"error": "Only PDF and text files are allowed"}), 400

    try:
        # Save the file with a secure filename
        filename = secure_filename(file.filename)

        # Determine file type and save to appropriate folder
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(app.config['PDF_FOLDER'], filename)
            file_type = 'pdf'
        else:
            file_path = os.path.join(app.config['TEXT_FOLDER'], filename)
            file_type = 'text'

        file.save(file_path)

        # Generate a document ID
        document_id = f"doc_{uuid.uuid4().hex[:10]}"

        # Process the document based on its type
        if file_type == 'pdf':
            # Process PDF directly with Gemini for text extraction and vectorization
            if gemini_client and vector_store:
                # Create extraction prompt for text contents
                extraction_prompt = """
                Extract all meaningful text content from this PDF document.
                Include all text from paragraphs, headers, bullet points, tables, and captions.
                Maintain the original structure as much as possible.
                Do not include your own commentary or analysis.
                """

                # Create lecture prompt for lecture creation
                lecture_prompt = """
                Create a comprehensive lecture from this document. Structure it with:

                1. TITLE AND OVERVIEW:
                   - Begin with a clear title based on the document content
                   - Provide a brief overview of what the lecture will cover

                2. INTRODUCTION:
                   - Explain the main topic and its importance
                   - Provide necessary background context
                   - Outline the key learning objectives

                3. MAIN CONTENT:
                   - Organize into 3-5 clearly defined chapters with descriptive titles
                   - Include subsections with key concepts, definitions, and explanations
                   - Preserve any important formulas, theories, or methodologies
                   - Describe any charts, diagrams, or visual elements present in the document

                4. PRACTICAL APPLICATIONS:
                   - Include examples of how the concepts are applied in real-world scenarios
                   - Explain the practical significance of the material

                5. CONCLUSION:
                   - Summarize the key points from each section
                   - Connect the concepts to broader themes or future directions
                   - End with final thoughts on the importance of the material

                Format it as a well-structured lecture that could be presented to university students.
                Use Markdown formatting for better readability (headings with #, lists with -, etc.).
                """

                # First extract text for vectorization
                print(f"Extracting text from PDF: {file_path}")
                extract_result = gemini_client.process_pdf(file_path, prompt=extraction_prompt)
                extracted_text = extract_result["text"]

                # Save the extracted text
                text_filename = f"{os.path.splitext(filename)[0]}_extracted.txt"
                text_path = os.path.join(app.config['TEXT_FOLDER'], text_filename)
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)

                # Generate a lecture summary in parallel
                print(f"Generating lecture from PDF: {file_path}")
                lecture_result = gemini_client.process_pdf(file_path, prompt=lecture_prompt, use_pro_model=True)
                lecture_text = lecture_result["text"]

                # Save the lecture
                lecture_filename = f"{os.path.splitext(filename)[0]}_lecture.md"
                lecture_path = os.path.join(app.config['TEXT_FOLDER'], lecture_filename)
                with open(lecture_path, 'w', encoding='utf-8') as f:
                    f.write(lecture_text)

                # Add to vector store
                vector_success = vector_store.add_document(
                    document_id=document_id,
                    title=os.path.splitext(filename)[0],
                    content=extracted_text,
                    source_path=file_path,
                    session_id=session_id,
                    metadata={
                        "file_type": "pdf",
                        "original_filename": filename,
                        "lecture_summary_path": lecture_path,
                        "extracted_text_path": text_path
                    }
                )

                # Add document to session
                session_manager.add_document_to_session(session_id, document_id)

                return jsonify({
                    "success": True,
                    "message": f"PDF '{filename}' processed successfully",
                    "document_id": document_id,
                    "vectorized": vector_success,
                    "lecture_generated": True,
                    "session_id": session_id,
                    "file_path": file_path
                })
            else:
                return jsonify({
                    "error": "PDF processing unavailable. Required services not initialized."
                }), 503

        elif file_type == 'text':
            # Process text file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add to vector store if available
            vector_success = False
            if vector_store:
                vector_success = vector_store.add_document(
                    document_id=document_id,
                    title=os.path.splitext(filename)[0],
                    content=content,
                    source_path=file_path,
                    session_id=session_id,
                    metadata={"file_type": "text", "original_filename": filename}
                )

            # Add document to session
            session_manager.add_document_to_session(session_id, document_id)

            return jsonify({
                "success": True,
                "message": f"Text file '{filename}' processed successfully",
                "document_id": document_id,
                "vectorized": vector_success,
                "session_id": session_id,
                "file_path": file_path
            })

    except Exception as e:
        print(f"Error processing document: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests with RAG integration"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Get session ID and message
    session_id = data.get('session_id')
    message = data.get('message')

    if not session_id or not session_manager.get_session(session_id):
        return jsonify({"error": "Invalid or missing session_id"}), 400

    if not message:
        return jsonify({"error": "No message provided"}), 400

    # Retrieve conversation history
    conversation_history = session_manager.format_for_cohere(session_id)

    # Retrieve relevant document chunks
    relevant_chunks = document_processor.retrieve_relevant_chunks(message, session_id=session_id)

    try:
        # Generate response using Cohere's RAG
        response = cohere_client.chat_with_docs(message, relevant_chunks, conversation_history)

        # Extract text and citations
        response_text = response.text
        citations = []
        if hasattr(response, 'citations'):
            # Format citations to be JSON-serializable
            citations = [
                {
                    'text': citation.text,
                    'start': citation.start,
                    'end': citation.end,
                    'sources': [
                        {
                            'document_id': source.id,
                            'title': source.document.get('title', ''),
                            'snippet': source.document.get('snippet', '')
                        }
                        for source in citation.sources
                    ]
                }
                for citation in response.citations
            ]

        # Add messages to conversation history
        session_manager.add_message_to_conversation(session_id, 'user', message)
        session_manager.add_message_to_conversation(
            session_id,
            'assistant',
            response_text,
            metadata={'citations': citations}
        )

        return jsonify({
            "message": response_text,
            "citations": citations,
            "has_context": len(relevant_chunks) > 0,
            "context_count": len(relevant_chunks),
            "conversation_id": len(session_manager.get_conversation(session_id)) // 2  # Count of conversation turns
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def list_documents():
    """Get information about all documents in a session"""
    session_id = request.args.get('session_id')

    if not session_id or not session_manager.get_session(session_id):
        return jsonify({"error": "Invalid or missing session_id"}), 400

    documents = document_processor.get_session_documents(session_id)
    return jsonify(documents)

@app.route('/api/text', methods=['POST'])
def process_raw_text():
    """Process raw text input"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    session_id = data.get('session_id')
    text_content = data.get('text')
    text_title = data.get('title', 'User provided text')

    if not session_id or not session_manager.get_session(session_id):
        return jsonify({"error": "Invalid or missing session_id"}), 400

    if not text_content:
        return jsonify({"error": "No text content provided"}), 400

    try:
        # Generate a unique filename for the text
        filename = f"text_{uuid.uuid4().hex[:8]}.txt"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save the text to a file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

        # Process the text directly (create chunks and embeddings)
        doc_id = document_processor.process_text(text_content, text_title, session_id, file_path)

        # Add document to session
        session_manager.add_document_to_session(session_id, doc_id)

        return jsonify({
            "success": True,
            "message": "Text processed successfully",
            "document_id": doc_id,
            "session_id": session_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def end_session(session_id):
    """End a session"""
    if not session_id or not session_manager.get_session(session_id):
        return jsonify({"error": "Session not found"}), 404

    # Don't delete the session, just mark it as inactive
    success = session_manager.update_session(session_id, {'active': False})

    if success:
        return jsonify({
            "success": True,
            "message": "Session ended successfully"
        })
    else:
        return jsonify({"error": "Failed to end session"}), 500

@app.route('/api/admin/clean-sessions', methods=['POST'])
def clean_sessions():
    """Admin endpoint to clean expired sessions"""
    # You might want to add authentication for this endpoint
    count = session_manager.clean_expired_sessions()
    return jsonify({
        "success": True,
        "message": f"Cleaned {count} expired sessions"
    })

@app.route('/api')
def api_docs():
    """API documentation endpoint"""
    return send_from_directory('static', 'api_docs.html')

@app.route('/api/analyze-pdf', methods=['POST'])
def analyze_pdf():
    """Analyze a PDF using Google Gemini"""
    # Check if Gemini client is available
    if not gemini_client:
        return jsonify({"error": "Gemini client is not available"}), 503

    # Check if session_id is provided
    session_id = request.form.get('session_id')
    if not session_id or not session_manager.get_session(session_id):
        return jsonify({"error": "Invalid or missing session_id"}), 400

    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Check if it's a PDF
    if not allowed_file(file.filename, 'pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # Get analysis type
    analysis_type = request.form.get('analysis_type', 'summary')

    # Create safe filename
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['PDF_FOLDER'], filename)
    file.save(file_path)

    try:
        # Process the PDF according to the requested analysis type
        if analysis_type == 'summary':
            result = gemini_client.summarize_document(file_path)
        elif analysis_type == 'detailed':
            result = gemini_client.analyze_document(file_path)
        elif analysis_type == 'tables':
            result = gemini_client.extract_key_information(file_path, information_type='tables')
        elif analysis_type == 'questions':
            questions = request.form.get('questions', 'What is this document about?')
            result = gemini_client.answer_questions(file_path, questions)
        else:
            result = gemini_client.summarize_document(file_path)

        # Also process the PDF with our regular document processor for RAG
        doc_id = document_processor.process_pdf(file_path, filename, session_id)

        # Add document to session
        session_manager.add_document_to_session(session_id, doc_id)

        return jsonify({
            "success": True,
            "message": f"PDF '{filename}' analyzed successfully",
            "document_id": doc_id,
            "analysis": result["text"],
            "model": result["model"],
            "session_id": session_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rag', methods=['POST'])
def rag_query():
    """
    Perform a RAG query using the vector store and LLM.
    """
    # Verify vector store is available
    if not vector_store:
        return jsonify({"error": "Vector store is not available"}), 503

    # Parse request
    data = request.json
    query = data.get('query')
    session_id = data.get('session_id')
    document_id = data.get('document_id')  # Optional

    if not query:
        return jsonify({"error": "Query is required"}), 400

    # Get relevant chunks
    chunks = vector_store.search_similar(
        query,
        limit=5,
        session_id=session_id,
        document_id=document_id
    )

    if not chunks:
        return jsonify({
            "answer": "I couldn't find any relevant information to answer your question.",
            "chunks": []
        }), 200

    # Format chunks as context
    context = "\n\n---\n\n".join([chunk["content"] for chunk in chunks])

    # Initialize Gemini client
    gemini_client = GeminiClient()

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
    result = gemini_client.process_text(rag_prompt)

    # Format chunk information for response
    chunk_info = []
    for chunk in chunks:
        chunk_info.append({
            "document_id": chunk["document_id"],
            "document_title": chunk["title"],
            "content_excerpt": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
            "similarity_score": chunk["similarity"]
        })

    return jsonify({
        "answer": result,
        "chunks": chunk_info
    })

@app.route('/api/process-document', methods=['POST'])
def process_document():
    """
    Process one or more document uploads and add them to the vector store.
    Expects multipart/form-data with:
    - file: Single PDF or text file, or
    - files[]: Multiple PDF or text files
    - session_id: (optional) Session ID to associate with the document(s)

    Returns a list of processed document IDs.
    """

    # Verify vector store is available
    # if not vector_store:
    #     return jsonify({"error": "Vector store is not available"}), 503

    # Get session_id (optional)
    session_id = request.form.get('session_id', 'default_session')

    # Check if any files were uploaded
    files = []

    # Try to get files from both possible formats:
    # 1. Single file with 'file' key
    # 2. Multiple files with 'files[]' key
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            files.append(file)

    if 'files[]' in request.files:
        file_list = request.files.getlist('files[]')
        for file in file_list:
            if file.filename != '':
                files.append(file)

    # Check if we have any valid files
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    # Process each file
    processed_documents = []
    failed_documents = []

    for file in files:
        # Check file format
        if allowed_file(file.filename, ['pdf', 'txt']):
            try:
                # Create a secure filename
                filename = secure_filename(file.filename)

                # Determine file type from extension
                file_extension = filename.rsplit('.', 1)[1].lower()

                # Save the file
                if file_extension == 'pdf':
                    file_path = os.path.join(app.config['PDF_FOLDER'], filename)
                else:
                    file_path = os.path.join(app.config['TEXT_FOLDER'], filename)

                file.save(file_path)
                print(f"File saved to {file_path}")

                # Process the file based on its type
                if file_extension == 'pdf':
                    # Process PDF file
                    document_id = process_pdf_to_vector_store(file_path, vector_store, session_id)
                else:
                    # Process text file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Generate a unique document ID
                    document_id = f"doc_{uuid.uuid4().hex[:10]}"

                    # Add to vector store
                    vector_store.add_document(
                        document_id=document_id,
                        title=filename,
                        content=content,
                        source_path=file_path,
                        session_id=session_id
                    )

                if document_id:
                    # Associate document with session if session_id was provided
                    if session_id != 'default_session' and hasattr(session_manager, 'add_document_to_session'):
                        session_manager.add_document_to_session(session_id, document_id)

                    # Add to processed documents list
                    processed_documents.append({
                        "document_id": document_id,
                        "filename": filename,
                        "file_type": file_extension
                    })
                else:
                    failed_documents.append({
                        "filename": filename,
                        "reason": "Failed to process file"
                    })

            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                traceback.print_exc()
                failed_documents.append({
                    "filename": file.filename,
                    "reason": str(e)
                })
        else:
            failed_documents.append({
                "filename": file.filename,
                "reason": "File format not supported"
            })

    # Return the results
    if processed_documents:
        return jsonify({
            "success": True,
            "message": f"Processed {len(processed_documents)} file(s) successfully",
            "documents": processed_documents,
            "failed": failed_documents,
            "total_processed": len(processed_documents),
            "total_failed": len(failed_documents)
        })
    else:
        return jsonify({
            "error": "Failed to process any files",
            "failed": failed_documents
        }), 500

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    """Process a PDF file and make it searchable"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Check if it's a PDF
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        # Save the file with a secure filename
        filename = secure_filename(file.filename)

        # Ensure folders exist
        pdf_folder = app.config.get('PDF_FOLDER', os.path.join(app.static_folder, 'uploads', 'pdfs'))
        text_folder = app.config.get('TEXT_FOLDER', os.path.join(app.static_folder, 'uploads', 'texts'))

        os.makedirs(pdf_folder, exist_ok=True)
        os.makedirs(text_folder, exist_ok=True)

        file_path = os.path.join(pdf_folder, filename)
        file.save(file_path)

        # Generate a document ID
        document_id = f"doc_{uuid.uuid4().hex[:10]}"

        # Extract text from PDF using Gemini
        extracted_text = "Text extraction not available"
        text_path = None
        vectorization_success = False

        try:
            # Check if Gemini client is available
            if gemini_client:
                print(f"Using Gemini to extract text from {file_path}")

                # Create extraction prompt for text contents
                extraction_prompt = """
                Extract all meaningful text content from this PDF document.
                Include all text from paragraphs, headers, bullet points, tables, and captions.
                Maintain the original structure as much as possible.
                Do not include your own commentary or analysis.
                """

                # Extract text with Gemini
                extract_result = gemini_client.process_pdf(file_path, prompt=extraction_prompt)
                extracted_text = extract_result["text"]

                # Save the extracted text
                text_filename = f"{os.path.splitext(filename)[0]}_extracted.txt"
                text_path = os.path.join(text_folder, text_filename)
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
                print(f"Extracted text saved to {text_path}")

                # Add to vector store if available
                if vector_store:
                    print(f"Adding document to vector store...")
                    vector_success = vector_store.add_document(
                        document_id=document_id,
                        title=os.path.splitext(filename)[0],
                        content=extracted_text,
                        source_path=file_path,
                        metadata={
                            "file_type": "pdf",
                            "original_filename": filename,
                            "extracted_text_path": text_path
                        }
                    )

                    if vector_success:
                        print(f"Document successfully added to vector store")
                        vectorization_success = True
                    else:
                        print(f"Failed to add document to vector store")
                else:
                    print("Vector store not available, falling back to text extraction only")
            else:
                print("Gemini client not available, falling back to PyPDF2")

                # Fall back to PyPDF2 if Gemini is not available
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        pdf_text = ""
                        for page_num in range(len(pdf_reader.pages)):
                            page = pdf_reader.pages[page_num]
                            pdf_text += page.extract_text() + "\n\n"

                        extracted_text = pdf_text

                    # Save the extracted text
                    text_filename = f"{os.path.splitext(filename)[0]}_extracted.txt"
                    text_path = os.path.join(text_folder, text_filename)
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(extracted_text)
                    print(f"Extracted text saved to {text_path}")

                except Exception as e:
                    print(f"PyPDF2 error: {e}")

        except Exception as e:
            print(f"Error extracting text: {e}")
            import traceback
            traceback.print_exc()

        # Return the results
        return jsonify({
            "success": True,
            "message": f"PDF '{filename}' processed successfully",
            "document_id": document_id,
            "file_paths": {
                "original_pdf": file_path,
                "extracted_text": text_path
            },
            "text_preview": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
            "has_text_extraction": extracted_text != "Text extraction not available",
            "vectorized": vectorization_success
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/ask-pdf', methods=['POST'])
def ask_pdf():
    """
    A simple endpoint to ask questions about a PDF without requiring a session ID.
    Expects JSON with:
    {
        "pdf_path": "/path/to/pdf/file.pdf",
        "question": "What is this document about?"
    }
    """
    data = request.json
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    pdf_path = data.get('pdf_path')
    question = data.get('question')

    if not pdf_path:
        return jsonify({"error": "Missing PDF path"}), 400
    if not question:
        return jsonify({"error": "Missing question"}), 400
    if not os.path.exists(pdf_path):
        return jsonify({"error": "PDF file not found"}), 404

    try:
        # Initialize Gemini client
        client = GeminiClient()

        # Create a prompt for answering questions about the PDF
        prompt = f"""
        I have a question about a PDF document. Please review the document content and answer my question based solely on the information in the document.

        My question is: {question}

        Please provide a detailed and accurate answer based exclusively on the PDF's content. Include specific information from the document to support your answer.
        """

        # Process the PDF with the question
        result = client.process_pdf(pdf_path, prompt=prompt, use_pro_model=True)

        return jsonify({
            "success": True,
            "question": question,
            "answer": result["text"],
            "pdf_path": pdf_path
        })

    except Exception as e:
        print(f"Error answering question: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/simple')
def simple_interface():
    """Provide a simple interface for PDF processing without sessions"""
    return send_from_directory('static', 'simple.html')

@app.route('/api/v1/search', methods=['POST'])
def api_v1_search():
    """
    API v1 endpoint for vectorized search
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON data"}), 400

        query = data.get('query', '')
        document_id = data.get('document_id')

        if not query:
            return jsonify({"error": "Query is required"}), 400

        # If we have a vector store, use it for search
        if 'vector_store' in globals() and vector_store:
            # Search with vector store
            results = vector_store.search_similar(
                query=query,
                limit=5,
                document_id=document_id
            )

            return jsonify({
                "query": query,
                "results": results,
                "count": len(results)
            })
        else:
            # Fallback to simple text search if vector store isn't available
            results = perform_simple_text_search(query, document_id)

            return jsonify({
                "query": query,
                "results": results,
                "count": len(results),
                "search_type": "simple_text"  # Indicate this is not vector search
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    """
    Search the vector store for relevant documents.
    Optional filters:
    - document_id: Filter to a specific document
    - session_id: Filter to a specific session
    """
    # Verify vector store is available
    if not vector_store:
        return jsonify({"error": "Vector store is not available"}), 503

    # Get JSON data
    data = request.json
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    # Get required fields
    query = data.get('query')
    if not query:
        return jsonify({"error": "query is required"}), 400

    # Get optional filter fields
    document_id = data.get('document_id')  # Optional
    session_id = data.get('session_id')    # Optional

    try:
        # Search the vector store
        results = vector_store.search_similar(
            query=query,
            limit=10,  # Return top 10 results
            session_id=session_id,
            document_id=document_id
        )

        # If no results from vector search, try text search
        if not results:
            print("No vector search results, falling back to text search")
            results = perform_simple_text_search(query, document_id)

        return jsonify({
            "query": query,
            "results": results,
            "filters": {
                "document_id": document_id,
                "session_id": session_id
            }
        })

    except Exception as e:
        print(f"Error during search: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def perform_simple_text_search(query, document_id=None):
    """
    Perform a simple text-based search when vector store is not available
    """
    results = []

    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    query_terms = query_lower.split()

    # Define the folder containing text files
    text_folder = app.config.get('TEXT_FOLDER', os.path.join(app.static_folder, 'uploads', 'texts'))

    # Find all text files
    text_files = []
    for file in os.listdir(text_folder):
        if file.endswith('.txt') and 'extracted' in file:
            text_files.append(os.path.join(text_folder, file))

    # Search through each text file
    for text_path in text_files:
        file_name = os.path.basename(text_path)
        doc_title = os.path.splitext(file_name)[0].replace('_extracted', '')

        # If document_id is specified, only search that document
        if document_id:
            # Simple check if the document ID might be in the filename
            # This is just a basic heuristic, not reliable for production
            if document_id not in text_path:
                continue

        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split the content into paragraphs
            paragraphs = content.split('\n\n')

            for i, paragraph in enumerate(paragraphs):
                if not paragraph.strip():
                    continue

                # Simple scoring: count term occurrences and calculate similarity
                paragraph_lower = paragraph.lower()

                # Check if any term is in the paragraph
                matches = 0
                for term in query_terms:
                    if term in paragraph_lower:
                        matches += paragraph_lower.count(term)

                if matches > 0:
                    # Calculate a simple similarity score
                    similarity = matches / (len(query_terms) + 0.1)  # Adding 0.1 to avoid division by zero

                    # Create a result with the paragraph and metadata
                    curr_doc_id = f"doc_{hash(text_path) % 10000:04d}_{i}"

                    # Add to results if similarity is above threshold
                    results.append({
                        "document_id": document_id or curr_doc_id,
                        "title": doc_title,
                        "content": paragraph,
                        "chunk_index": i,
                        "similarity": similarity
                    })
        except Exception as e:
            print(f"Error processing {text_path}: {e}")
            continue

    # Sort by similarity score
    results.sort(key=lambda x: x["similarity"], reverse=True)

    # Return top results
    return results[:5]

@app.route('/api/process-text', methods=['POST'])
def process_text():
    """
    Process raw text and add it to the vector store.
    Expects JSON with:
    {
        "text": "The text content to process",
        "title": "Optional title for the document",
        "session_id": "Optional session ID to associate with the document"
    }
    """
    # Verify vector store is available
    if not vector_store:
        return jsonify({"error": "Vector store is not available"}), 503

    # Get JSON data
    data = request.json
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    # Get required fields
    text = data.get('text')
    if not text:
        return jsonify({"error": "text field is required"}), 400

    # Get optional fields
    title = data.get('title', f"Text Document {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    session_id = data.get('session_id', 'default_session')

    try:
        # Generate a unique document ID
        document_id = f"doc_{uuid.uuid4().hex[:10]}"

        # Save text to file for reference (optional)
        filename = f"{document_id}.txt"
        text_path = os.path.join(app.config['TEXT_FOLDER'], filename)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"Processing text document: {title}")
        print(f"Text length: {len(text)} characters")

        # Add to vector store
        success = vector_store.add_document(
            document_id=document_id,
            title=title,
            content=text,
            source_path=text_path,
            session_id=session_id,
            metadata={
                "source_type": "direct_text",
                "character_count": len(text),
                "created_at": datetime.now().isoformat()
            }
        )

        if success:
            print(f"Text successfully added to vector store with ID: {document_id}")

            # Associate document with session if session_id was provided and not default
            if session_id != 'default_session' and hasattr(session_manager, 'add_document_to_session'):
                session_manager.add_document_to_session(session_id, document_id)
                print(f"Document {document_id} associated with session {session_id}")

            return jsonify({
                "success": True,
                "message": "Text processed and added to vector store",
                "document_id": document_id,
                "title": title,
                "text_path": text_path,
                "character_count": len(text)
            })
        else:
            return jsonify({
                "error": "Failed to add text to vector store"
            }), 500

    except Exception as e:
        print(f"Error processing text: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-lecture', methods=['POST'])
def generate_lecture():
    """
    Generate a lecture-style summary from documents.

    Expects JSON with:
    {
        "session_id": "Optional: Session ID containing the documents. If not provided, uses all documents.",
        "document_ids": "Optional: List of specific document IDs to include. If provided, overrides session_id.",
        "title": "Optional title for the lecture",
        "style": "Optional style parameter: 'academic', 'conversational', etc."
    }

    Returns a lecture-style summary based on the specified documents.
    """
    # Verify vector store is available
    if not vector_store:
        return jsonify({"error": "Vector store is not available"}), 503

    # Get JSON data
    data = request.json
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    # Get optional fields
    session_id = data.get('session_id', 'default_session')
    document_ids = data.get('document_ids', [])
    title = data.get('title', f"Lecture Summary {datetime.now().strftime('%Y-%m-%d')}")
    style = data.get('style', 'academic')

    try:
        # Get documents based on the provided parameters
        documents = []

        if document_ids:
            # If specific document IDs are provided, retrieve those documents
            for doc_id in document_ids:
                # Get the document chunks
                chunks = vector_store.get_document_chunks(doc_id)
                if chunks:
                    # Get the document info from the first chunk
                    first_chunk = chunks[0]
                    documents.append({
                        "document_id": doc_id,
                        "title": first_chunk.get('title', 'Untitled Document'),
                        "chunks": chunks
                    })
        elif session_id != 'default_session':
            # If session_id is provided, get documents from that session
            documents_info = vector_store.get_documents_by_session(session_id)

            if not documents_info:
                return jsonify({"error": "No documents found in this session"}), 404

            for doc in documents_info:
                doc_id = doc.get('document_id')
                chunks = vector_store.get_document_chunks(doc_id)
                if chunks:
                    documents.append({
                        "document_id": doc_id,
                        "title": doc.get('title', 'Untitled Document'),
                        "chunks": chunks
                    })
        else:
            # If neither document_ids nor session_id is provided, get all available documents
            # This requires a function to get all documents from the vector store
            try:
                # Execute a direct query to get all unique document IDs
                conn = vector_store.conn
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT document_id FROM documents")
                all_doc_ids = [row[0] for row in cursor.fetchall()]
                cursor.close()

                for doc_id in all_doc_ids:
                    chunks = vector_store.get_document_chunks(doc_id)
                    if chunks:
                        first_chunk = chunks[0]
                        documents.append({
                            "document_id": doc_id,
                            "title": first_chunk.get('title', 'Untitled Document'),
                            "chunks": chunks
                        })
            except Exception as e:
                print(f"Error retrieving all documents: {e}")
                traceback.print_exc()
                return jsonify({"error": "Error retrieving documents"}), 500

        if not documents:
            return jsonify({"error": "No documents found"}), 404

        print(f"Found {len(documents)} documents for lecture generation")

        # Prepare document content for summarization
        document_contents = []

        for doc in documents:
            doc_id = doc.get('document_id')
            doc_title = doc.get('title', 'Untitled Document')

            # Combine chunks into full text
            chunks = doc.get('chunks', [])
            full_text = "\n\n".join([chunk.get('content', '') for chunk in chunks])

            document_contents.append({
                "title": doc_title,
                "text": full_text
            })

        # Create prompt for lecture generation
        style_instructions = {
            'academic': "Create an academic lecture with clear sections, scholarly language, and citations.",
            'conversational': "Write a conversational lecture as if speaking directly to students. Use informal language and rhetorical questions.",
            'concise': "Create a concise, point-form summary of the key concepts.",
            'narrative': "Create a narrative-style lecture that tells a story while educating about the topic."
        }

        style_prompt = style_instructions.get(style, style_instructions['academic'])

        lecture_prompt = f"""Based on the following documents, create a comprehensive lecture titled "{title}". {style_prompt}

The lecture should:
1. Begin with an introduction explaining the main topics
2. Have a logical structure with clear sections and transitions
3. Highlight key concepts and their relationships
4. Use examples to illustrate important points
5. End with a summary and potential discussion questions

Documents for reference:
"""

        for i, doc in enumerate(document_contents):
            lecture_prompt += f"\n\nDOCUMENT {i+1}: {doc['title']}\n{doc['text'][:5000]}"  # Limit text length for each doc

        # Generate lecture using Cohere
        print("Generating lecture using Cohere...")
        cohere_client = CohereClient()

        response = cohere_client.client.chat(
            model=cohere_client.chat_model,
            messages=[{"role": "user", "content": lecture_prompt}],
            temperature=0.7,
            max_tokens=3000
        )

        # Extract text from response
        response_text = ""
        if hasattr(response, 'message') and hasattr(response.message, 'content'):
            content_items = response.message.content
            if content_items and len(content_items) > 0:
                for item in content_items:
                    if hasattr(item, 'text'):
                        response_text += item.text

        # Generate a unique ID for the lecture
        lecture_id = f"lecture_{uuid.uuid4().hex[:10]}"

        # Save the lecture to a file
        lecture_path = os.path.join(app.config['TEXT_FOLDER'], f"{lecture_id}.txt")
        with open(lecture_path, 'w', encoding='utf-8') as f:
            f.write(response_text)

        # Also add the lecture as a document in the vector store
        vector_store.add_document(
            document_id=lecture_id,
            title=title,
            content=response_text,
            source_path=lecture_path,
            session_id=session_id,
            metadata={
                "source_type": "generated_lecture",
                "source_documents": [doc.get('document_id') for doc in documents],
                "style": style,
                "created_at": datetime.now().isoformat()
            }
        )

        # Associate lecture with session if using a non-default session
        if session_id != 'default_session' and hasattr(session_manager, 'add_document_to_session'):
            session_manager.add_document_to_session(session_id, lecture_id)

        return jsonify({
            "success": True,
            "lecture_id": lecture_id,
            "title": title,
            "content": response_text,
            "source_documents": len(documents),
            "file_path": lecture_path
        })

    except Exception as e:
        print(f"Error generating lecture: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/video-search', methods=['POST'])
def video_search():
    """
    Search the vector store and generate a video from the results.
    Expects JSON with:
    {
        "query": "The search query",
        "document_id": "Optional document ID to filter search",
        "session_id": "Optional session ID to filter search"
    }
    Returns a link to the generated video.
    """
    # Check if video module is available
    if not HAS_VIDEO_MODULE:
        return jsonify({"error": "Video generation module not available"}), 503

    # Verify vector store is available
    if not vector_store:
        return jsonify({"error": "Vector store is not available"}), 503

    # Get JSON data
    data = request.json
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    # Get required fields
    query = data.get('query')
    if not query:
        return jsonify({"error": "query is required"}), 400

    # Get optional filter fields
    document_id = data.get('document_id')  # Optional
    session_id = data.get('session_id')    # Optional

    try:
        # Search the vector store - same as regular search
        results = vector_store.search_similar(
            query=query,
            limit=5,  # Return top 5 results for video
            session_id=session_id,
            document_id=document_id
        )

        # If no results from vector search, try text search
        if not results:
            print("No vector search results, falling back to text search")
            results = perform_simple_text_search(query, document_id)

        if not results:
            return jsonify({"error": "No relevant content found for video generation"}), 404

        # Extract text content from search results
        content_texts = [result["content"] for result in results]
        combined_text = "\n\n".join(content_texts)

        # Generate a title for the video
        video_title = f"Video on: {query}"

        # Call the video generation function
        video_url = vid.generate_video(
            title=video_title,
            content=combined_text,
            query=query
        )

        return jsonify({
            "success": True,
            "query": query,
            "video_url": video_url,
            "message": "Video generated successfully",
            "result_count": len(results)
        })

    except Exception as e:
        print(f"Error during video generation: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Video generation failed: {str(e)}"}), 500

@app.route('/api/videos', methods=['GET'])
def list_videos():
    """
    List all generated videos.
    Query parameters:
    - limit: Maximum number of videos to return (default: 10)
    """
    # Check if video module is available
    if not HAS_VIDEO_MODULE:
        return jsonify({"error": "Video module not available"}), 503

    try:
        # Get limit parameter
        limit = request.args.get('limit', 10, type=int)

        # Get list of videos
        videos = vid.list_videos(limit=limit)

        return jsonify({
            "success": True,
            "count": len(videos),
            "videos": videos
        })

    except Exception as e:
        print(f"Error listing videos: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video_info(video_id):
    """
    Get information about a specific video.
    """
    # Check if video module is available
    if not HAS_VIDEO_MODULE:
        return jsonify({"error": "Video module not available"}), 503

    try:
        # Get video info
        video_info = vid.get_video_info(video_id)

        if video_info:
            return jsonify({
                "success": True,
                "video": video_info
            })
        else:
            return jsonify({"error": "Video not found"}), 404

    except Exception as e:
        print(f"Error getting video info: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/rag-chat', methods=['POST'])
def rag_chat():
    """
    Chat with documents using RAG (Retrieval Augmented Generation).

    Expects JSON with:
    {
        "query": "User's question or message",
        "document_id": "Optional document ID to filter search",
        "session_id": "Optional session ID to filter search",
        "history": "Optional array of previous messages in the conversation"
    }

    Returns a response generated based on relevant document chunks.
    """
    # Verify vector store is available
    if not vector_store:
        return jsonify({"error": "Vector store is not available"}), 503

    # Get JSON data
    data = request.json
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    # Get required fields
    query = data.get('query')
    if not query:
        return jsonify({"error": "query is required"}), 400

    # Get optional filter fields
    document_id = data.get('document_id')  # Optional
    session_id = data.get('session_id')    # Optional
    history = data.get('history', [])      # Optional conversation history

    try:
        # Step 1: Search the vector store for relevant chunks
        print(f"Searching for relevant chunks for: {query}")
        results = vector_store.search_similar(
            query=query,
            limit=5,  # Return top 5 results
            session_id=session_id,
            document_id=document_id
        )

        # If no results from vector search, try text search as fallback
        if not results:
            print("No vector search results, falling back to text search")
            results = perform_simple_text_search(query, document_id)

        if not results:
            # If still no results, return a message indicating no relevant information was found
            return jsonify({
                "response": "I couldn't find any relevant information to answer your question.",
                "query": query,
                "sources": []
            })

        # Step 2: Prepare the documents for the Cohere RAG API
        cohere_docs = []
        seen_ids = set()  # Track IDs we've already used

        for result in results:
            # Create a base document ID
            base_id = f"{result.get('document_id', '')}_chunk{result.get('chunk_index', 0)}"

            # Make sure the ID is unique
            doc_id = base_id
            counter = 1
            while doc_id in seen_ids:
                doc_id = f"{base_id}_{counter}"
                counter += 1

            # Add the ID to our tracking set
            seen_ids.add(doc_id)

            cohere_docs.append({
                "id": doc_id,
                "data": {
                    "title": result.get("title", "Unknown Title"),
                    "text": result.get("content", ""),
                    "url": result.get("url", ""),
                    "similarity_score": result.get("similarity", 0)
                }
            })

        # Step 3: Initialize Cohere client
        cohere_client = CohereClient()

        # Step 4: Format conversation history if provided
        formatted_history = []
        if history:
            for msg in history:
                if 'role' in msg and 'content' in msg:
                    formatted_history.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })

        # Step 5: Generate response using Cohere with RAG
        print("Generating RAG response with Cohere...")
        response = cohere_client.chat_with_docs(
            message=query,
            documents=cohere_docs,
            conversation_history=formatted_history
        )

        # Extract response text
        response_text = ""
        if hasattr(response, 'text'):
            response_text = response.text
        else:
            # Try to extract text from the newer Cohere API response structure
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                content_items = response.message.content
                if content_items and len(content_items) > 0:
                    for item in content_items:
                        if hasattr(item, 'text'):
                            response_text += item.text

        # Format citations if available
        citations = []
        if hasattr(response, 'citations'):
            for citation in response.citations:
                citation_obj = {
                    "text": citation.text,
                    "start": citation.start,
                    "end": citation.end,
                    "sources": []
                }

                # Add source information
                if hasattr(citation, 'sources'):
                    for source in citation.sources:
                        # Extract appropriate data from the document format
                        source_doc = {}
                        if hasattr(source, 'document') and source.document:
                            source_doc = source.document

                        source_obj = {
                            "id": source.id,
                            "title": source_doc.get('title', '') if isinstance(source_doc, dict) else '',
                            "snippet": source_doc.get('text', '') if isinstance(source_doc, dict) else ''
                        }
                        citation_obj["sources"].append(source_obj)

                citations.append(citation_obj)

        # Step 6: Prepare source information for the response
        sources = []
        for i, doc in enumerate(cohere_docs):
            sources.append({
                "id": doc["id"],
                "title": doc["data"]["title"],
                "snippet": doc["data"]["text"][:200] + "..." if len(doc["data"]["text"]) > 200 else doc["data"]["text"],
                "relevance": doc["data"]["similarity_score"]
            })

        # Return the RAG response
        return jsonify({
            "response": response_text,
            "query": query,
            "sources": sources,
            "citations": citations,
            "source_count": len(sources)
        })

    except Exception as e:
        print(f"Error during RAG chat: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-video', methods=['POST'])
def generate_video_endpoint():
    """
    Generate a video based on a user query and related content.

    Expects JSON with:
    {
        "query": "User's query for the video",
        "document_id": "Optional document ID to filter search",
        "session_id": "Optional session ID to filter search"
    }

    Returns URL to the generated video.
    """
    # Check if video module is available
    if not HAS_VIDEO_MODULE:
        return jsonify({"error": "Video generation module not available"}), 503

    # Verify vector store is available
    if not vector_store:
        return jsonify({"error": "Vector store is not available"}), 503

    # Get JSON data
    data = request.json
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    # Get required fields
    query = data.get('query')
    if not query:
        return jsonify({"error": "query is required"}), 400

    # Get optional filter fields
    document_id = data.get('document_id')  # Optional
    session_id = data.get('session_id')    # Optional

    try:
        # Search the vector store for relevant content
        print(f"Searching for relevant content for video about: {query}")
        results = vector_store.search_similar(
            query=query,
            limit=5,  # Return top 5 results for video
            session_id=session_id,
            document_id=document_id
        )

        # If no results from vector search, try text search as fallback
        if not results:
            print("No vector search results, falling back to text search")
            results = perform_simple_text_search(query, document_id)

        if not results:
            return jsonify({"error": "No relevant content found for video generation"}), 404

        # Extract text content from search results
        content_texts = [result["content"] for result in results]
        combined_text = "\n\n".join(content_texts)

        # Generate a title for the video
        video_title = f"Video on: {query}"

        try:
            # Call the video generation function
            video_url = vid.generate_video(
                title=video_title,
                content=combined_text,
                query=query,
                style="educational"
            )

            return jsonify({
                "success": True,
                "query": query,
                "video_url": video_url,
                "message": "Video generation initiated",
                "result_count": len(results)
            })

        except Exception as e:
            print(f"Error during video generation: {e}")
            traceback.print_exc()
            return jsonify({"error": f"Video generation failed: {str(e)}"}), 500

    except Exception as e:
        print(f"Error during content search for video: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)

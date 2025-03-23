from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_cors import CORS
from pathlib import Path
import traceback

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
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

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
def process_text():
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
    Process a document and add it to the vector store.
    """

    # Verify vector store is available
    # if not vector_store:
    #     return jsonify({"error": "Vector store is not available"}), 503

    # Check if session_id is provided
    # session_id = request.form.get('session_id')
    # if not session_id:
    #     return jsonify({"error": "session_id is required"}), 400

    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Check if it's an acceptable format
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "File format not supported"}), 400

    # Save the file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['PDF_FOLDER'], filename)
    file.save(file_path)

    is_uploaded = add_pdf_to_vstore(file_path)

    if not is_uploaded:
        return jsonify({"error": "Failed to process document"}), 500

    return jsonify({
        "success": True,
        "message": "Document processed and added to vector store"
        })

    

    # try:
    #     # Process different file types
    #     if filename.lower().endswith('.pdf'):
    #         # Process PDF
    #         from process_pdf_to_vectors import process_pdf_to_vector_store
    #         document_id = process_pdf_to_vector_store(file_path, vector_store, session_id)
    #     elif filename.lower().endswith('.txt'):
    #         # Process text file
    #         with open(file_path, 'r', encoding='utf-8') as f:
    #             content = f.read()

    #         # Generate a unique document ID
    #         document_id = f"doc_{uuid.uuid4().hex[:10]}"

    #         # Add to vector store
    #         vector_store.add_document(
    #             document_id=document_id,
    #             title=os.path.splitext(filename)[0],
    #             content=content,
    #             source_path=file_path,
    #             session_id=session_id
    #         )

    #     if document_id:
    #         return jsonify({
    #             "success": True,
    #             "message": "Document processed and added to vector store",
    #             "document_id": document_id
    #         })
    #     else:
    #         return jsonify({"error": "Failed to process document"}), 500

    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500


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

        # Extract text from PDF using a simple approach (install PyPDF2 if needed)
        extracted_text = "Text extraction not available"
        text_path = None

        try:
            # First try using PyPDF2
            try:
                import PyPDF2
                with open(file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    pdf_text = ""
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        pdf_text += page.extract_text() + "\n\n"

                    extracted_text = pdf_text
            except (ImportError, Exception) as e:
                print(f"PyPDF2 error: {e}")
                # If PyPDF2 is not available or fails, try a different approach
                # You might want to install pdfplumber or other PDF libraries

            # Save the extracted text
            if extracted_text and extracted_text != "Text extraction not available":
                text_filename = f"{os.path.splitext(filename)[0]}_extracted.txt"
                text_path = os.path.join(text_folder, text_filename)
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
                print(f"Extracted text saved to {text_path}")
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
            "has_text_extraction": extracted_text != "Text extraction not available"
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

# Add an alias for compatibility
@app.route('/api/search', methods=['POST'])
def api_search():
    """
    Alias for /api/v1/search for backward compatibility
    """
    return api_v1_search()

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)

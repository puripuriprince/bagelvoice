import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# API configurations
COHERE_API_KEY = os.environ.get('COHERE_API_KEY')
if not COHERE_API_KEY:
    # Fallback for development only
    COHERE_API_KEY = "DEt2F21MaVaT1s4W8Ld35Smw9KKUlA9bgnqmOTe6"

# Flask app configurations
DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-for-development')

# Base directories
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
PDF_FOLDER = os.path.join(UPLOAD_FOLDER, 'pdfs')
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, 'audio')

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf': {'pdf'},
    'text': {'txt'},
    'audio': {'mp3', 'wav'},
}

# Maximum file size (16MB)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# RAG configurations
CHUNK_SIZE = 1000  # Size of text chunks for embedding
CHUNK_OVERLAP = 200  # Overlap between chunks
SESSION_EXPIRY = 24 * 60 * 60  # Session expiry in seconds (24 hours)

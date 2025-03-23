# BagelVoice

A document question-answering system with vector search capabilities, powered by Flask, PostgreSQL with pgvector, and LLM integrations.

## Quickstart Guide

Follow these instructions to set up and run BagelVoice on a new machine.

### Prerequisites

- Python 3.9+
- PostgreSQL 14+ with pgvector extension
- Node.js 18+ (for frontend)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/bagelvoice.git
cd bagelvoice
```

### 2. Set Up PostgreSQL with pgvector

Install PostgreSQL and pgvector:

#### Windows

1. Download and install PostgreSQL from the [official website](https://www.postgresql.org/download/windows/)
   - During installation, set the password for the postgres user
   - Make sure to check the option to install "PostgreSQL Server" and "Command Line Tools"

2. Install pgvector:
   - Download the [pgvector release](https://github.com/pgvector/pgvector/releases) for your PostgreSQL version
   - Extract the files to a temporary folder
   - Copy the files to your PostgreSQL installation's `lib` directory
   - Open Command Prompt as Administrator and run:
     ```
     cd "C:\Program Files\PostgreSQL\14\bin"
     psql -U postgres -c "CREATE EXTENSION vector;" notebook
     ```

#### macOS (using Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Install pgvector extension
brew install pgvector
```

#### Ubuntu/Debian

```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update

# Install PostgreSQL
sudo apt-get -y install postgresql-14

# Install build dependencies for pgvector
sudo apt-get -y install postgresql-server-dev-14 build-essential

# Download and install pgvector
git clone --branch v0.4.4 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
cd ..
```

#### Create Database and Enable pgvector

```bash
# Create a new database (as postgres user)
sudo -u postgres psql -c "CREATE DATABASE notebook;"

# Create a user (change password as needed)
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE notebook TO postgres;"

# Connect to the database and enable pgvector
sudo -u postgres psql -d notebook -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r flask/requirements.txt

# Install additional dependencies for vector store
pip install psycopg2-binary pgvector cohere
```

### 4. Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Flask
SECRET_KEY=your-secret-key
DEBUG=True

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=notebook
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# API Keys
COHERE_API_KEY=your-cohere-api-key
GOOGLE_API_KEY=your-google-api-key
```

### 5. Run the Setup Script

#### On Windows:
```
setup.bat
```

#### On macOS/Linux:
```
chmod +x setup.sh
./setup.sh
```

### 6. Run the Backend

```bash
# Make sure your virtual environment is activated
cd flask
python app.py
```

The Flask backend will start on http://localhost:5000.

### 7. Testing the Application

#### Process a Document

```bash
python flask/test_text_processing.py path/to/your/sample.txt --title "Sample Text"
```

#### Search a Document

After processing a document, you'll receive a document ID. Use it to test the search:

```bash
python flask/test_search.py your_document_id
```

#### Direct Text Processing API

You can also directly use the API to process raw text:

```bash
curl -X POST http://localhost:5000/api/process-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text content here...",
    "title": "Optional Document Title",
    "session_id": "unique-session-id"
  }'
```

### Common Issues and Troubleshooting

1. **PostgreSQL Connection Issues**:
   - Ensure PostgreSQL is running:
     - On Windows: Check Services app for "postgresql-x64-14" service
     - On macOS/Linux: `ps aux | grep postgres`
   - Check connection parameters in `.env` file

2. **pgvector Extension**:
   - Verify pgvector is installed:
     - On Windows: `psql -U postgres -d notebook -c "\dx"`
     - On macOS/Linux: `sudo -u postgres psql -d notebook -c "\dx"`

3. **API Key Errors**:
   - Make sure all required API keys are set in your `.env` file

4. **Module Not Found Errors**:
   - Ensure all dependencies are installed: `pip install -r flask/requirements.txt`

5. **Windows-Specific Path Issues**:
   - If you encounter path-related errors on Windows, ensure that paths in the code use
     `os.path.join()` instead of hardcoded forward slashes

### System Architecture

BagelVoice consists of:

1. **Flask Backend**: API server handling document processing and search
2. **PostgreSQL with pgvector**: Vector database for semantic search
3. **LLM Integration**: Cohere and Google Gemini for text processing and embeddings

### API Endpoints

- `/api/process-document`: Upload and process PDF/text files
- `/api/process-text`: Process raw text directly
- `/api/v1/search`: Search processed documents
- `/api/generate-lecture`: Generate a lecture-style summary from session documents
- `/api/health`: Health check endpoint

### 8. Lecture Generation

BagelVoice can automatically generate comprehensive lecture notes from your uploaded documents. This feature combines content from all documents in a session and creates a well-structured lecture.

#### Generate a Lecture

After uploading documents to a session, you can generate a lecture:

```bash
python flask/test_generate_lecture.py your_session_id --title "Your Lecture Title" --style academic
```

Available lecture styles:
- `academic`: Formal scholarly style with sections and citations
- `conversational`: Informal style as if speaking directly to students
- `concise`: Point-form summary of key concepts
- `narrative`: Story-telling approach to the content

The generated lecture is also saved as a document in your session and can be searched like any other document.

#### API Usage Example

```bash
curl -X POST http://localhost:5000/api/generate-lecture \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "title": "Comprehensive Lecture on Topic",
    "style": "academic"
  }'
```

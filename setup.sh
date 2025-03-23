#!/bin/bash

# BagelVoice Setup Script
echo "=== BagelVoice Setup Script ==="
echo "This script will set up the BagelVoice application environment"
echo

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"
if [[ "$python_version" < "3.9" ]]; then
  echo "Warning: This application works best with Python 3.9 or higher"
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r flask/requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
  echo "Creating .env file from example..."
  cp .env.example .env
  echo "Please edit the .env file and add your API keys"
fi

# Check if PostgreSQL is installed
if command -v psql &> /dev/null; then
  echo "PostgreSQL is installed"

  # Check if pgvector is installed
  if psql -t -c "SELECT * FROM pg_available_extensions WHERE name = 'vector'" postgres 2>/dev/null | grep -q 'vector'; then
    echo "pgvector extension is available"
  else
    echo "WARNING: pgvector extension is not installed in PostgreSQL"
    echo "Please install pgvector according to the instructions in README.md"
  fi
else
  echo "WARNING: PostgreSQL is not installed or not in PATH"
  echo "Please install PostgreSQL according to the instructions in README.md"
fi

# Create required directories
echo "Creating required directories..."
mkdir -p flask/static/uploads/pdfs
mkdir -p flask/static/uploads/texts
mkdir -p flask/static/temp
mkdir -p flask/sessions

echo
echo "=== Setup Completed ==="
echo "To start the application:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the application: cd flask && python app.py"
echo "3. Access the application at http://localhost:5000"
echo
echo "For more information, please refer to the README.md file"

@echo off
setlocal enabledelayedexpansion

echo === BagelVoice Setup Script for Windows ===
echo This script will set up the BagelVoice application environment
echo.

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo Python version: %python_version%

:: Create virtual environment
echo Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

:: Install Python dependencies
echo Installing Python dependencies...
pip install --upgrade pip
pip install -r flask\requirements.txt

:: Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    echo Please edit the .env file and add your API keys
)

:: Check if PostgreSQL is installed
where psql >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo PostgreSQL is installed

    :: Check if pgvector is installed
    psql -t -c "SELECT * FROM pg_available_extensions WHERE name = 'vector'" postgres >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        echo pgvector extension is available
    ) else (
        echo WARNING: pgvector extension is not installed in PostgreSQL
        echo Please install pgvector according to the instructions in README.md
    )
) else (
    echo WARNING: PostgreSQL is not installed or not in PATH
    echo Please install PostgreSQL according to the instructions in README.md
)

:: Create required directories
echo Creating required directories...
if not exist flask\static\uploads\pdfs mkdir flask\static\uploads\pdfs
if not exist flask\static\uploads\texts mkdir flask\static\uploads\texts
if not exist flask\static\temp mkdir flask\static\temp
if not exist flask\sessions mkdir flask\sessions

echo.
echo === Setup Completed ===
echo To start the application:
echo 1. Activate the virtual environment: venv\Scripts\activate
echo 2. Run the application: cd flask ^& python app.py
echo 3. Access the application at http://localhost:5000
echo.
echo For more information, please refer to the README.md file

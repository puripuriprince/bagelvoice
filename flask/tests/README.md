# BagelVoice Test Scripts

This directory contains test scripts for the BagelVoice Flask application. These scripts test various functionalities of the application, from uploading PDFs to searching and generating content based on the documents.

## Running Tests

All test scripts can be run using Python's module system. The general pattern is:

```bash
python -m flask.tests.test_name [arguments]
```

### Example Commands

1. **Full Pipeline Test** (with multiple documents):
   ```bash
   python -m flask.tests.test_full_pipeline path/to/doc1.pdf path/to/doc2.pdf path/to/doc3.pdf
   ```

2. **Upload Test** (with multiple documents):
   ```bash
   python -m flask.tests.test_upload path/to/doc1.pdf path/to/doc2.pdf
   ```

3. **RAG Chat Test**:
   ```bash
   python -m flask.tests.test_rag_chat --query "Your question" --document_id doc_12345
   ```

4. **Video Search Test**:
   ```bash
   python -m flask.tests.test_video_search --query "main concepts" --document_id doc_12345
   ```

5. **Generate Lecture Test**:
   ```bash
   python -m flask.tests.test_generate_lecture --document_ids doc_12345,doc_67890
   ```

## Test Files Description

- **test_upload.py**: Tests the PDF upload functionality. Now supports uploading multiple PDFs in a single request.
- **test_full_pipeline.py**: Tests the end-to-end pipeline from PDF upload to search. Supports processing multiple documents in a single run.
- **test_pdf_processing.py**: Tests the PDF processing functionality specifically.
- **test_search.py**: Tests the search functionality.
- **test_rag_chat.py**: Tests the RAG chat functionality.
- **test_video_search.py**: Tests the video search functionality.
- **test_generate_lecture.py**: Tests the lecture generation functionality.
- **test_text_processing.py**: Tests text processing utilities.

## Output Files

Most test scripts will save their output as JSON files with timestamps to avoid overwriting previous results. These files are useful for debugging and analysis.

## Multi-Document Upload Support

The test scripts have been updated to support uploading multiple documents in a single request. This matches the updated backend functionality which now allows processing multiple files in a single API call. Key changes include:

- Upload tests now accept multiple file paths as arguments
- The test scripts construct proper multipart requests with multiple files
- Results handling has been updated to process arrays of document IDs
- Search and other downstream tests have been updated to work with multiple documents

## Typical Testing Workflow

1. Run the upload test with one or more PDFs
2. Use the returned document ID(s) to test search functionality
3. Use document ID(s) to test more advanced features like RAG chat or video generation

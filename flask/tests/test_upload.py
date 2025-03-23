#!/usr/bin/env python3
"""
Test script for uploading PDFs to the Flask application.
Usage: python -m flask.tests.test_upload path/to/your/document1.pdf [path/to/your/document2.pdf ...]
"""

import argparse
import os
import sys
import requests
import json
from pprint import pprint
from pathlib import Path
import time

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_pdf_upload(pdf_paths):
    """Test uploading multiple PDFs to the Flask app"""
    # Check if files exist and are PDFs
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"Error: File {pdf_path} does not exist")
            return False

        if not pdf_path.lower().endswith('.pdf'):
            print(f"Error: File {pdf_path} is not a PDF")
            return False

    print(f"Testing PDF upload with {len(pdf_paths)} files:")
    for pdf_path in pdf_paths:
        file_size = os.path.getsize(pdf_path)
        print(f"- {pdf_path} ({file_size/1024/1024:.2f} MB)")

    # Prepare the files for upload
    print("Preparing upload...")
    files = []
    for pdf_path in pdf_paths:
        with open(pdf_path, 'rb') as f:
            files.append(('files[]', (os.path.basename(pdf_path), f.read(), 'application/pdf')))

    try:
        # Flask app base URL
        base_url = 'http://localhost:5000'

        # Send request to /api/process-document endpoint
        print(f"Sending request to {base_url}/api/process-document...")
        start_time = time.time()

        response = requests.post(
            f"{base_url}/api/process-document",
            files=files
        )

        # Check response status
        if response.status_code == 200:
            # Process successful
            duration = time.time() - start_time
            print(f"\n✅ Upload successful! Processed in {duration:.2f} seconds")

            # Parse JSON response
            result = response.json()

            # Print a nice summary
            print("\n📄 PDF Processing Summary:")
            if result.get('success', False):
                processed_documents = result.get('documents', [])
                failed_documents = result.get('failed', [])

                print(f"Successfully processed: {len(processed_documents)} documents")
                print("Document IDs:")
                for doc in processed_documents:
                    print(f"  - {doc['document_id']} ({doc['filename']})")

                if failed_documents:
                    print(f"\nFailed documents: {len(failed_documents)}")
                    for failed in failed_documents:
                        print(f"  - {failed['filename']}: {failed['reason']}")
            else:
                print("❌ Upload processing reported issues.")

            # Save the full response to a file for inspection
            output_dir = os.path.dirname(os.path.abspath(__file__))
            output_file = os.path.join(output_dir, f"upload_result_{int(time.time())}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)

            print(f"\nFull response saved to {output_file}")

            # Return document IDs for use in search test
            if result.get('success', False):
                return [doc['document_id'] for doc in processed_documents]
            return []

        else:
            # Handle error
            print(f"\n❌ Upload failed with status code: {response.status_code}")
            print("Response content:")
            pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
            return []

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection error: Could not connect to {base_url}")
        print("Make sure your Flask app is running and accessible")
        return []
    except Exception as e:
        print(f"\n❌ Error during upload: {str(e)}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test PDF upload to Flask application')
    parser.add_argument('pdf_paths', nargs='+', help='Paths to PDF files for upload testing')
    args = parser.parse_args()

    # Run the test
    document_ids = test_pdf_upload(args.pdf_paths)

    if document_ids:
        print("\n🔍 Next step: Test vectorized search using these document IDs")
        print(f"For individual document search:")
        for doc_id in document_ids:
            print(f"  Run: python -m flask.tests.test_search \"{doc_id}\"")

        print("\nFor testing all documents:")
        print(f"  Run: python -m flask.tests.test_full_pipeline {' '.join(args.pdf_paths)}")
    else:
        print("\n❌ No document IDs returned, upload failed or no documents were processed successfully")

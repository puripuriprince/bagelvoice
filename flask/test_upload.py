#!/usr/bin/env python3
"""
Test script for uploading a PDF to the Flask application.
Usage: python test_upload.py path/to/your/document.pdf
"""

import argparse
import os
import sys
import requests
import json
from pprint import pprint
from pathlib import Path
import time

def test_pdf_upload(pdf_path):
    """Test uploading a PDF to the Flask app"""
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} does not exist")
        return False

    # Check if the file is a PDF
    if not pdf_path.lower().endswith('.pdf'):
        print(f"Error: File {pdf_path} is not a PDF")
        return False

    print(f"Testing PDF upload with file: {pdf_path}")

    # Get file size for progress reporting
    file_size = os.path.getsize(pdf_path)
    print(f"File size: {file_size/1024/1024:.2f} MB")

    # Prepare the file for upload
    print("Preparing upload...")
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}

        try:
            # Flask app base URL
            base_url = 'http://localhost:5000'

            # Send request to /process-pdf endpoint
            print(f"Sending request to {base_url}/process-pdf...")
            start_time = time.time()

            response = requests.post(
                f"{base_url}/process-pdf",
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
                print(f"Document ID: {result.get('document_id', 'N/A')}")

                # File paths
                print("\nFile Paths:")
                file_paths = result.get('file_paths', {})
                for key, path in file_paths.items():
                    print(f"  - {key}: {path}")

                # Text preview
                if 'text_preview' in result:
                    preview_text = result['text_preview']
                    print(f"\nExtracted Text Preview ({len(preview_text)} chars):")
                    print("-" * 80)
                    print(preview_text[:300] + "..." if len(preview_text) > 300 else preview_text)
                    print("-" * 80)

                # Save the full response to a file for inspection
                output_file = f"upload_result_{int(time.time())}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)

                print(f"\nFull response saved to {output_file}")

                # Return document ID for use in search test
                return result.get('document_id')

            else:
                # Handle error
                print(f"\n❌ Upload failed with status code: {response.status_code}")
                print("Response content:")
                pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
                return False

        except requests.exceptions.ConnectionError:
            print(f"\n❌ Connection error: Could not connect to {base_url}")
            print("Make sure your Flask app is running and accessible")
            return False
        except Exception as e:
            print(f"\n❌ Error during upload: {str(e)}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test PDF upload to Flask application')
    parser.add_argument('pdf_path', help='Path to PDF file for upload testing')
    args = parser.parse_args()

    # Run the test
    document_id = test_pdf_upload(args.pdf_path)

    if document_id:
        print("\n🔍 Next step: Test vectorized search using this document ID")
        print(f"Run: python test_search.py \"{document_id}\"")

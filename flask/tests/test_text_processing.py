#!/usr/bin/env python3
"""
Test the text processing endpoint by sending raw text for vectorization.
Usage: python test_text_processing.py path/to/text/file.txt [--title "Custom Title"]

This will read the text file and send its contents to the API for processing.
"""

import argparse
import os
import sys
import requests
import json
import time
import uuid
from pprint import pprint

def test_text_processing(text_path, title=None, session_id=None):
    """Test the text processing endpoint with a text file"""
    print("=" * 80)
    print(f"🔤 TESTING TEXT PROCESSING API")
    print("=" * 80)

    # Check if file exists
    if not os.path.exists(text_path):
        print(f"Error: File {text_path} does not exist")
        return False

    # Read the text file
    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

    # Get title from filename if not provided
    if not title:
        basename = os.path.basename(text_path)
        title = os.path.splitext(basename)[0].replace("_", " ").title()

    # Create session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    print(f"File: {text_path}")
    print(f"Title: {title}")
    print(f"Text length: {len(text_content)} characters")
    print(f"Session ID: {session_id}")

    # Flask app base URL
    base_url = 'http://localhost:5000'

    # Prepare the payload
    payload = {
        "text": text_content,
        "title": title,
        "session_id": session_id
    }

    # Send the request
    try:
        print(f"\nSending request to {base_url}/api/process-text...")
        start_time = time.time()

        response = requests.post(
            f"{base_url}/api/process-text",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        processing_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            document_id = result.get('document_id')
            success = result.get('success', False)

            print(f"✅ Text processing successful! Completed in {processing_time:.2f} seconds")
            print(f"Document ID: {document_id}")

            if success:
                print(f"✅ Text was added to vector store successfully")
            else:
                print(f"⚠️ Text processing reported issues")

            # Save processing results
            with open("text_processing_result.json", 'w') as f:
                output = {
                    "input_file": text_path,
                    "title": title,
                    "session_id": session_id,
                    "document_id": document_id,
                    "processing_time": processing_time,
                    "success": success,
                    "api_response": result,
                    "timestamp": time.time()
                }
                json.dump(output, f, indent=2)

            print(f"\nProcessing results saved to text_processing_result.json")

            # Test search with the new document
            print("\nWaiting 3 seconds before testing search...")
            time.sleep(3)

            print("\n🔍 Testing search with the new document...")
            search_payload = {
                "query": "main topic",
                "document_id": document_id,
                "session_id": session_id
            }

            search_response = requests.post(
                f"{base_url}/api/v1/search",
                json=search_payload,
                headers={'Content-Type': 'application/json'}
            )

            if search_response.status_code == 200:
                search_result = search_response.json()
                result_count = len(search_result.get('results', []))
                print(f"✅ Search successful! Found {result_count} results")

                if result_count > 0:
                    print("\nFirst search result preview:")
                    content = search_result['results'][0].get('content', '')
                    print(content[:200] + "..." if len(content) > 200 else content)
            else:
                print(f"❌ Search test failed with status code: {search_response.status_code}")

            return document_id

        else:
            print(f"❌ Text processing failed with status code: {response.status_code}")
            print("Response content:")
            pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
            return False

    except Exception as e:
        print(f"❌ Error during text processing: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test text processing API')
    parser.add_argument('text_path', help='Path to text file to process')
    parser.add_argument('--title', '-t', help='Custom title for the document')
    parser.add_argument('--session', '-s', help='Session ID (optional)')
    args = parser.parse_args()

    # Run the test
    test_text_processing(args.text_path, args.title, args.session)

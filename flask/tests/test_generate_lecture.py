#!/usr/bin/env python3
"""
Test the lecture generation API by creating a lecture from documents.
Usage: python test_generate_lecture.py [--session_id SESSION_ID] [--document_ids DOC_ID1,DOC_ID2,...] [--title "Your Lecture Title"] [--style academic|conversational|concise|narrative]
"""

import argparse
import os
import sys
import requests
import json
from pprint import pprint
import time
import uuid

def test_generate_lecture(session_id=None, document_ids=None, title=None, style=None):
    """Test the lecture generation from documents"""
    print("=" * 80)
    print(f"🎓 GENERATING LECTURE FROM DOCUMENTS")
    print("=" * 80)

    # Create a default title if not provided
    if not title:
        title = f"Generated Lecture ({time.strftime('%Y-%m-%d')})"

    # Flask app base URL
    base_url = 'http://localhost:5000'

    # Construct payload
    payload = {
        "title": title
    }

    # Add session_id if provided
    if session_id:
        payload["session_id"] = session_id

    # Add document_ids if provided
    if document_ids:
        payload["document_ids"] = document_ids.split(',') if isinstance(document_ids, str) else document_ids

    # Add style if provided
    if style:
        payload["style"] = style

    print(f"\n📝 REQUEST DETAILS:")
    print("-" * 80)
    if session_id:
        print(f"Session ID: {session_id}")
    if document_ids:
        print(f"Document IDs: {document_ids}")
    print(f"Title: {title}")
    if style:
        print(f"Style: {style}")

    # Send request to generate lecture
    try:
        print(f"\nSending request to {base_url}/api/generate-lecture...")
        start_time = time.time()

        response = requests.post(
            f"{base_url}/api/generate-lecture",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            lecture_id = result.get('lecture_id')
            lecture_content = result.get('content')

            print(f"\n✅ Lecture generated successfully in {duration:.2f} seconds!")
            print(f"Lecture ID: {lecture_id}")
            print(f"Title: {result.get('title')}")
            print(f"Source documents: {result.get('source_documents')}")
            print(f"File path: {result.get('file_path')}")

            # Save the result to a file
            output_file = f"lecture_result_{int(time.time())}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"\nFull result saved to {output_file}")

            # Preview of the lecture
            print("\n📝 LECTURE PREVIEW:")
            print("-" * 80)
            preview_length = min(500, len(lecture_content))
            print(lecture_content[:preview_length] + "...")
            print("-" * 80)
            print(f"Full lecture length: {len(lecture_content)} characters")

            return lecture_id

        else:
            print(f"\n❌ Request failed with status code: {response.status_code}")
            print("Response content:")
            pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
            return False

    except Exception as e:
        print(f"\n❌ Error during lecture generation: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a lecture from documents')
    parser.add_argument('--session_id', help='Optional: Session ID containing the documents')
    parser.add_argument('--document_ids', help='Optional: Comma-separated list of document IDs to include')
    parser.add_argument('--title', help='Title for the generated lecture')
    parser.add_argument('--style', choices=['academic', 'conversational', 'concise', 'narrative'],
                       help='Style of the lecture')

    args = parser.parse_args()

    # Generate the lecture
    lecture_id = test_generate_lecture(args.session_id, args.document_ids, args.title, args.style)

    if lecture_id:
        print("\n🔍 TO SEARCH THIS LECTURE:")
        print(f"python flask/test_search.py {lecture_id}")

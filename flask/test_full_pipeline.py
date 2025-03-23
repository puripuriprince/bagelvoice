#!/usr/bin/env python3
"""
Test the full pipeline: uploading a PDF and then testing vectorized search.
Usage: python test_full_pipeline.py path/to/your/document.pdf
"""

import argparse
import os
import sys
import requests
import json
from pprint import pprint
import time
import uuid

def test_full_pipeline(pdf_path):
    """Test the full pipeline from PDF upload to vectorized search"""
    print("=" * 80)
    print(f"🧪 TESTING FULL PIPELINE: PDF UPLOAD → VECTORIZED SEARCH")
    print("=" * 80)

    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} does not exist")
        return False

    # Check if the file is a PDF
    if not pdf_path.lower().endswith('.pdf'):
        print(f"Error: File {pdf_path} is not a PDF")
        return False

    # Flask app base URL
    base_url = 'http://localhost:5000'

    # Step 1: Upload PDF
    print("\n📤 STEP 1: UPLOADING PDF")
    print("-" * 80)
    print(f"File: {pdf_path}")

    document_id = None
    with open(pdf_path, 'rb') as f:
        try:
            print(f"Sending request to {base_url}/api/process-document...")
            upload_start = time.time()

            # Create a session ID if not provided
            session_id = str(uuid.uuid4())

            # Use form data with session_id and file
            response = requests.post(
                f"{base_url}/api/process-document",
                files={'file': (os.path.basename(pdf_path), f, 'application/pdf')},
                data={'session_id': session_id}
            )

            upload_duration = time.time() - upload_start

            if response.status_code == 200:
                result = response.json()
                document_id = result.get('document_id')
                success = result.get('success', False)

                print(f"✅ Upload successful! Processed in {upload_duration:.2f} seconds")
                print(f"Document ID: {document_id}")

                if success:
                    print(f"✅ Document was processed and added to vector store successfully!")
                    print(f"Session ID: {session_id}")
                else:
                    print(f"⚠️ Document processing reported issues. Check server logs for errors.")

                # Save brief upload stats
                with open("upload_stats.json", 'w') as f:
                    json.dump({
                        "file": pdf_path,
                        "document_id": document_id,
                        "session_id": session_id,
                        "upload_time": upload_duration,
                        "success": success,
                        "timestamp": time.time()
                    }, f, indent=2)

            else:
                print(f"❌ Upload failed with status code: {response.status_code}")
                print("Response content:")
                pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
                return False

        except Exception as e:
            print(f"❌ Error during upload: {str(e)}")
            return False

    # Add a longer delay to allow backend processing to complete
    wait_time = 25  # Increased to 15 seconds for Gemini processing
    print(f"\nWaiting {wait_time} seconds for Gemini processing to complete...")
    time.sleep(wait_time)

    # Step 2: Test search
    if document_id:
        print("\n🔍 STEP 2: TESTING VECTORIZED SEARCH")
        print("-" * 80)

        # Generate search queries based on the filename
        filename = os.path.basename(pdf_path)
        base_filename = os.path.splitext(filename)[0].replace("_", " ")

        # Create some generic queries based on filename
        words = base_filename.split()
        queries = [
            base_filename,  # Full filename as query
            " ".join(words[:2]) if len(words) > 1 else base_filename,  # First two words
            words[0] if words else base_filename  # Just the first word
        ]

        # Add some generic queries
        generic_queries = [
            "main topic",
            "important concepts",
            "key findings"
        ]

        all_queries = queries + generic_queries

        # Run searches for each query
        print(f"Running {len(all_queries)} search queries...")

        search_results = []
        for i, query in enumerate(all_queries):
            print(f"\nQuery {i+1}/{len(all_queries)}: \"{query}\"")

            payload = {
                'query': query,
                'document_id': document_id,
                'session_id': session_id
            }

            try:
                # Try both possible endpoints
                endpoints = [f"{base_url}/api/v1/search", f"{base_url}/api/search"]

                for endpoint in endpoints:
                    try:
                        print(f"Trying endpoint: {endpoint}")
                        search_start = time.time()

                        response = requests.post(
                            endpoint,
                            json=payload,
                            headers={'Content-Type': 'application/json'}
                        )

                        search_duration = time.time() - search_start

                        if response.status_code == 200:
                            result = response.json()
                            result_count = len(result.get('results', []))

                            print(f"✅ Search successful! Found {result_count} results in {search_duration:.2f} seconds")

                            # Save result summary
                            search_results.append({
                                "query": query,
                                "result_count": result_count,
                                "search_time": search_duration,
                                "endpoint": endpoint
                            })

                            # Only show first result preview
                            if result_count > 0:
                                first_result = result['results'][0]
                                content = first_result.get('content', '')
                                print(f"First result preview ({len(content)} chars):")
                                print(content[:150] + "..." if len(content) > 150 else content)

                            # Break the endpoint loop on success
                            break

                        elif response.status_code == 404:
                            # Endpoint not found, try the next one
                            print(f"Endpoint not available (404)")
                            continue
                        else:
                            print(f"❌ Search failed with status code: {response.status_code}")
                            # Try the next endpoint
                            continue

                    except requests.exceptions.ConnectionError:
                        print(f"❌ Connection error with endpoint {endpoint}")
                        continue

                # Check if any endpoint succeeded
                if not any(r['query'] == query for r in search_results):
                    print("❌ All search endpoints failed")

            except Exception as e:
                print(f"❌ Error during search: {str(e)}")
                continue

        # Print search summary
        print("\n📊 SEARCH SUMMARY")
        print("-" * 80)
        print(f"Total queries: {len(all_queries)}")
        print(f"Successful queries: {len(search_results)}")

        if search_results:
            # Calculate average result count and search time
            avg_results = sum(r['result_count'] for r in search_results) / len(search_results)
            avg_time = sum(r['search_time'] for r in search_results) / len(search_results)

            print(f"Average results per query: {avg_results:.2f}")
            print(f"Average search time: {avg_time:.2f} seconds")

            # Save search stats
            with open("search_stats.json", 'w') as f:
                json.dump({
                    "document_id": document_id,
                    "queries": search_results,
                    "avg_results": avg_results,
                    "avg_search_time": avg_time,
                    "timestamp": time.time()
                }, f, indent=2)

            print("\n✅ Full pipeline test completed successfully")
            print(f"Upload and search statistics saved to upload_stats.json and search_stats.json")
            return True
        else:
            print("❌ No successful search queries")
            return False
    else:
        print("❌ Document ID not available, cannot proceed with search testing")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test full PDF processing and search pipeline')
    parser.add_argument('pdf_path', help='Path to PDF file for testing')
    args = parser.parse_args()

    # Run the test
    test_full_pipeline(args.pdf_path)

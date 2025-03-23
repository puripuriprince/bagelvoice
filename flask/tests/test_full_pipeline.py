#!/usr/bin/env python3
"""
Test the full pipeline: uploading PDFs and then testing vectorized search.
Usage: python -m flask.tests.test_full_pipeline path/to/your/document1.pdf [path/to/your/document2.pdf ...]
"""

import argparse
import os
import sys
import requests
import json
from pprint import pprint
import time
import uuid

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_full_pipeline(pdf_paths):
    """Test the full pipeline from PDF upload to vectorized search"""
    print("=" * 80)
    print(f"🧪 TESTING FULL PIPELINE: PDF UPLOAD → VECTORIZED SEARCH")
    print("=" * 80)

    # Check if files exist and are PDFs
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"Error: File {pdf_path} does not exist")
            return False

        if not pdf_path.lower().endswith('.pdf'):
            print(f"Error: File {pdf_path} is not a PDF")
            return False

    # Flask app base URL
    base_url = 'http://localhost:5000'

    # Step 1: Upload PDFs
    print(f"\n📤 STEP 1: UPLOADING {len(pdf_paths)} PDFs")
    print("-" * 80)
    for pdf_path in pdf_paths:
        print(f"File: {pdf_path}")

    document_ids = []
    try:
        print(f"Sending request to {base_url}/api/process-document...")
        upload_start = time.time()

        # Create a session ID if not provided
        session_id = str(uuid.uuid4())

        # Prepare the files for upload
        files = []
        for pdf_path in pdf_paths:
            with open(pdf_path, 'rb') as f:
                files.append(('files[]', (os.path.basename(pdf_path), f.read(), 'application/pdf')))

        # Prepare form data
        data = {'session_id': session_id}

        # Send request with multiple files
        response = requests.post(
            f"{base_url}/api/process-document",
            files=files,
            data=data
        )

        upload_duration = time.time() - upload_start

        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            processed_documents = result.get('documents', [])
            document_ids = [doc['document_id'] for doc in processed_documents]
            failed_documents = result.get('failed', [])

            print(f"✅ Upload successful! Processed in {upload_duration:.2f} seconds")

            if success:
                print(f"✅ Processed {len(processed_documents)} documents successfully!")
                print(f"Document IDs: {', '.join(document_ids)}")
                print(f"Session ID: {session_id}")

                if failed_documents:
                    print(f"⚠️ {len(failed_documents)} documents failed processing:")
                    for failed in failed_documents:
                        print(f"  - {failed['filename']}: {failed['reason']}")
            else:
                print(f"⚠️ Document processing reported issues. Check server logs for errors.")

            # Save brief upload stats
            output_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(output_dir, "upload_stats.json"), 'w') as f:
                json.dump({
                    "files": pdf_paths,
                    "document_ids": document_ids,
                    "session_id": session_id,
                    "upload_time": upload_duration,
                    "success": success,
                    "timestamp": time.time(),
                    "processed": len(processed_documents),
                    "failed": len(failed_documents)
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
    wait_time = 25
    print(f"\nWaiting {wait_time} seconds for backend processing to complete...")
    time.sleep(wait_time)

    # Step 2: Test search on each document
    if document_ids:
        print("\n🔍 STEP 2: TESTING VECTORIZED SEARCH")
        print("-" * 80)

        # Generic queries for all documents
        generic_queries = [
            "main topic",
            "important concepts",
            "key findings"
        ]

        # Run searches for each document
        all_search_results = []

        for document_id in document_ids:
            print(f"\nTesting search for document ID: {document_id}")

            # Create document-specific queries based on document ID
            doc_specific_queries = [
                f"key points in document {document_id}",
                f"summary of {document_id}"
            ]

            all_queries = generic_queries + doc_specific_queries

            # Run searches for each query
            document_results = []

            for query in all_queries:
                print(f"  Query: \"{query}\"")

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

                                print(f"    ✅ Found {result_count} results in {search_duration:.2f} seconds")

                                # Save result summary
                                search_result = {
                                    "document_id": document_id,
                                    "query": query,
                                    "result_count": result_count,
                                    "search_time": search_duration,
                                    "endpoint": endpoint
                                }

                                document_results.append(search_result)

                                # Break the endpoint loop on success
                                break

                            elif response.status_code == 404:
                                # Endpoint not found, try the next one
                                continue
                            else:
                                print(f"    ❌ Search failed with status code: {response.status_code}")
                                # Try the next endpoint
                                continue

                        except requests.exceptions.ConnectionError:
                            print(f"    ❌ Connection error with endpoint {endpoint}")
                            continue

                except Exception as e:
                    print(f"    ❌ Error during search: {str(e)}")
                    continue

            # Add document results to all results
            all_search_results.extend(document_results)

        # Print search summary
        print("\n📊 SEARCH SUMMARY")
        print("-" * 80)
        print(f"Total documents: {len(document_ids)}")
        print(f"Total queries: {len(all_search_results)}")

        # Group results by document ID
        results_by_document = {}
        for result in all_search_results:
            doc_id = result['document_id']
            if doc_id not in results_by_document:
                results_by_document[doc_id] = []
            results_by_document[doc_id].append(result)

        # Print summary for each document
        for doc_id, results in results_by_document.items():
            if results:
                avg_results = sum(r['result_count'] for r in results) / len(results)
                avg_time = sum(r['search_time'] for r in results) / len(results)

                print(f"\nDocument {doc_id}:")
                print(f"  Queries: {len(results)}")
                print(f"  Average results per query: {avg_results:.2f}")
                print(f"  Average search time: {avg_time:.2f} seconds")

        # Save search stats
        if all_search_results:
            output_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(output_dir, "search_stats.json"), 'w') as f:
                json.dump({
                    "document_ids": document_ids,
                    "session_id": session_id,
                    "queries": all_search_results,
                    "results_by_document": {doc_id: len(results) for doc_id, results in results_by_document.items()},
                    "timestamp": time.time()
                }, f, indent=2)

            print("\n✅ Full pipeline test completed successfully")
            print(f"Upload and search statistics saved to upload_stats.json and search_stats.json")
            return True
        else:
            print("❌ No successful search queries")
            return False
    else:
        print("❌ No document IDs available, cannot proceed with search testing")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test full PDF processing and search pipeline')
    parser.add_argument('pdf_paths', nargs='+', help='Paths to PDF files for testing')
    args = parser.parse_args()

    # Run the test
    test_full_pipeline(args.pdf_paths)

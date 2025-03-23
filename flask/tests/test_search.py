#!/usr/bin/env python3
"""
Test search functionality with a specific document ID.
Usage: python -m flask.tests.test_search document_id [--query "your query"] [--session your_session_id]
"""

import argparse
import os
import sys
import requests
import json
from pprint import pprint
import time

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_search(document_id, query=None, session_id=None):
    """Test search functionality with a specific document ID"""
    print("=" * 80)
    print(f"🔍 TESTING SEARCH FOR DOCUMENT: {document_id}")
    print("=" * 80)

    # Flask app base URL
    base_url = 'http://localhost:5000'

    # Use default queries if none provided
    if not query:
        queries = [
            "main topic",
            "important concepts",
            "key findings",
            "introduction",
            "summary",
            "definition",
            "methodology",
            "conclusion"
        ]
    else:
        queries = [query]

    print(f"Running {len(queries)} search queries...")

    search_results = []
    for i, query in enumerate(queries):
        print(f"\nQuery {i+1}/{len(queries)}: \"{query}\"")

        payload = {
            'query': query,
            'document_id': document_id
        }

        # Add session_id to payload if provided
        if session_id:
            payload['session_id'] = session_id
            print(f"Using session ID: {session_id}")

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

                        # Show results
                        if result_count > 0:
                            print("\nSearch Results:")
                            print("-" * 40)

                            for idx, res in enumerate(result.get('results', [])):
                                content = res.get('content', '')
                                similarity = res.get('similarity', 0)
                                print(f"Result {idx+1} (Similarity: {similarity:.4f}):")
                                print(f"{content[:200]}..." if len(content) > 200 else content)
                                print("-" * 40)
                        else:
                            print("No results found.")

                        # Break the endpoint loop on success
                        break

                    elif response.status_code == 404:
                        # Endpoint not found, try the next one
                        print(f"Endpoint not available (404)")
                        continue
                    else:
                        print(f"❌ Search failed with status code: {response.status_code}")
                        print("Response content:")
                        pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
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
    print(f"Total queries: {len(queries)}")
    print(f"Successful queries: {len(search_results)}")

    if search_results:
        # Calculate average result count and search time
        avg_results = sum(r['result_count'] for r in search_results) / len(search_results)
        avg_time = sum(r['search_time'] for r in search_results) / len(search_results)

        print(f"Average results per query: {avg_results:.2f}")
        print(f"Average search time: {avg_time:.2f} seconds")

        # Save search stats
        output_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(output_dir, f"search_stats_{document_id}_{int(time.time())}.json"), 'w') as f:
            json.dump({
                "document_id": document_id,
                "queries": search_results,
                "avg_results": avg_results,
                "avg_search_time": avg_time,
                "timestamp": time.time()
            }, f, indent=2)

        print("\n✅ Search test completed successfully")
        print(f"Search statistics saved to search_stats_{document_id}_{int(time.time())}.json")
        return True
    else:
        print("❌ No successful search queries")
        return False

def test_multiple_documents(document_ids, query=None, session_id=None):
    """Test search across multiple documents"""
    print("=" * 80)
    print(f"🔍 TESTING SEARCH ACROSS MULTIPLE DOCUMENTS")
    print("=" * 80)

    success_count = 0
    total_documents = len(document_ids)

    print(f"Testing search for {total_documents} documents:")
    for doc_id in document_ids:
        print(f"- {doc_id}")

    for doc_id in document_ids:
        print("\n" + "=" * 60)
        print(f"Document ID: {doc_id}")
        print("=" * 60)

        result = test_search(doc_id, query, session_id)
        if result:
            success_count += 1

    print("\n" + "=" * 80)
    print(f"OVERALL RESULTS: {success_count}/{total_documents} document searches successful")
    print("=" * 80)

    return success_count == total_documents

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test search with document IDs')
    parser.add_argument('document_ids', help='Document ID(s) to search in (comma-separated for multiple)')
    parser.add_argument('--query', '-q', help='Specific query to search for (optional)')
    parser.add_argument('--session', '-s', help='Session ID (optional)')
    args = parser.parse_args()

    # Process document IDs (support comma-separated format)
    document_id_list = [doc_id.strip() for doc_id in args.document_ids.split(',')]

    # Run tests based on number of document IDs
    if len(document_id_list) == 1:
        test_search(document_id_list[0], args.query, args.session)
    else:
        test_multiple_documents(document_id_list, args.query, args.session)

#!/usr/bin/env python3
"""
Test script for testing vectorized search in the Flask application.
Usage: python test_search.py [document_id]
"""

import argparse
import sys
import requests
import json
from pprint import pprint
import time

def test_vectorized_search(query, document_id=None):
    """Test the vectorized search functionality"""
    # Flask app base URL
    base_url = 'http://localhost:5000'

    print(f"Testing vectorized search with query: \"{query}\"")
    if document_id:
        print(f"Filtering to document ID: {document_id}")

    # Prepare the request payload
    payload = {
        'query': query
    }

    if document_id:
        payload['document_id'] = document_id

    try:
        # First try the newer v1 endpoint
        search_url = f"{base_url}/api/v1/search"
        print(f"Sending request to {search_url}...")
        start_time = time.time()

        response = requests.post(
            search_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        # If that fails, try the fallback endpoint
        if response.status_code != 200:
            print(f"Endpoint {search_url} not available (status {response.status_code})")
            print("Trying fallback endpoint...")

            search_url = f"{base_url}/api/search"
            response = requests.post(
                search_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )

        # Check response status
        if response.status_code == 200:
            # Process successful
            duration = time.time() - start_time
            print(f"\n✅ Search successful! Completed in {duration:.2f} seconds")

            # Parse JSON response
            result = response.json()

            # Print number of results
            results = result.get('results', [])
            count = len(results)
            print(f"\nFound {count} results for query: \"{query}\"")

            # Print results
            if count > 0:
                print("\n🔎 Search Results:")
                for i, item in enumerate(results):
                    print(f"\n--- Result {i+1} ---")
                    print(f"Document: {item.get('document_id', 'N/A')}")
                    print(f"Title: {item.get('title', 'N/A')}")
                    print(f"Similarity: {item.get('similarity', 'N/A')}")

                    # Content preview
                    content = item.get('content', '')
                    print(f"Content Preview ({len(content)} chars):")
                    print("-" * 80)
                    print(content[:300] + "..." if len(content) > 300 else content)
                    print("-" * 80)

            # If no results, suggest improvements
            else:
                print("\n⚠️ No results found. Consider:")
                print("1. Checking if documents were properly processed")
                print("2. Using different search terms")
                print("3. Verifying that the vector store is working")

            # Save the full response to a file
            output_file = f"search_result_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)

            print(f"\nFull response saved to {output_file}")
            return True

        else:
            # Handle error
            print(f"\n❌ Search failed with status code: {response.status_code}")
            print("Response content:")
            pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)

            # Check for common error conditions
            if response.status_code == 404:
                print("\nError: Endpoint not found. Make sure your Flask app has the search endpoint configured.")
            elif response.status_code == 500:
                print("\nError: Server error. This might be related to your vector store configuration.")
                print("Check your Flask app logs for more details.")

            return False

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection error: Could not connect to {base_url}")
        print("Make sure your Flask app is running and accessible")
        return False
    except Exception as e:
        print(f"\n❌ Error during search: {str(e)}")
        return False

def run_interactive_search(document_id=None):
    """Run interactive search queries"""
    print("\n🔍 Interactive Search Mode")
    print("Type 'exit' or 'quit' to end the session")

    while True:
        query = input("\nEnter search query: ")
        if query.lower() in ('exit', 'quit', 'q'):
            print("Exiting search mode")
            break

        if not query:
            print("Please enter a valid query")
            continue

        test_vectorized_search(query, document_id)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test vectorized search in Flask application')
    parser.add_argument('document_id', nargs='?', help='Optional document ID to filter results')
    parser.add_argument('--query', '-q', help='Search query (if not provided, runs in interactive mode)')
    args = parser.parse_args()

    if args.query:
        # Run single search with provided query
        test_vectorized_search(args.query, args.document_id)
    else:
        # Run interactive search mode
        run_interactive_search(args.document_id)

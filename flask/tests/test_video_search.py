#!/usr/bin/env python3
"""
Test the video search API by generating a video based on search results.
Usage: python -m flask.tests.test_video_search [--query "Your search query"] [--document_id DOC_ID] [--session_id SESSION_ID]
"""

import argparse
import os
import sys
import requests
import json
from pprint import pprint
import time
import webbrowser
import uuid

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_video_search(query=None, document_id=None, session_id=None):
    """Test the video search functionality"""
    print("=" * 80)
    print(f"🎬 TESTING VIDEO SEARCH")
    print("=" * 80)

    # Create a default query if not provided
    if not query:
        query = "main concepts and key points"

    # Flask app base URL
    base_url = 'http://localhost:5000'

    # Construct payload
    payload = {
        "query": query
    }

    # Add document_id if provided
    if document_id:
        payload["document_id"] = document_id

    # Add session_id if provided
    if session_id:
        payload["session_id"] = session_id

    print(f"\n📝 REQUEST DETAILS:")
    print("-" * 80)
    print(f"Query: {query}")
    if document_id:
        print(f"Document ID: {document_id}")
    if session_id:
        print(f"Session ID: {session_id}")

    # Send request to generate video
    try:
        print(f"\nSending request to {base_url}/api/video-search...")
        start_time = time.time()

        response = requests.post(
            f"{base_url}/api/video-search",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            video_url = result.get('video_url')

            print(f"\n✅ Video generated successfully in {duration:.2f} seconds!")
            print(f"Video URL: {base_url}{video_url}")

            # Save the result to a file
            output_dir = os.path.dirname(os.path.abspath(__file__))
            output_file = os.path.join(output_dir, f"video_search_result_{int(time.time())}.json")
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"\nFull result saved to {output_file}")

            # Ask to open the video
            open_browser = input("\nOpen video in browser? (y/n): ").lower().strip() == 'y'
            if open_browser:
                full_url = f"{base_url}{video_url}"
                print(f"Opening {full_url} in browser...")
                webbrowser.open(full_url)

            return video_url

        else:
            print(f"\n❌ Request failed with status code: {response.status_code}")
            print("Response content:")
            pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
            return False

    except Exception as e:
        print(f"\n❌ Error during video search: {str(e)}")
        return False

def test_list_videos():
    """Test listing all videos"""
    print("\n" + "=" * 80)
    print(f"📋 LISTING ALL VIDEOS")
    print("=" * 80)

    # Flask app base URL
    base_url = 'http://localhost:5000'

    try:
        print(f"Sending request to {base_url}/api/videos...")

        response = requests.get(
            f"{base_url}/api/videos",
            params={'limit': 5}
        )

        if response.status_code == 200:
            result = response.json()
            videos = result.get('videos', [])

            print(f"\n✅ Found {len(videos)} videos")

            if videos:
                print("\nRecent videos:")
                for i, video in enumerate(videos):
                    print(f"{i+1}. {video.get('title')} (ID: {video.get('video_id')})")
                    print(f"   Query: {video.get('query')}")
                    print(f"   Created: {video.get('created_at')}")
                    print()

            return True

        else:
            print(f"\n❌ Request failed with status code: {response.status_code}")
            print("Response content:")
            pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
            return False

    except Exception as e:
        print(f"\n❌ Error listing videos: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test video search functionality')
    parser.add_argument('--query', help='Search query for video generation')
    parser.add_argument('--document_id', help='Optional document ID to filter search')
    parser.add_argument('--session_id', help='Optional session ID to filter search')

    args = parser.parse_args()

    # Run the video search test
    video_url = test_video_search(args.query, args.document_id, args.session_id)

    # If successful, also test listing videos
    if video_url:
        test_list_videos()

#!/usr/bin/env python3
"""
Test video generation using Manim.
Usage: python -m flask.tests.test_video_generation [--query "Your query"]
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

def test_video_generation(query=None):
    """Test video generation with a specific query"""
    print("=" * 80)
    print(f"🎬 TESTING VIDEO GENERATION")
    print("=" * 80)

    # Flask app base URL
    base_url = 'http://localhost:5000'

    # Use default query if none provided
    if not query:
        query = "Explain how artificial intelligence works with simple animations"

    print(f"Using query: \"{query}\"")

    # Prepare payload for the video generation request
    payload = {
        'query': query
    }

    try:
        # Send request to the video generation endpoint
        print(f"Sending request to {base_url}/api/generate-video...")
        start_time = time.time()

        response = requests.post(
            f"{base_url}/api/generate-video",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        # Check response status
        if response.status_code == 200:
            result = response.json()
            duration = time.time() - start_time
            print(f"\n✅ Video generation request successful! Processed in {duration:.2f} seconds")

            # Extract video URL
            video_url = result.get('video_url')
            video_id = None

            # Extract video ID from URL if available
            if video_url:
                video_id = video_url.split('/')[-1].split('.')[0]
                print(f"Video URL: {video_url}")
                print(f"Video ID: {video_id}")

            # Wait for video processing to complete
            if video_id:
                print("\nChecking video info...")

                # Try to get video info
                video_info_url = f"{base_url}/api/videos/{video_id}"
                video_info_response = requests.get(video_info_url)

                if video_info_response.status_code == 200:
                    video_info = video_info_response.json().get('video', {})
                    video_type = video_info.get('video_type', 'unknown')

                    print(f"Video type: {video_type}")
                    if video_type == 'manim':
                        print("✅ Successfully generated Manim video!")
                    elif video_type == 'placeholder':
                        print("⚠️ Generated placeholder HTML (Manim generation failed)")

                    # Save the video info to a file for inspection
                    output_dir = os.path.dirname(os.path.abspath(__file__))
                    output_file = os.path.join(output_dir, f"video_generation_result_{int(time.time())}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "query": query,
                            "video_url": video_url,
                            "video_id": video_id,
                            "video_info": video_info,
                            "generation_time": duration,
                            "timestamp": time.time()
                        }, f, indent=2)

                    print(f"\nFull result saved to {output_file}")
                    return video_url
                else:
                    print(f"❌ Failed to get video info: {video_info_response.status_code}")

            return video_url

        else:
            # Handle error
            print(f"\n❌ Video generation failed with status code: {response.status_code}")
            print("Response content:")
            pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
            return None

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection error: Could not connect to {base_url}")
        print("Make sure your Flask app is running and accessible")
        return None
    except Exception as e:
        print(f"\n❌ Error during video generation request: {str(e)}")
        return None

def test_list_videos():
    """Test the video listing endpoint"""
    print("\n" + "=" * 80)
    print("📋 TESTING VIDEO LISTING")
    print("=" * 80)

    # Flask app base URL
    base_url = 'http://localhost:5000'

    try:
        # Send request to the videos listing endpoint
        print(f"Sending request to {base_url}/api/videos...")

        response = requests.get(f"{base_url}/api/videos")

        # Check response status
        if response.status_code == 200:
            result = response.json()
            videos = result.get('videos', [])

            print(f"\n✅ Successfully retrieved {len(videos)} videos")

            if videos:
                print("\nMost recent videos:")
                for i, video in enumerate(videos[:3]):  # Show top 3
                    title = video.get('title', 'No title')
                    video_id = video.get('video_id', 'Unknown')
                    video_type = video.get('video_type', 'unknown')
                    created_at = video.get('created_at', 'Unknown')
                    print(f"{i+1}. {title} (ID: {video_id}, Type: {video_type}, Created: {created_at})")

            return videos
        else:
            print(f"\n❌ Video listing failed with status code: {response.status_code}")
            print("Response content:")
            pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
            return None

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection error: Could not connect to {base_url}")
        print("Make sure your Flask app is running and accessible")
        return None
    except Exception as e:
        print(f"\n❌ Error during video listing request: {str(e)}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test video generation')
    parser.add_argument('--query', '-q', help='Query to generate video for')
    args = parser.parse_args()

    # Run the tests
    video_url = test_video_generation(args.query)
    if video_url:
        print("\n🎬 Video generation test completed successfully")
        print(f"Video URL: {video_url}")

    # List available videos
    test_list_videos()

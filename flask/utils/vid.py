"""
Video generation utility for BagelVoice.
This module handles converting text content to video presentations using Manim.
"""

import os
import uuid
import json
import time
import subprocess
import traceback
import tempfile
import anthropic
import shutil
from datetime import datetime
from pathlib import Path

# Video generation settings
VIDEO_STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'static', 'generated', 'videos')
VIDEO_PUBLIC_PATH = '/static/generated/videos'
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')

# Create storage directories if they don't exist
os.makedirs(VIDEO_STORAGE_PATH, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize Anthropic client (Claude)
# Use environment variable ANTHROPIC_API_KEY
try:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        # Minimal initialization to avoid any unexpected arguments
        client = anthropic.Client(api_key=api_key)
        print("Anthropic client initialized successfully")
    else:
        print("No ANTHROPIC_API_KEY found in environment variables")
        client = None
except Exception as e:
    print(f"Error initializing Anthropic client: {e}")
    client = None

def generate_video(title, content, query=None, style="presentation"):
    """
    Generate a video presentation from text content using Manim.

    Args:
        title (str): Title of the video
        content (str): Text content to convert to video
        query (str, optional): The search query that triggered this generation
        style (str, optional): Style of video (presentation, tutorial, etc)

    Returns:
        str: URL of the generated video
    """
    print(f"Generating video with Manim for query: {query}")

    # Generate a unique ID for this video
    video_id = f"video_{uuid.uuid4().hex[:10]}"

    # Create a temporary directory for this specific video generation
    video_temp_dir = os.path.join(TEMP_DIR, video_id)
    os.makedirs(video_temp_dir, exist_ok=True)

    # Generate Manim code using Claude
    manim_code = generate_manim_code(query)

    if not manim_code:
        # If code generation failed, create a placeholder HTML
        return create_placeholder_video(video_id, title, content, query, style)

    # Save the generated Manim code to a file
    manim_file_path = os.path.join(video_temp_dir, "vid.py")
    with open(manim_file_path, "w") as f:
        f.write(manim_code)

    # Execute the Manim code to generate the video
    try:
        video_path = execute_manim_code(manim_file_path, video_temp_dir)

        if not video_path or not os.path.exists(video_path):
            print("Manim execution didn't produce a video file")
            return create_placeholder_video(video_id, title, content, query, style)

        # Copy the video to the permanent storage location
        final_video_path = os.path.join(VIDEO_STORAGE_PATH, f"{video_id}.mp4")
        shutil.copy2(video_path, final_video_path)

        # Save metadata
        metadata = {
            "video_id": video_id,
            "title": title,
            "query": query,
            "content_length": len(content),
            "style": style,
            "created_at": datetime.now().isoformat(),
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "video_type": "manim",
            "file_path": final_video_path
        }

        # Save metadata file
        metadata_path = os.path.join(VIDEO_STORAGE_PATH, f"{video_id}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        # Generate the public URL
        video_url = f"{VIDEO_PUBLIC_PATH}/{video_id}.mp4"
        print(f"Manim video generated: {video_url}")

        # Clean up the temporary directory
        shutil.rmtree(video_temp_dir, ignore_errors=True)

        return video_url

    except Exception as e:
        print(f"Error executing Manim code: {e}")
        traceback.print_exc()
        # If video generation fails, create a placeholder HTML
        return create_placeholder_video(video_id, title, content, query, style)

def generate_manim_code(query):
    """
    Generate Manim code using Claude for the given query.

    Args:
        query (str): The query to visualize with Manim

    Returns:
        str: Generated Manim Python code
    """
    try:
        # Check if client is available
        if client is None:
            print("Anthropic client not available")
            return None

        # Construct prompt for Claude
        prompt = f"""Generate code to make a manim video of 10 seconds, the filename is to be named vid.py and it has to: {query}

The code should:
1. Import the necessary Manim libraries
2. Create a scene class that visualizes the query
3. Keep the video to approximately 10 seconds
4. Include clear animations and visuals
5. Be complete and runnable with standard Manim installation
6. Use ManimCE syntax (the community edition)

Please only give me valid Python code that can be directly saved to a file and executed.
"""

        # Call Claude API to generate code (using older API version 0.18.1)
        response = client.completion(
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt} {anthropic.AI_PROMPT}",
            model="claude-2.0",
            max_tokens_to_sample=1500,
            temperature=0.2
        )

        # Extract the code from the response
        code = response.completion

        # Simple validation to make sure we have Python code
        if "class" in code and "def" in code and "import manim" in code:
            return code
        else:
            print("Claude didn't generate valid Manim code")
            return None

    except Exception as e:
        print(f"Error generating Manim code with Claude: {e}")
        traceback.print_exc()
        return None

def execute_manim_code(file_path, working_dir):
    """
    Execute the Manim code to generate a video.

    Args:
        file_path (str): Path to the Python file with Manim code
        working_dir (str): Directory to use as the working directory

    Returns:
        str: Path to the generated video file, or None if generation failed
    """
    try:
        # Get the filename without the path
        filename = os.path.basename(file_path)

        # Execute Manim command to generate the video
        # The -pql flag produces low quality but faster rendering
        # --media_dir specifies where to save the output
        cmd = ["manim", "-pql", file_path, "--media_dir", working_dir]

        # Run the command
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True
        )

        print(f"Manim execution stdout: {result.stdout}")

        if result.returncode != 0:
            print(f"Manim execution error: {result.stderr}")
            return None

        # Find the generated video file
        media_dir = os.path.join(working_dir, "media")
        videos_dir = os.path.join(media_dir, "videos")

        # Look for MP4 files in the videos directory
        for root, dirs, files in os.walk(videos_dir):
            for file in files:
                if file.endswith(".mp4"):
                    return os.path.join(root, file)

        return None

    except Exception as e:
        print(f"Error executing Manim code: {e}")
        traceback.print_exc()
        return None

def create_placeholder_video(video_id, title, content, query, style):
    """
    Create a placeholder HTML file when video generation fails.

    Args:
        video_id (str): Unique ID for the video
        title (str): Title of the video
        content (str): Text content for the video
        query (str): The search query
        style (str): Style of video

    Returns:
        str: URL of the placeholder HTML
    """
    print(f"Creating placeholder for video: {title}")

    # Prepare video metadata
    metadata = {
        "video_id": video_id,
        "title": title,
        "query": query,
        "content_length": len(content),
        "style": style,
        "created_at": datetime.now().isoformat(),
        "content_preview": content[:500] + "..." if len(content) > 500 else content,
        "video_type": "placeholder"
    }

    # Save metadata file
    metadata_path = os.path.join(VIDEO_STORAGE_PATH, f"{video_id}_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    # Create HTML file as video placeholder
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; }}
        .content {{ white-space: pre-wrap; background: #f8f9fa; padding: 15px; border-radius: 5px; }}
        .meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }}
        .error {{ color: #e74c3c; padding: 10px; background: #fadbd8; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="meta">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} • Query: "{query or 'None'}"
        </div>
        <div class="error">
            <strong>Note:</strong> Manim video generation was not successful. Showing content as HTML instead.
        </div>
        <h2>Content that would be in the video:</h2>
        <div class="content">
{content}
        </div>
    </div>
</body>
</html>
"""

    # Save the HTML file
    html_filename = f"{video_id}.html"
    html_path = os.path.join(VIDEO_STORAGE_PATH, html_filename)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Generate the public URL
    video_url = f"{VIDEO_PUBLIC_PATH}/{html_filename}"
    print(f"Placeholder HTML generated: {video_url}")

    return video_url

def get_video_info(video_id):
    """
    Get information about a generated video

    Args:
        video_id (str): The video ID

    Returns:
        dict: Video metadata or None if not found
    """
    metadata_path = os.path.join(VIDEO_STORAGE_PATH, f"{video_id}_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def list_videos(limit=10):
    """
    List recently generated videos

    Args:
        limit (int): Maximum number of videos to return

    Returns:
        list: List of video metadata objects
    """
    videos = []
    try:
        # Get all JSON files in the video directory
        metadata_files = [f for f in os.listdir(VIDEO_STORAGE_PATH) if f.endswith('_metadata.json')]

        # Sort by modification time (newest first)
        metadata_files.sort(key=lambda x: os.path.getmtime(os.path.join(VIDEO_STORAGE_PATH, x)), reverse=True)

        # Load metadata for each video
        for metadata_file in metadata_files[:limit]:
            with open(os.path.join(VIDEO_STORAGE_PATH, metadata_file), 'r', encoding='utf-8') as f:
                videos.append(json.load(f))

    except Exception as e:
        print(f"Error listing videos: {e}")
        traceback.print_exc()

    return videos

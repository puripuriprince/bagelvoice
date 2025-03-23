import base64
import datetime
import json
import os
import subprocess
import threading
import uuid

import dotenv
import PyPDF2
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from openai import OpenAI

# Load environment variables
dotenv.load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS to allow requests from any origin
CORS(app, resources={r"/*": {"origins": "*"}})

# Ensure directories exist
FILES_DIR = "files"
VIDEOS_DIR = "static/videos"
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)


# PDF parsing function
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text


# Speech-to-text function for audio files
def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
        )
    return transcription.text


# Generate summary function
def generate_summary(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or another appropriate model
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes documents concisely.",
            },
            {
                "role": "user",
                "content": f"Please summarize the following document in one paragraph (approx 300 words max), with only the meaningful info:\n\n{text[:10000]}",
            },  # Taking first 10K chars for API limits
        ],
    )
    return response.choices[0].message.content


# Check if a question requires a video explanation
def check_video_requirement(question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that determines if a question would benefit from a video explanation.",
            },
            {
                "role": "user",
                "content": f"Does the following question require or would significantly benefit from a video explanation? Answer with only 'yes' or 'no'.\n\nQuestion: {question}",
            },
        ],
    )
    answer = response.choices[0].message.content.strip().lower()
    return "yes" in answer


# Generate Manim code for video explanation
def generate_manim_code(question, answer):
    response = client.chat.completions.create(
        model="gpt-4o",  # Use a more capable model for code generation
        messages=[
            {
                "role": "system",
                "content": "You are a Python programming assistant specialized in creating Manim animations to explain concepts visually. Generate complete, self-contained Manim code that can be executed directly to produce an educational video.",
            },
            {
                "role": "user",
                "content": f"Create Manim code to generate a short educational video explaining the following question and answer. The code should be complete and ready to run. The animation should be visually engaging and clearly explain the concept.\n\nQuestion: {question}\n\nAnswer: {answer[:1000]}",
            },
        ],
    )
    return response.choices[0].message.content


# Function to render Manim video asynchronously
def render_manim_video(manim_code, video_path, video_filename):
    try:
        # Create a temporary Python file with the Manim code
        temp_file = f"temp_manim_{uuid.uuid4()}.py"
        with open(temp_file, "w") as f:
            f.write(manim_code)

        # Run Manim to generate the video
        subprocess.run(
            ["python", "-m", "manim", temp_file, "MainScene", "-o", video_filename],
            check=True,
        )

        # Move the generated video to the designated path
        source_video = f"media/videos/temp_manim_{uuid.uuid4()}/1080p60/MainScene.mp4"
        if os.path.exists(source_video):
            os.rename(source_video, video_path)

        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)

    except Exception as e:
        print(f"Error generating video: {str(e)}")
        # Create an error log file
        with open(f"{video_path}.error.log", "w") as f:
            f.write(f"Error generating video: {str(e)}\n\nManim Code:\n{manim_code}")


# Serve static files
@app.route("/static/videos/<path:filename>")
def serve_video(filename):
    return send_from_directory(VIDEOS_DIR, filename)


@app.route("/summarize", methods=["GET"])
def asdasd():
    return "asdasd"


@app.route("/summarize-audio", methods=["POST"])
def summarize_audio():
    # Generate a unique ID
    audio_id = str(uuid.uuid4())

    # Create a timestamp-based name
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    audio_name = f"Voice at {current_date}"

    # Check if the request contains a file or base64 data
    if "file" in request.files:
        # Handle file upload
        audio_file = request.files["file"]

        if not audio_file or audio_file.filename == "":
            return jsonify({"error": "No audio file selected"}), 400

        # Get original filename
        original_filename = audio_file.filename

        # Save file with ID as name
        save_path = os.path.join(FILES_DIR, f"{audio_id}.wav")
        audio_file.save(save_path)

    elif request.json and "audioData" in request.json:
        # Handle base64 encoded audio data from recording
        try:
            audio_data = request.json["audioData"]
            # Remove the data URL prefix if present
            if "base64," in audio_data:
                audio_data = audio_data.split("base64,")[1]

            # Decode the base64 data
            binary_data = base64.b64decode(audio_data)

            # Save the binary data to a file
            save_path = os.path.join(FILES_DIR, f"{audio_id}.wav")
            with open(save_path, "wb") as f:
                f.write(binary_data)

            original_filename = "recorded_audio.wav"
        except Exception as e:
            return jsonify({"error": f"Failed to process audio data: {str(e)}"}), 400
    else:
        return jsonify({"error": "No audio data provided"}), 400

    try:
        # Transcribe audio to text
        transcription = transcribe_audio(save_path)

        # If transcription is empty or too short, return an error
        if not transcription or len(transcription.strip()) < 5:
            return (
                jsonify(
                    {
                        "error": "Could not transcribe audio - recording may be too short or empty"
                    }
                ),
                400,
            )

        # Generate summary from transcription
        summary = generate_summary(transcription)

        return jsonify(
            {
                "id": audio_id,
                "name": audio_name,
                "filename": original_filename,
                "transcription": transcription,
                "summary": summary,
            }
        )
    except Exception as e:
        return jsonify({"error": f"Failed to process audio file: {str(e)}"}), 500


@app.route("/summarize-text", methods=["POST"])
def summarize_text():
    # Get JSON data from request
    data = request.json

    if not data or "text" not in data or not data["text"]:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"]

    # Generate a unique ID
    text_id = str(uuid.uuid4())

    # Create a timestamp-based name
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text_name = f"Text at {current_date}"

    try:
        # Generate summary using OpenAI
        summary = generate_summary(text)

        return jsonify({"id": text_id, "name": text_name, "summary": summary})
    except Exception as e:
        return jsonify({"error": f"Failed to process text: {str(e)}"}), 500


@app.route("/meta-summarize", methods=["POST"])
def meta_summarize():
    # Get JSON data from request
    data = request.json

    if not data or "summaries" not in data or not isinstance(data["summaries"], list):
        return (
            jsonify(
                {"error": "Invalid request format. Please provide a list of summaries."}
            ),
            400,
        )

    summaries = data["summaries"]

    if len(summaries) == 0:
        return jsonify({"error": "No summaries provided"}), 400

    # Optional title for the meta-summary
    title = data.get("title", "Document Collection")

    # Combine summaries with numbering for context
    combined_text = f"Generate a comprehensive summary of the following document summaries for the collection titled '{title}':\n\n"

    for i, summary in enumerate(summaries, 1):
        combined_text += f"Document {i}:\n{summary}\n\n"

    try:
        # Generate meta-summary using OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or another appropriate model
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that synthesizes multiple document summaries into a cohesive meta-summary. Focus on key themes, patterns, and important information across all documents. You will ensure that it is short (maximum 600 words) and fits within two paragraphs.",
                },
                {"role": "user", "content": combined_text},
            ],
        )

        meta_summary = response.choices[0].message.content

        return jsonify(
            {
                "meta_summary": meta_summary,
                "document_count": len(summaries),
                "title": title,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to generate meta-summary: {str(e)}"}), 500


@app.route("/summarize", methods=["POST"])
def summarize_files():
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")

    if not files or files[0].filename == "":
        return jsonify({"error": "No files selected"}), 400

    results = []

    for file in files:
        if file and file.filename.lower().endswith(".pdf"):
            # Generate a unique ID
            file_id = str(uuid.uuid4())

            # Get original filename and extension
            original_filename = file.filename
            file_extension = original_filename.split(".")[-1]

            # Save file with ID as name
            save_path = os.path.join(FILES_DIR, f"{file_id}.{file_extension}")
            file.save(save_path)

            # Extract text from PDF
            try:
                pdf_text = extract_text_from_pdf(save_path)

                # Generate summary using OpenAI
                summary = generate_summary(pdf_text)

                results.append(
                    {"id": file_id, "filename": original_filename, "summary": summary}
                )
            except Exception as e:
                results.append(
                    {
                        "id": file_id,
                        "filename": original_filename,
                        "error": f"Failed to process file: {str(e)}",
                    }
                )
        else:
            results.append(
                {
                    "filename": file.filename if file else "Unknown",
                    "error": "Not a PDF file or invalid file",
                }
            )

    return jsonify({"results": results})


@app.route("/answer-question", methods=["POST"])
def answer_question():
    # Get JSON data from request
    data = request.json

    if not data or "question" not in data or not data["question"]:
        return jsonify({"error": "No question provided"}), 400

    if (
        "summaries" not in data
        or not isinstance(data["summaries"], list)
        or len(data["summaries"]) == 0
    ):
        return jsonify({"error": "No document summaries provided"}), 400

    question = data["question"]
    summaries = data["summaries"]
    personality = data.get("personality", "helpful and informative")

    # Check if the question would benefit from a video explanation
    needs_video = check_video_requirement(question)

    # Create a video ID and path if a video is needed
    video_id = None
    video_url = None

    if needs_video:
        video_id = str(uuid.uuid4())
        video_filename = f"{video_id}.mp4"
        video_path = os.path.join(VIDEOS_DIR, video_filename)
        video_url = f"/static/videos/{video_filename}"

    # Create context from summaries
    context = "I'll provide you with summaries of several documents. Based on this information, please answer the question that follows.\n\n"

    # Create a list of document names for referencing
    doc_names = []

    for i, summary_item in enumerate(summaries, 1):
        # Handle both formats: plain string or {name, summary} object
        if isinstance(summary_item, dict):
            doc_name = summary_item.get("name", f"Document {i}")
            doc_id = summary_item.get("id", str(i))
            summary = summary_item.get("summary", "")
        else:
            doc_name = f"Document {i}"
            doc_id = str(i)
            summary = summary_item

        doc_names.append(doc_name)
        context += f"Document: {doc_name} (ID: {doc_id})\nSummary: {summary}\n\n"

    context += f"Question: {question}\n\n"
    context += "Please provide a comprehensive answer based solely on the information provided in these document summaries. "
    context += "Include specific references to the documents using the format [Document Name] where 'Document Name' is the exact name of the document. "
    context += "When you cite information from a specific document, make it clear which document it came from. "
    context += f"This is your response tone: {personality}"

    # Select model based on whether a video is needed
    model = "gpt-4o" if needs_video else "gpt-4o-mini"

    try:
        # Generate answer using OpenAI
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful AI assistant that answers questions based on document summaries. Provide well-reasoned, comprehensive answers based only on the information in the provided documents. Cite specific documents using the [Document Name] format when referencing information. The available document names are: {', '.join(doc_names)}. If the documents don't contain relevant information to answer the question, acknowledge that limitation.",
                },
                {"role": "user", "content": context},
            ],
        )

        answer = response.choices[0].message.content

        # Create a references object mapping document names to document info
        references = {}
        for summary_item in summaries:
            if isinstance(summary_item, dict):
                doc_name = summary_item.get("name", "")
                if doc_name:
                    references[doc_name] = {
                        "id": summary_item.get("id", ""),
                        "name": doc_name,
                    }

        result = {
            "answer": answer,
            "question": question,
            "document_count": len(summaries),
            "references": references,
        }

        # Add video URL to response if a video is needed
        if needs_video and video_url:
            result["video"] = f"http://localhost:8080{video_url}"

            # Start video generation in a background thread
            def generate_video_async():
                manim_code = generate_manim_code(question, answer)
                render_manim_video(manim_code, video_path, video_filename)

            threading.Thread(target=generate_video_async).start()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Failed to generate answer: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)

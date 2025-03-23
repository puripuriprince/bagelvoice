import base64
import datetime
import os
import uuid

import dotenv
import PyPDF2
from flask import Flask, jsonify, request
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

# Ensure files directory exists
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)


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
    personality = data["personality"]
    print(personality)
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
    context += "When you cite information from a specific document, make it clear which document it came from."
    context += f"This is your response tone: {personality}"

    try:
        # Generate answer using OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or another appropriate model
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

        return jsonify(
            {
                "answer": answer,
                "question": question,
                "document_count": len(summaries),
                "references": references,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to generate answer: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)

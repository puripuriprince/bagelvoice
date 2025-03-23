import os
import sys
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Add the notebook directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the GeminiClient
from models.gemini_client import GeminiClient

def ensure_directory_exists(directory_path):
    """Make sure the output directory exists"""
    os.makedirs(directory_path, exist_ok=True)

def process_pdf_to_lecture(pdf_path, output_dir):
    """
    Process a PDF file using Gemini, generate a lecture-style summary,
    and save it to a text file.

    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str): Directory to save the output text file

    Returns:
        str: Path to the generated text file
    """
    print(f"Processing PDF: {pdf_path}")

    # Extract the filename without extension for the output file
    pdf_filename = os.path.basename(pdf_path)
    base_filename = os.path.splitext(pdf_filename)[0]

    # Initialize the Gemini client
    print("Initializing Gemini client...")
    client = GeminiClient()
    print("Client initialized successfully!")

    # Create a lecture-style prompt
    lecture_prompt = """
    Create a comprehensive lecture from this document. Structure it with:

    1. TITLE AND OVERVIEW:
       - Begin with a clear title based on the document content
       - Provide a brief overview of what the lecture will cover

    2. INTRODUCTION:
       - Explain the main topic and its importance
       - Provide necessary background context
       - Outline the key learning objectives

    3. MAIN CONTENT:
       - Organize into 3-5 clearly defined chapters with descriptive titles
       - Include subsections with key concepts, definitions, and explanations
       - Preserve any important formulas, theories, or methodologies
       - Describe any charts, diagrams, or visual elements present in the document

    4. PRACTICAL APPLICATIONS:
       - Include examples of how the concepts are applied in real-world scenarios
       - Explain the practical significance of the material

    5. CONCLUSION:
       - Summarize the key points from each section
       - Connect the concepts to broader themes or future directions
       - End with final thoughts on the importance of the material

    Format it as a well-structured lecture that could be presented to university students.
    Use Markdown formatting for better readability (headings with #, lists with -, etc.).
    """

    # Process the PDF with Gemini
    print(f"Generating lecture from PDF...")
    start_time = time.time()

    try:
        result = client.process_pdf(pdf_path, prompt=lecture_prompt, use_pro_model=True)

        # Extract the text from the result
        lecture_text = result["text"]

        # Create the output file path
        output_filename = f"{base_filename}_lecture.md"
        output_path = os.path.join(output_dir, output_filename)

        # Save the lecture to a text file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(lecture_text)

        processing_time = time.time() - start_time
        print(f"Lecture generated successfully in {processing_time:.2f} seconds!")
        print(f"Output saved to: {output_path}")

        return output_path

    except Exception as e:
        print(f"Error processing PDF: {e}")
        traceback.print_exc()
        raise

def main():
    """Main function to run the PDF processing test"""
    # Load environment variables
    load_dotenv()

    # Check if GEMINI_API_KEY is set
    if not os.environ.get('GEMINI_API_KEY'):
        print("Error: GEMINI_API_KEY environment variable is not set")
        print("Please set it in your .env file or export it to your environment")
        sys.exit(1)

    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "notebook", "data", "user_kenny")

    # Ensure the output directory exists
    ensure_directory_exists(data_dir)

    # Default PDF path (the queues.pdf we mentioned earlier)
    default_pdf_path = os.path.join(data_dir, "queues.pdf")

    # If the default file doesn't exist, look for alternatives or ask for input
    if not os.path.exists(default_pdf_path):
        print(f"Default PDF not found at: {default_pdf_path}")

        # Look for any PDF in the data directory
        pdf_files = list(Path(data_dir).glob("*.pdf"))

        if pdf_files:
            # Use the first PDF found
            pdf_path = str(pdf_files[0])
            print(f"Using alternative PDF: {pdf_path}")
        else:
            # Ask the user for a PDF path
            pdf_path = input("Please enter the path to a PDF file: ")

            if not os.path.exists(pdf_path):
                print(f"Error: File not found at {pdf_path}")
                sys.exit(1)
    else:
        pdf_path = default_pdf_path

    # Process the PDF and generate the lecture
    output_path = process_pdf_to_lecture(pdf_path, data_dir)

    print("\nProcess completed successfully!")
    print(f"You can find the generated lecture at: {output_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)

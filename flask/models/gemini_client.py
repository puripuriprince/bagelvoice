import os
import sys
import traceback
import pathlib
from dotenv import load_dotenv

class GeminiClient:
    """
    Client for interacting with Google's Gemini API.
    Provides PDF processing capabilities without running local models.
    """
    def __init__(self):
        # Load environment variables if not already loaded
        load_dotenv()

        # Read the API key from the environment variable
        self.api_key = os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment")

        # Initialize the Gemini client
        self._initialize_client()

        print("Gemini client initialized successfully")

    def _initialize_client(self):
        """Initialize the Google Gemini API client"""
        try:
            # Import Google Gemini libraries - fixed import
            import google.generativeai as genai

            # Configure the client with your API key
            genai.configure(api_key=self.api_key)

            # Create a client instance
            self.client = genai.GenerativeModel

            # Set default models
            self.default_model = "gemini-1.5-flash"  # Faster model
            self.pro_model = "gemini-1.5-pro"        # More capable model

        except ImportError as e:
            print(f"Error importing Google Gemini libraries: {e}")
            print("Please install the required packages with:")
            print("pip install google-generativeai --upgrade --no-cache-dir")
            raise
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
            traceback.print_exc()
            raise

    def process_pdf(self, pdf_path, prompt=None, use_pro_model=False):
        """
        Process a PDF file using Google Gemini.

        Args:
            pdf_path (str): Path to the PDF file
            prompt (str, optional): Custom prompt for the model
            use_pro_model (bool): Whether to use the more capable Pro model

        Returns:
            dict: Contains the processed response and metadata
        """
        try:
            # Import required libraries for Gemini
            import google.generativeai as genai
            from pathlib import Path

            # Check if file exists
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            # Read the PDF file as bytes
            filepath = Path(pdf_path)
            pdf_bytes = filepath.read_bytes()

            # Use default prompt if none provided
            if prompt is None:
                prompt = "Please analyze this document and provide a comprehensive summary. Include the main topics, key points, and important conclusions."

            # Choose which model to use
            model_name = self.pro_model if use_pro_model else self.default_model

            print(f"Processing PDF with Gemini {model_name}...")
            print(f"Prompt: {prompt}")

            # Process the PDF directly with Gemini
            model = genai.GenerativeModel(model_name)

            response = model.generate_content(
                contents=[
                    {
                        "mime_type": "application/pdf",
                        "data": pdf_bytes
                    },
                    prompt
                ]
            )

            # Extract the text from the response
            result = {
                "text": response.text,
                "model": model_name,
                "file_path": pdf_path,
                "file_name": os.path.basename(pdf_path)
            }

            return result

        except Exception as e:
            print(f"Error processing PDF with Gemini: {e}")
            traceback.print_exc()
            raise

    def summarize_document(self, pdf_path):
        """
        Generate a concise summary of a PDF document.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            str: Summary of the document
        """
        prompt = """
        Please provide a concise summary of this document. Include:
        1. The main topic and purpose of the document
        2. Key points and arguments presented
        3. Important findings or conclusions
        4. Any recommendations or next steps mentioned

        Keep the summary clear and focused on the most important information.
        """

        result = self.process_pdf(pdf_path, prompt=prompt)
        return result

    def analyze_document(self, pdf_path):
        """
        Perform a detailed analysis of a PDF document.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            dict: Detailed analysis of the document
        """
        prompt = """
        Please provide a detailed analysis of this document. Include:

        1. DOCUMENT OVERVIEW:
           - Title, authors, and publication date if available
           - Document type (research paper, report, article, etc.)
           - Main topic and purpose

        2. CONTENT ANALYSIS:
           - Key sections and their main points
           - Main arguments or claims presented
           - Evidence provided to support claims
           - Methodology used (if applicable)

        3. KEY FINDINGS:
           - Major results or conclusions
           - Limitations acknowledged
           - Implications discussed

        4. CRITICAL EVALUATION:
           - Strengths and weaknesses
           - Relevance and significance of the work
           - How it connects to existing knowledge

        Format your response with clear headings and bullet points for readability.
        """

        result = self.process_pdf(pdf_path, prompt=prompt, use_pro_model=True)
        return result

    def extract_key_information(self, pdf_path, information_type=None):
        """
        Extract specific types of information from a PDF document.

        Args:
            pdf_path (str): Path to the PDF file
            information_type (str): Type of information to extract (e.g., "tables", "citations")

        Returns:
            dict: Extracted information
        """
        if information_type is None or information_type == "tables":
            prompt = """
            Please extract all tables from this document and present them in a structured format.
            For each table:
            1. Provide the table title/caption if available
            2. Convert the table to a markdown or plaintext representation
            3. Briefly explain what the table represents or its significance

            If there are no tables, please state that and provide a summary of the key numerical data or statistics mentioned in the document instead.
            """
        elif information_type == "citations":
            prompt = """
            Please extract all citations and references from this document. For each citation:
            1. List the citation as it appears in the text
            2. If there's a references/bibliography section, match each citation to its full reference

            Present the results in a clear, organized format.
            """
        elif information_type == "definitions":
            prompt = """
            Please extract all key terms, concepts, and their definitions from this document.
            Present them in a glossary format with:
            1. The term or concept
            2. Its definition as provided in the document
            3. The context in which it's used (if available)

            Focus on technical terms, specialized vocabulary, and important concepts.
            """
        else:
            prompt = f"Please extract the following information from this document: {information_type}"

        result = self.process_pdf(pdf_path, prompt=prompt, use_pro_model=True)
        return result

    def answer_questions(self, pdf_path, questions):
        """
        Answer specific questions based on a PDF document.

        Args:
            pdf_path (str): Path to the PDF file
            questions (list or str): Questions to answer

        Returns:
            dict: Answers to the questions
        """
        # Format the questions
        if isinstance(questions, list):
            formatted_questions = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        else:
            formatted_questions = questions

        prompt = f"""
        Please answer the following questions based solely on the information provided in this document:

        {formatted_questions}

        For each answer:
        1. Provide a clear, concise response
        2. Cite the specific section or page where the information was found
        3. If the document doesn't contain information to answer a question, state that clearly

        Base your answers exclusively on the document content, not on external knowledge.
        """

        result = self.process_pdf(pdf_path, prompt=prompt)
        return result


# Test the Gemini functionality if this file is run directly
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Check if API key is available
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set it in your .env file or environment variables")
        print("\nAttempting to check other possible API key names...")

        # Check for alternative key names
        alternative_keys = ['GOOGLE_API_KEY', 'GOOGLE_GENERATIVE_AI_KEY', 'GOOGLE_GEMINI_API_KEY']
        for key_name in alternative_keys:
            if os.environ.get(key_name):
                print(f"Found alternative API key: {key_name}")
                os.environ['GEMINI_API_KEY'] = os.environ.get(key_name)
                print("Using this key instead.")
                break
        else:
            print("No alternative API keys found.")
            api_key = input("Please enter your Gemini API key: ")
            os.environ['GEMINI_API_KEY'] = api_key

    print("\n===== Testing Gemini PDF Processing =====")
    print(f"API key status: {'Available' if api_key else 'Not available'}")

    try:
        # First, make sure package is installed
        try:
            import google.generativeai
            print("Google Generative AI package is installed correctly.")
        except ImportError:
            print("Google Generative AI package is not installed.")
            print("Installing now...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                                  "google-generativeai", "--upgrade", "--no-cache-dir"])
            print("Package installed successfully. Continuing...")

        # Initialize the client
        print("\nInitializing Gemini client...")
        client = GeminiClient()
        print("Client initialized successfully!")

        # Path to test PDF
        pdf_path = "notebook/data/user_kenny/queues.pdf"

        if not os.path.exists(pdf_path):
            print(f"Error: Test PDF not found at {pdf_path}")
            print("Current working directory:", os.getcwd())
            alternative_paths = [
                "data/user_kenny/queues.pdf",
                "../data/user_kenny/queues.pdf",
                "notebook/data/queues.pdf",
                "data/queues.pdf"
            ]

            # Try to find the PDF in alternative locations
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    print(f"Found PDF at alternative path: {alt_path}")
                    pdf_path = alt_path
                    break
            else:
                # If loop completes without finding file, ask for path
                pdf_path = input("Please enter the full path to the PDF file: ")
                if not os.path.exists(pdf_path):
                    print(f"Error: File not found at {pdf_path}")
                    sys.exit(1)

        print(f"\nFound PDF file: {pdf_path}")

        # Run the document summarization test
        print("\n===== GENERATING PDF SUMMARY =====\n")
        result = client.summarize_document(pdf_path)

        print("\n===== SUMMARY RESULT =====\n")
        print(result["text"])

        print("\n===== TEST COMPLETED SUCCESSFULLY =====")

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nDetailed traceback:")
        traceback.print_exc()

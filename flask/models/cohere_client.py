import cohere
import os
import sys
import traceback
from dotenv import load_dotenv

class CohereClient:
    """
    Client for interacting with Cohere API.
    Handles RAG-specific operations and document summarization using Cohere models.
    """
    def __init__(self):
        # Read the API key from the environment variable
        self.api_key = os.environ.get('COHERE_API_KEY')
        if not self.api_key:
            raise ValueError("COHERE_API_KEY is not set in the environment")

        # Initialize the Cohere client
        self.client = cohere.ClientV2(self.api_key)

        # Default model settings
        self.chat_model = "command-a-03-2025"
        self.embed_model = "embed-english-v3.0"
        self.rerank_model = "rerank-english-v3.0"

        print("Cohere client initialized successfully")

    def chat_with_docs(self, message, documents, conversation_history=None):
        """
        Generate a response using Cohere's chat endpoint with RAG.

        This method uses documents as context to answer questions.

        Args:
            message (str): The user's message
            documents (list): List of document dictionaries for context.
                Each document should have 'id' and 'data' fields.
                The 'data' field should contain at least one field (e.g., 'text', 'title').
            conversation_history (list, optional): Previous conversation history

        Returns:
            dict: Cohere chat response
        """
        if conversation_history is None:
            conversation_history = []

        # Format messages for the chat API
        messages = conversation_history.copy()
        messages.append({"role": "user", "content": message})

        # Debug: Print parameters being sent to the API
        print("\n===== REQUEST PARAMETERS (RAG) =====")
        print(f"Model: {self.chat_model}")
        print(f"Message: {message[:100]}..." if len(message) > 100 else f"Message: {message}")
        print(f"Message count: {len(messages)}")

        # Validate documents format
        print("\nValidating documents format...")
        if not isinstance(documents, list):
            print(f"ERROR: 'documents' is not a list. Type: {type(documents)}")
            raise ValueError("documents must be a list")

        print(f"Document count: {len(documents)}")

        # Validate and fix document format if needed
        valid_docs = []
        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                print(f"Warning: Document {i} is not a dictionary. Skipping.")
                continue

            # Ensure each document has id and data fields
            doc_id = doc.get('id')
            if not doc_id:
                doc_id = f"doc_{i}"
                print(f"Warning: Document {i} missing 'id'. Generated ID: {doc_id}")

            # Ensure data field exists and contains at least one sub-field
            doc_data = doc.get('data', {})
            if not doc_data or not isinstance(doc_data, dict) or len(doc_data) == 0:
                # If data is missing or empty, try to construct it from other fields
                doc_data = {}

                # Check if document has direct text/title fields
                if 'text' in doc:
                    doc_data['text'] = doc['text']
                elif 'snippet' in doc:
                    doc_data['text'] = doc['snippet']
                elif 'content' in doc:
                    doc_data['text'] = doc['content']

                if 'title' in doc:
                    doc_data['title'] = doc['title']

                # If still no data, skip this document
                if not doc_data:
                    print(f"Warning: Document {i} has no valid content. Skipping.")
                    continue

            # Create a valid document
            valid_doc = {
                'id': doc_id,
                'data': doc_data
            }

            valid_docs.append(valid_doc)

        if not valid_docs:
            raise ValueError("No valid documents found for RAG query")

        documents = valid_docs

        # Sample first document structure
        if documents:
            print("\nSample document structure:")
            sample_doc = documents[0]
            print(f"Document type: {type(sample_doc)}")
            print(f"Document keys: {sample_doc.keys() if isinstance(sample_doc, dict) else 'Not a dictionary'}")
            if 'data' in sample_doc:
                print(f"Data keys: {sample_doc['data'].keys() if isinstance(sample_doc['data'], dict) else 'Not a dictionary'}")

        try:
            print("\nSending request to Cohere API...")
            response = self.client.chat(
                model=self.chat_model,
                messages=messages,
                documents=documents,
                temperature=0.7
            )

            # Extract text from response based on actual structure
            response_text = None
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                content_items = response.message.content
                if content_items and len(content_items) > 0:
                    for item in content_items:
                        if hasattr(item, 'text'):
                            if response_text is None:
                                response_text = item.text
                            else:
                                response_text += item.text

            # Add text attribute to response for compatibility
            if response_text is not None:
                response.text = response_text
            else:
                print("WARNING: Could not extract text from response")
                response.text = "Error: Could not extract text from response"

            return response
        except Exception as e:
            print(f"Error in chat_with_docs: {e}")
            print("Traceback:")
            traceback.print_exc()
            raise

    def summarize_documents(self, documents, prompt=None, max_tokens=1024):
        """
        Generate a summary of documents using Cohere's LLM capabilities.

        This method focuses on creating a concise summary rather than answering questions.

        Args:
            documents (list): List of document dictionaries to summarize
            prompt (str, optional): Custom instructions for the summary style/focus
            max_tokens (int, optional): Maximum tokens for the response

        Returns:
            dict: Cohere chat response containing the summary
        """
        # Create a prompt for summarization if not provided
        if prompt is None:
            prompt = "Summarize the following documents, highlighting the main points and key information:"

        # Format the documents into a text representation
        documents_text = ""
        for i, doc in enumerate(documents):
            if isinstance(doc, dict):
                title = None
                text = None

                # Extract title from document
                if 'data' in doc and isinstance(doc['data'], dict):
                    if 'title' in doc['data']:
                        title = doc['data']['title']

                    # Extract text content from various possible fields
                    if 'snippet' in doc['data']:
                        text = doc['data']['snippet']
                    elif 'text' in doc['data']:
                        text = doc['data']['text']
                elif 'title' in doc:
                    title = doc['title']

                    if 'snippet' in doc:
                        text = doc['snippet']
                    elif 'text' in doc:
                        text = doc['text']

                # Add document to the text representation
                if title and text:
                    documents_text += f"\n\nDocument {i+1}: {title}\n{text}"
                elif text:
                    documents_text += f"\n\nDocument {i+1}:\n{text}"
            elif isinstance(doc, str):
                documents_text += f"\n\nDocument {i+1}:\n{doc}"

        # Combined prompt for summarization
        combined_prompt = f"{prompt}\n\n{documents_text}"

        # Debug: Print parameters
        print("\n===== REQUEST PARAMETERS (SUMMARIZATION) =====")
        print(f"Model: {self.chat_model}")
        print(f"Prompt length: {len(combined_prompt)} characters")
        print(f"Max tokens: {max_tokens}")

        try:
            print("\nSending summarization request to Cohere API...")
            response = self.client.chat(
                model=self.chat_model,
                messages=[{"role": "user", "content": combined_prompt}],
                temperature=0.5,
                max_tokens=max_tokens
            )

            # Extract text from response based on actual structure
            response_text = None
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                content_items = response.message.content
                if content_items and len(content_items) > 0:
                    for item in content_items:
                        if hasattr(item, 'text'):
                            if response_text is None:
                                response_text = item.text
                            else:
                                response_text += item.text

            # Add text attribute to response for compatibility
            if response_text is not None:
                response.text = response_text
            else:
                print("WARNING: Could not extract text from response")
                response.text = "Error: Could not extract text from response"

            return response
        except Exception as e:
            print(f"Error in summarize_documents: {e}")
            print("Traceback:")
            traceback.print_exc()
            raise

    def embed_texts(self, texts):
        """
        Generate embeddings for a list of texts.

        Args:
            texts (list): List of text strings to embed

        Returns:
            list: List of embeddings
        """
        try:
            response = self.client.embed(
                texts=texts,
                model=self.embed_model
            )
            return response.embeddings
        except Exception as e:
            print(f"Error in embed_texts: {e}")
            print("Traceback:")
            traceback.print_exc()
            raise

    def rerank_chunks(self, query, chunks, top_n=5):
        """
        Rerank document chunks based on relevance to the query.

        Args:
            query (str): The user query
            chunks (list): List of text chunks to rerank
            top_n (int): Number of top chunks to return

        Returns:
            list: Ranked document chunks with scores and metadata
        """
        try:
            # Convert chunks to the format expected by Cohere's rerank
            documents = []
            for i, chunk in enumerate(chunks):
                if isinstance(chunk, dict) and 'text' in chunk:
                    doc = {
                        "text": chunk['text'],
                        "id": chunk.get('id', f"chunk_{i}")
                    }
                    # Add any additional metadata
                    for key, value in chunk.items():
                        if key not in ['text', 'id']:
                            doc[key] = value
                    documents.append(doc)
                else:
                    documents.append({
                        "text": chunk,
                        "id": f"chunk_{i}"
                    })

            # Perform reranking
            response = self.client.rerank(
                model=self.rerank_model,
                query=query,
                documents=documents,
                top_n=top_n
            )

            # Format the results
            results = []
            for item in response.results:
                result = {
                    "text": item.document,
                    "score": item.relevance_score,
                    "id": item.document_id
                }
                results.append(result)

            return results
        except Exception as e:
            print(f"Error in rerank_chunks: {e}")
            print("Traceback:")
            traceback.print_exc()
            raise


# Test the RAG and summarization functionality if this file is run directly
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    import traceback

    # Load environment variables from .env file
    load_dotenv()

    print("\n===== Testing Cohere Integration =====")

    # Display API key status (masked)
    api_key = os.environ.get('COHERE_API_KEY')
    if api_key:
        masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
        print(f"COHERE_API_KEY found: {masked_key}")
        print(f"Current working directory: {os.getcwd()}")
    else:
        print("COHERE_API_KEY not found in environment variables")
        print("Attempting to load from .env file...")

        # Try again with explicit path
        parent_dir = os.path.dirname(os.getcwd())
        env_path = os.path.join(parent_dir, '.env')
        if os.path.exists(env_path):
            print(f"Found .env at: {env_path}")
            load_dotenv(env_path)
            api_key = os.environ.get('COHERE_API_KEY')
            if api_key:
                print("Successfully loaded API key from .env file")
            else:
                print("Failed to load API key from .env file")
                api_key = input("Enter your Cohere API key: ")
                os.environ['COHERE_API_KEY'] = api_key

    try:
        # Initialize the client
        print("\nInitializing Cohere client...")
        client = CohereClient()
        print("Client initialized successfully!")

        # Define sample documents
        sample_documents = [
            {
                "id": "doc_1",
                "data": {
                    "title": "Introduction to Derivatives",
                    "snippet": "In calculus, the derivative of a function of a real variable measures the sensitivity to change of the function value with respect to a change in its argument. Derivatives are a fundamental tool of calculus. The derivative of a function at a chosen input value describes the rate of change of the function near that input value. The process of finding a derivative is called differentiation. Geometrically, the derivative at a point is the slope of the tangent line to the graph of the function at that point."
                }
            },
            {
                "id": "doc_2",
                "data": {
                    "title": "Derivative Applications",
                    "snippet": "Derivatives have numerous applications in mathematics, physics, engineering, and economics. They are used to find rates of change, optimize functions, solve differential equations, and model real-world phenomena. In physics, the derivative of position with respect to time is velocity, and the derivative of velocity with respect to time is acceleration. In economics, the derivative of a cost function gives the marginal cost, and the derivative of a utility function gives the marginal utility."
                }
            },
            {
                "id": "doc_3",
                "data": {
                    "title": "Computing Derivatives",
                    "snippet": "There are multiple ways to compute derivatives, including the limit definition, power rule, product rule, quotient rule, and chain rule. The choice of method depends on the function's structure. For a function f(x), the derivative is defined as the limit of the difference quotient as h approaches zero: f'(x) = lim(h→0) [f(x+h) - f(x)]/h. This definition can be challenging to apply directly, so we typically use established rules for common functions."
                }
            }
        ]

        # Ask for test mode
        print("\nChoose test mode:")
        print("1. RAG (Question Answering)")
        print("2. Document Summarization")
        print("3. Run both tests")

        choice = input("Enter your choice (1-3, default=3): ").strip()
        if not choice:
            choice = "3"

        # Run selected test(s)
        if choice in ["1", "3"]:
            # Testing RAG functionality
            question = "What is a derivative and how is it used in different fields?"
            print(f"\n\n===== TESTING RAG WITH QUESTION: '{question}' =====")

            # Send request to Cohere
            print("Waiting for response from Cohere API...")
            rag_response = client.chat_with_docs(question, sample_documents)

            # Extract and display the response
            print("\n===== RAG RESPONSE =====")

            # Handle text extraction based on response structure
            if hasattr(rag_response, 'text'):
                print(rag_response.text)
            elif hasattr(rag_response, 'message'):
                if hasattr(rag_response.message, 'content'):
                    for item in rag_response.message.content:
                        if hasattr(item, 'text'):
                            print(item.text)
                else:
                    print("Response message format not as expected")
                    print(f"Response structure: {dir(rag_response.message)}")
            else:
                print("Unexpected response format")
                print(f"Response attributes: {dir(rag_response)}")

            # Display citations if available
            print("\n===== CITATIONS =====")
            citations_found = False

            if hasattr(rag_response, "citations") and rag_response.citations:
                citations_found = True
                for citation in rag_response.citations:
                    print(f"- Text: '{citation.text}'")
                    print(f"  Sources: {[s.document['title'] for s in citation.sources]}")
                    print()
            elif hasattr(rag_response, 'message') and hasattr(rag_response.message, 'citations') and rag_response.message.citations:
                citations_found = True
                for citation in rag_response.message.citations:
                    print(f"- Text: '{citation.text}'")
                    print(f"  Sources: {[s.document['title'] for s in citation.sources if hasattr(s, 'document')]}")
                    print()

            if not citations_found:
                print("No citations found in the response")

            print("\n===== RAG TEST COMPLETED =====")

        if choice in ["2", "3"]:
            # Testing summarization functionality
            print(f"\n\n===== TESTING DOCUMENT SUMMARIZATION =====")

            # Custom prompt for summarization
            summary_prompt = "Provide a comprehensive summary of these documents about derivatives in mathematics. Highlight key concepts, applications, and calculation methods."

            # Send request to Cohere
            print("Waiting for summarization response from Cohere API...")
            summary_response = client.summarize_documents(sample_documents, prompt=summary_prompt)

            # Extract and display the summary
            print("\n===== SUMMARY RESPONSE =====")

            # Handle text extraction based on response structure
            if hasattr(summary_response, 'text'):
                print(summary_response.text)
            elif hasattr(summary_response, 'message'):
                if hasattr(summary_response.message, 'content'):
                    for item in summary_response.message.content:
                        if hasattr(item, 'text'):
                            print(item.text)
                else:
                    print("Response message format not as expected")
                    print(f"Response structure: {dir(summary_response.message)}")
            else:
                print("Unexpected response format")
                print(f"Response attributes: {dir(summary_response)}")

            print("\n===== SUMMARIZATION TEST COMPLETED =====")

        print("\n===== ALL TESTS COMPLETED SUCCESSFULLY =====")

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nDetailed traceback:")
        traceback.print_exc()

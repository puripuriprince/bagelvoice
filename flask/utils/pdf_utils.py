#from PyPDF2 import PdfReader
import os
import re

# def extract_text_from_pdf(pdf_path):
#     """
#     Extract text from a PDF file.

#     Args:
#         pdf_path (str): Path to the PDF file

#     Returns:
#         str: Extracted text
#     """
#     if not os.path.exists(pdf_path):
#         raise FileNotFoundError(f"PDF file not found: {pdf_path}")

#     try:
#         reader = PdfReader(pdf_path)
#         text = ""

#         for page in reader.pages:
#             page_text = page.extract_text()
#             if page_text:
#                 text += page_text + "\n\n"

#         # Clean up the text - remove extra whitespace
#         text = re.sub(r'\s+', ' ', text).strip()
#         return text
#     except Exception as e:
#         print(f"Error extracting text from PDF {pdf_path}: {e}")
#         raise

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    """
    Split text into overlapping chunks.

    Args:
        text (str): The text to split
        chunk_size (int): Size of each chunk
        chunk_overlap (int): Overlap between chunks

    Returns:
        list: List of text chunks
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Find the end of this chunk
        end = min(start + chunk_size, text_length)

        # If we're not at the end of the text, try to break at a sentence or paragraph
        if end < text_length:
            # Try to find a paragraph break
            paragraph_break = text.rfind('\n\n', start, end)
            if paragraph_break != -1 and paragraph_break > start + chunk_size // 2:
                end = paragraph_break + 2
            else:
                # Try to find a sentence break (period followed by space)
                sentence_break = text.rfind('. ', start, end)
                if sentence_break != -1 and sentence_break > start + chunk_size // 2:
                    end = sentence_break + 2

        # Extract the chunk and add it to our list
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move the start pointer, accounting for overlap
        start = end - chunk_overlap

        if start >= text_length:
            break

    return chunks

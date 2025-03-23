import os
import sys
import json
import traceback
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

from dotenv import load_dotenv
import fitz 
import uuid

from langchain_astradb import AstraDBVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain import hub
from langchain.agents import AgentExecutor
from google.generativeai.types import HarmCategory, HarmBlockThreshold



# Load environment variables
load_dotenv()

def connect_to_vstore():
    embeddings = HuggingFaceEmbeddings()
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")

    vstore = AstraDBVectorStore(
        embedding=embeddings,
        collection_name="Doc",
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        token=ASTRA_DB_APPLICATION_TOKEN,
        namespace="MedDocs",
    )
    return vstore

def add_documents_to_vstore(texts: list):
    try:
        vstore = connect_to_vstore()

        for text in texts:
            id=f"doc_{uuid.uuid4().hex[:10]}",
            document = Document(
                id=id,
                page_content=text, 
            )

            vstore.add_documents([document]) 
        
        return True, id
    
    except Exception as e:
        print(f"Error: {e}")
        return False, 0

def query_database(query, k=1):
    vstore = connect_to_vstore()
    retriever = vstore.as_retriever(search_kwargs={"k": k})
    
    retrieved_data = retriever.get_relevant_documents(query)
    context = "\n".join([doc.page_content for doc in retrieved_data]) if retrieved_data else "No relevant context available."

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    prompt_template = ( 
        "You are a helpful teaching assistant answering students' questions based on the provided context.\n"
        "Answer the query using the context information.\n"
        "Make sure your answer responds to the user's question.\n\n"
        "Query: {query}\n"
        "Context: {context}"
    )

    result = llm.invoke(prompt_template.format(query=query, context=context))

    return result

def get_documents_by_session(self, session_id: str) -> List[Dict]:
    """
    Get all documents for a specific session.

    Args:
        session_id (str): Session identifier

    Returns:
        List[Dict]: List of documents
    """
    pass

def delete_document(self, document_id: str) -> bool:
    """
    Delete a document and all its chunks.

    Args:
        document_id (str): Document identifier

    Returns:
        bool: Success status
    """
    pass

def close(self):
    """Close the database connection."""
    pass

def summarizer(text):
    """Summarize the text using the Google Generative AI model."""

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    prompt_template = ( 
        "You are a helpful assistant that summarizes text. "
        "Make sure your answer summarizes the query information.\n"
        "Query: {text}\n"
    )

    result = llm.invoke(prompt_template.format(text=text))
    
    return result


if __name__ == "__main__":
    pass
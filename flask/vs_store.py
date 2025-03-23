from dotenv import load_dotenv
import os
import json
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

def query_database(query, k=1):
    vstore = connect_to_vstore()

    retriever = vstore.as_retriever(search_kwargs={"k": k})

    retrieved_data = retriever.get_relevant_documents(query)

    context = "\n".join([doc.page_content for doc in retrieved_data])

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    prompt_template = ( 
        "You are a helpful assistant answering medical questions based on the provided context. "
        "Answer the query using the context information.\n"
        "Make sure your awnser responde to the user question"
        "Query: {query}\n"
        "Context: {context}" 
    )

    result = llm.invoke(prompt_template.format(query=query, context=context))

    return result

def add_documents_to_vstore(texts: list):
    try:
        vstore = connect_to_vstore()

        for text in texts:
            document = Document(
                id=doc_id,
                page_content=text, 
            )

            vstore.add_documents([document]) 
        
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        return False
    
def extract_text_from_pdf(pdf_path):
    with fitz.open(pdf_path) as doc:
        text = "\n".join([page.get_text() for page in doc])
    return text

def add_pdf_to_vstore(pdf_path):
    try:
        vstore = connect_to_vstore()

        document = Document(
            id=f"doc_{uuid.uuid4().hex[:10]}",
            page_content=extract_text_from_pdf(pdf_path), 
        )

        vstore.add_documents([document]) 
        
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    # with open("sections.json", "r") as file:
    #     documents = json.load(file)

    # add_documents_to_vstore(documents)

    print(query_database("Cure"))
    # print(query_database("Best Cure Headache"))

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test the RAG chat API by asking questions about documents in the vector store.
Usage: python -m flask.tests.test_rag_chat [--query "Your question"] [--document_id DOC_ID] [--session_id SESSION_ID]
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

def test_rag_chat(query=None, document_id=None, session_id=None):
    """Test the RAG chat functionality"""
    print("=" * 80)
    print(f"🤖 TESTING RAG CHAT")
    print("=" * 80)

    # Create a default query if not provided
    if not query:
        query = "What are the main concepts covered in these documents?"

    # Flask app base URL
    base_url = 'http://localhost:5000'

    # Construct payload
    payload = {
        "query": query
    }

    # Add document_id if provided
    if document_id:
        payload["document_id"] = document_id

    # Add session_id if provided
    if session_id:
        payload["session_id"] = session_id

    print(f"\n📝 REQUEST DETAILS:")
    print("-" * 80)
    print(f"Query: {query}")
    if document_id:
        print(f"Document ID: {document_id}")
    if session_id:
        print(f"Session ID: {session_id}")

    # Send request to RAG chat endpoint
    try:
        print(f"\nSending request to {base_url}/api/rag-chat...")
        start_time = time.time()

        response = requests.post(
            f"{base_url}/api/rag-chat",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            rag_response = result.get('response', '')
            sources = result.get('sources', [])

            print(f"\n✅ Response generated successfully in {duration:.2f} seconds!")
            print("\n📄 SOURCES RETRIEVED:")
            print("-" * 80)
            for i, source in enumerate(sources):
                print(f"{i+1}. {source.get('title')} (ID: {source.get('id')})")
                print(f"   Relevance: {source.get('relevance', 0):.4f}")
                snippet = source.get('snippet', '')
                print(f"   Snippet: {snippet[:100]}..." if len(snippet) > 100 else f"   Snippet: {snippet}")
                print()

            print("\n🤖 AI RESPONSE:")
            print("-" * 80)
            print(rag_response)
            print("-" * 80)

            # Save the result to a file
            output_dir = os.path.dirname(os.path.abspath(__file__))
            output_file = os.path.join(output_dir, f"rag_chat_result_{int(time.time())}.json")
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"\nFull result saved to {output_file}")

            return True

        else:
            print(f"\n❌ Request failed with status code: {response.status_code}")
            print("Response content:")
            pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
            return False

    except Exception as e:
        print(f"\n❌ Error during RAG chat: {str(e)}")
        return False

def test_conversation():
    """Test a multi-turn conversation using RAG chat"""
    print("\n" + "=" * 80)
    print(f"🔄 TESTING MULTI-TURN CONVERSATION")
    print("=" * 80)

    # Flask app base URL
    base_url = 'http://localhost:5000'

    # Prepare conversation
    conversation = [
        {
            "query": "What topics are covered in these documents?",
            "role": "user",
            "content": "What topics are covered in these documents?"
        }
    ]

    # Loop through conversation turns
    for i in range(2):  # 2 turns of conversation
        if i > 0:
            # Ask a follow-up question
            conversation.append({
                "query": "Can you explain more about the most important concept?",
                "role": "user",
                "content": "Can you explain more about the most important concept?"
            })

        current_query = conversation[-1]["query"]

        # Format history for the API
        history = []
        for j in range(len(conversation) - 1):
            msg = conversation[j]
            if j % 2 == 0:  # User message
                history.append({"role": "user", "content": msg["content"]})
            else:  # Assistant message
                history.append({"role": "assistant", "content": msg["content"]})

        # Construct payload
        payload = {
            "query": current_query,
            "history": history
        }

        print(f"\n💬 CONVERSATION TURN {i+1}")
        print(f"Query: {current_query}")

        try:
            response = requests.post(
                f"{base_url}/api/rag-chat",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()
                rag_response = result.get('response', '')

                # Add assistant's response to conversation
                conversation.append({
                    "role": "assistant",
                    "content": rag_response
                })

                print("\n🤖 ASSISTANT:")
                print("-" * 80)
                print(rag_response)
                print("-" * 80)

            else:
                print(f"\n❌ Request failed with status code: {response.status_code}")
                print("Response content:")
                pprint(response.json() if response.headers.get('content-type') == 'application/json' else response.text)
                break

        except Exception as e:
            print(f"\n❌ Error during conversation: {str(e)}")
            break

    # Save the conversation to a file
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, f"rag_conversation_{int(time.time())}.json")
    with open(output_file, 'w') as f:
        json.dump(conversation, f, indent=2)

    print(f"\nFull conversation saved to {output_file}")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test RAG chat functionality')
    parser.add_argument('--query', help='Question to ask about the documents')
    parser.add_argument('--document_id', help='Optional document ID to filter search')
    parser.add_argument('--session_id', help='Optional session ID to filter search')
    parser.add_argument('--conversation', action='store_true', help='Test a multi-turn conversation')

    args = parser.parse_args()

    if args.conversation:
        # Test a multi-turn conversation
        test_conversation()
    else:
        # Test a single query
        test_rag_chat(args.query, args.document_id, args.session_id)

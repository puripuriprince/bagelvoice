import uuid
import time
import json
import os
from datetime import datetime
from config import SESSION_EXPIRY

class SessionManager:
    """
    Manages user sessions for the notebook application.
    Handles session creation, retrieval, and expiration.
    """
    def __init__(self, session_dir='sessions'):
        self.session_dir = session_dir
        self.sessions = {}  # In-memory cache of sessions

        # Create sessions directory if it doesn't exist
        os.makedirs(session_dir, exist_ok=True)

        # Load existing sessions
        self._load_sessions()

    def _load_sessions(self):
        """Load existing sessions from disk"""
        for filename in os.listdir(self.session_dir):
            if filename.endswith('.json'):
                try:
                    session_id = filename[:-5]  # Remove .json extension
                    with open(os.path.join(self.session_dir, filename), 'r') as f:
                        session_data = json.load(f)

                    # Skip expired sessions
                    if self._is_expired(session_data):
                        continue

                    self.sessions[session_id] = session_data
                except Exception as e:
                    print(f"Error loading session {filename}: {e}")

    def _is_expired(self, session_data):
        """Check if a session is expired"""
        last_active = session_data.get('last_active', 0)
        return (time.time() - last_active) > SESSION_EXPIRY

    def _save_session(self, session_id):
        """Save a session to disk"""
        if session_id in self.sessions:
            session_path = os.path.join(self.session_dir, f"{session_id}.json")
            try:
                with open(session_path, 'w') as f:
                    json.dump(self.sessions[session_id], f)
            except Exception as e:
                print(f"Error saving session {session_id}: {e}")

    def create_session(self, user_info=None):
        """
        Create a new session.

        Args:
            user_info (dict, optional): User information to store with the session

        Returns:
            str: The new session ID
        """
        session_id = str(uuid.uuid4())

        # Create the session object
        self.sessions[session_id] = {
            'session_id': session_id,
            'created_at': time.time(),
            'last_active': time.time(),
            'user_info': user_info or {},
            'document_ids': [],
            'conversation': []
        }

        # Save to disk
        self._save_session(session_id)

        return session_id

    def get_session(self, session_id):
        """
        Get a session by ID.

        Args:
            session_id (str): The session ID

        Returns:
            dict: The session data or None if not found or expired
        """
        session = self.sessions.get(session_id)

        if session and self._is_expired(session):
            # Remove expired session
            self.delete_session(session_id)
            return None

        if session:
            # Update last active time
            session['last_active'] = time.time()
            self._save_session(session_id)

        return session

    def update_session(self, session_id, update_data):
        """
        Update a session with new data.

        Args:
            session_id (str): The session ID
            update_data (dict): New data to update in the session

        Returns:
            bool: True if updated successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # Update session data
        for key, value in update_data.items():
            if key != 'session_id' and key != 'created_at':
                session[key] = value

        # Update last active time
        session['last_active'] = time.time()

        # Save to disk
        self._save_session(session_id)

        return True

    def add_document_to_session(self, session_id, doc_id):
        """
        Add a document ID to a session.

        Args:
            session_id (str): The session ID
            doc_id (str): The document ID to add

        Returns:
            bool: True if added successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False

        if 'document_ids' not in session:
            session['document_ids'] = []

        if doc_id not in session['document_ids']:
            session['document_ids'].append(doc_id)

        # Save to disk
        self._save_session(session_id)

        return True

    def add_message_to_conversation(self, session_id, role, content, metadata=None):
        """
        Add a message to the session conversation history.

        Args:
            session_id (str): The session ID
            role (str): The role of the message sender (user/assistant)
            content (str): The message content
            metadata (dict, optional): Additional metadata for the message

        Returns:
            bool: True if added successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False

        if 'conversation' not in session:
            session['conversation'] = []

        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
        }

        if metadata:
            message['metadata'] = metadata

        session['conversation'].append(message)

        # Save to disk
        self._save_session(session_id)

        return True

    def get_conversation(self, session_id, limit=None):
        """
        Get the conversation history for a session.

        Args:
            session_id (str): The session ID
            limit (int, optional): Maximum number of messages to return

        Returns:
            list: The conversation messages or empty list if not found
        """
        session = self.get_session(session_id)
        if not session or 'conversation' not in session:
            return []

        conversation = session['conversation']

        if limit and limit > 0:
            conversation = conversation[-limit:]

        return conversation

    def format_for_cohere(self, session_id, limit=None):
        """
        Format the conversation history for Cohere's chat API.

        Args:
            session_id (str): The session ID
            limit (int, optional): Maximum number of messages to include

        Returns:
            list: Formatted conversation history for Cohere
        """
        conversation = self.get_conversation(session_id, limit)

        cohere_messages = []
        for msg in conversation:
            cohere_msg = {
                'role': msg['role'],
                'content': msg['content']
            }

            # Add any citations or additional data if present
            if 'metadata' in msg and 'citations' in msg['metadata']:
                cohere_msg['citations'] = msg['metadata']['citations']

            cohere_messages.append(cohere_msg)

        return cohere_messages

    def delete_session(self, session_id):
        """
        Delete a session.

        Args:
            session_id (str): The session ID

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if session_id in self.sessions:
            # Remove from memory
            del self.sessions[session_id]

            # Remove from disk
            session_path = os.path.join(self.session_dir, f"{session_id}.json")
            if os.path.exists(session_path):
                try:
                    os.remove(session_path)
                    return True
                except Exception as e:
                    print(f"Error deleting session file {session_id}: {e}")
                    return False
            return True

        return False

    def clean_expired_sessions(self):
        """
        Clean up expired sessions.

        Returns:
            int: Number of sessions cleaned up
        """
        expired_count = 0
        session_ids = list(self.sessions.keys())

        for session_id in session_ids:
            if self._is_expired(self.sessions[session_id]):
                self.delete_session(session_id)
                expired_count += 1

        return expired_count

# Test functionality if this file is run directly
if __name__ == "__main__":
    import os
    import sys
    import tempfile

    print("\n===== Manual Testing for SessionManager =====")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize session manager with temp directory
        manager = SessionManager(session_dir=temp_dir)
        print(f"Session manager initialized with directory: {temp_dir}")

        # Keep track of created sessions
        test_sessions = {}

        # Menu for interactive testing
        while True:
            print("\nChoose a test option:")
            print("1. Create a new session")
            print("2. Get session information")
            print("3. Update session data")
            print("4. Add document to session")
            print("5. Add message to conversation")
            print("6. Get conversation history")
            print("7. Format conversation for Cohere")
            print("8. Delete a session")
            print("9. Clean expired sessions")
            print("l. List all active sessions")
            print("q. Quit")

            choice = input("\nEnter your choice: ").strip().lower()

            if choice == 'q':
                break

            elif choice == '1':
                # Create a new session
                print("\n----- Creating New Session -----")

                name = input("Enter user name (or press Enter for default): ") or "Test User"
                email = input("Enter email (optional): ") or "test@example.com"
                topic = input("Enter session topic (optional): ") or "Test Session"

                user_info = {
                    "name": name,
                    "email": email,
                    "topic": topic
                }

                session_id = manager.create_session(user_info)
                test_sessions[session_id] = user_info

                print(f"Session created successfully!")
                print(f"Session ID: {session_id}")

            elif choice == '2':
                # Get session information
                print("\n----- Getting Session Information -----")

                if not test_sessions:
                    print("No sessions created yet. Create a session first.")
                    continue

                print("Available sessions:")
                for i, (sid, info) in enumerate(test_sessions.items()):
                    print(f"{i+1}. {sid[:8]}... - {info.get('name')} - {info.get('topic')}")

                session_choice = input("Enter session number or ID: ")

                try:
                    if session_choice.isdigit() and 1 <= int(session_choice) <= len(test_sessions):
                        session_id = list(test_sessions.keys())[int(session_choice) - 1]
                    else:
                        session_id = session_choice

                    session_data = manager.get_session(session_id)

                    if session_data:
                        print("\nSession information:")
                        print(f"ID: {session_data.get('session_id')}")
                        print(f"Created: {session_data.get('created_at')}")
                        print(f"Last active: {session_data.get('last_active')}")
                        print(f"User info: {session_data.get('user_info')}")
                        print(f"Document count: {len(session_data.get('document_ids', []))}")
                        print(f"Conversation length: {len(session_data.get('conversation', []))}")
                    else:
                        print(f"Session not found or expired: {session_id}")

                except (ValueError, IndexError) as e:
                    print(f"Error: {e}")

            elif choice == '3':
                # Update session data
                print("\n----- Updating Session Data -----")

                if not test_sessions:
                    print("No sessions created yet. Create a session first.")
                    continue

                print("Available sessions:")
                for i, (sid, info) in enumerate(test_sessions.items()):
                    print(f"{i+1}. {sid[:8]}... - {info.get('name')} - {info.get('topic')}")

                session_choice = input("Enter session number or ID: ")

                try:
                    if session_choice.isdigit() and 1 <= int(session_choice) <= len(test_sessions):
                        session_id = list(test_sessions.keys())[int(session_choice) - 1]
                    else:
                        session_id = session_choice

                    # Get update fields
                    field_name = input("Enter field to update (e.g., user_info.name): ")
                    new_value = input("Enter new value: ")

                    # Parse the field name (e.g., user_info.name)
                    update_data = {}
                    if '.' in field_name:
                        main_field, sub_field = field_name.split('.', 1)

                        # Get the existing data first
                        session_data = manager.get_session(session_id)
                        if not session_data:
                            print(f"Session not found: {session_id}")
                            continue

                        # Create a copy of the nested object
                        nested_obj = session_data.get(main_field, {}).copy()
                        nested_obj[sub_field] = new_value
                        update_data[main_field] = nested_obj
                    else:
                        update_data[field_name] = new_value

                    # Update the session
                    success = manager.update_session(session_id, update_data)

                    if success:
                        print(f"Session updated successfully")
                        # Update local cache
                        if 'user_info' in update_data and session_id in test_sessions:
                            test_sessions[session_id] = update_data['user_info']
                    else:
                        print(f"Failed to update session: {session_id}")

                except (ValueError, IndexError) as e:
                    print(f"Error: {e}")

            elif choice == '4':
                # Add document to session
                print("\n----- Adding Document to Session -----")

                if not test_sessions:
                    print("No sessions created yet. Create a session first.")
                    continue

                print("Available sessions:")
                for i, (sid, info) in enumerate(test_sessions.items()):
                    print(f"{i+1}. {sid[:8]}... - {info.get('name')} - {info.get('topic')}")

                session_choice = input("Enter session number or ID: ")

                try:
                    if session_choice.isdigit() and 1 <= int(session_choice) <= len(test_sessions):
                        session_id = list(test_sessions.keys())[int(session_choice) - 1]
                    else:
                        session_id = session_choice

                    doc_id = input("Enter document ID: ") or f"test_doc_{int(time.time())}"

                    success = manager.add_document_to_session(session_id, doc_id)

                    if success:
                        print(f"Document {doc_id} added to session successfully")
                    else:
                        print(f"Failed to add document to session: {session_id}")

                except (ValueError, IndexError) as e:
                    print(f"Error: {e}")

            elif choice == '5':
                # Add message to conversation
                print("\n----- Adding Message to Conversation -----")

                if not test_sessions:
                    print("No sessions created yet. Create a session first.")
                    continue

                print("Available sessions:")
                for i, (sid, info) in enumerate(test_sessions.items()):
                    print(f"{i+1}. {sid[:8]}... - {info.get('name')} - {info.get('topic')}")

                session_choice = input("Enter session number or ID: ")

                try:
                    if session_choice.isdigit() and 1 <= int(session_choice) <= len(test_sessions):
                        session_id = list(test_sessions.keys())[int(session_choice) - 1]
                    else:
                        session_id = session_choice

                    role = input("Enter message role (user/assistant): ") or "user"
                    content = input("Enter message content: ") or "This is a test message."

                    metadata = None
                    has_metadata = input("Add metadata? (y/n): ").lower() == 'y'
                    if has_metadata:
                        citations = input("Enter comma-separated citation texts: ")
                        if citations:
                            citation_texts = [text.strip() for text in citations.split(',')]
                            metadata = {
                                "citations": [
                                    {"text": text, "start": 0, "end": len(text), "sources": []}
                                    for text in citation_texts
                                ]
                            }

                    success = manager.add_message_to_conversation(session_id, role, content, metadata)

                    if success:
                        print(f"Message added to conversation successfully")
                    else:
                        print(f"Failed to add message to session: {session_id}")

                except (ValueError, IndexError) as e:
                    print(f"Error: {e}")

            elif choice == '6':
                # Get conversation history
                print("\n----- Getting Conversation History -----")

                if not test_sessions:
                    print("No sessions created yet. Create a session first.")
                    continue

                print("Available sessions:")
                for i, (sid, info) in enumerate(test_sessions.items()):
                    print(f"{i+1}. {sid[:8]}... - {info.get('name')} - {info.get('topic')}")

                session_choice = input("Enter session number or ID: ")

                try:
                    if session_choice.isdigit() and 1 <= int(session_choice) <= len(test_sessions):
                        session_id = list(test_sessions.keys())[int(session_choice) - 1]
                    else:
                        session_id = session_choice

                    limit_str = input("Enter message limit (or press Enter for all): ")
                    limit = int(limit_str) if limit_str.isdigit() else None

                    conversation = manager.get_conversation(session_id, limit)

                    print(f"\nConversation history ({len(conversation)} messages):")
                    for i, msg in enumerate(conversation):
                        print(f"{i+1}. {msg['role']}: {msg['content'][:50]}..." +
                              f" ({msg.get('timestamp', 'unknown time')})")

                except (ValueError, IndexError) as e:
                    print(f"Error: {e}")

            elif choice == '7':
                # Format for Cohere
                print("\n----- Formatting Conversation for Cohere -----")

                if not test_sessions:
                    print("No sessions created yet. Create a session first.")
                    continue

                print("Available sessions:")
                for i, (sid, info) in enumerate(test_sessions.items()):
                    print(f"{i+1}. {sid[:8]}... - {info.get('name')} - {info.get('topic')}")

                session_choice = input("Enter session number or ID: ")

                try:
                    if session_choice.isdigit() and 1 <= int(session_choice) <= len(test_sessions):
                        session_id = list(test_sessions.keys())[int(session_choice) - 1]
                    else:
                        session_id = session_choice

                    cohere_format = manager.format_for_cohere(session_id)

                    print(f"\nCohere formatted conversation ({len(cohere_format)} messages):")
                    for i, msg in enumerate(cohere_format):
                        print(f"{i+1}. {msg['role']}: {msg['content'][:50]}...")
                        if 'citations' in msg:
                            print(f"   Has {len(msg['citations'])} citations")

                except (ValueError, IndexError) as e:
                    print(f"Error: {e}")

            elif choice == '8':
                # Delete a session
                print("\n----- Deleting Session -----")

                if not test_sessions:
                    print("No sessions created yet. Create a session first.")
                    continue

                print("Available sessions:")
                for i, (sid, info) in enumerate(test_sessions.items()):
                    print(f"{i+1}. {sid[:8]}... - {info.get('name')} - {info.get('topic')}")

                session_choice = input("Enter session number or ID: ")

                try:
                    if session_choice.isdigit() and 1 <= int(session_choice) <= len(test_sessions):
                        session_id = list(test_sessions.keys())[int(session_choice) - 1]
                    else:
                        session_id = session_choice

                    confirm = input(f"Are you sure you want to delete session {session_id}? (y/n): ")

                    if confirm.lower() == 'y':
                        success = manager.delete_session(session_id)

                        if success:
                            print(f"Session deleted successfully")
                            if session_id in test_sessions:
                                del test_sessions[session_id]
                        else:
                            print(f"Failed to delete session: {session_id}")

                except (ValueError, IndexError) as e:
                    print(f"Error: {e}")

            elif choice == '9':
                # Clean expired sessions
                print("\n----- Cleaning Expired Sessions -----")

                count = manager.clean_expired_sessions()
                print(f"Cleaned {count} expired sessions")

            elif choice == 'l':
                # List all sessions
                print("\n----- Active Sessions -----")

                if test_sessions:
                    print("Sessions created in this test run:")
                    for i, (sid, info) in enumerate(test_sessions.items()):
                        print(f"{i+1}. {sid} - {info.get('name')} - {info.get('topic')}")
                else:
                    print("No sessions created in this test run")

                print("\nAll sessions in manager:")
                if manager.sessions:
                    for i, (sid, data) in enumerate(manager.sessions.items()):
                        user_info = data.get('user_info', {})
                        print(f"{i+1}. {sid} - {user_info.get('name', 'Unknown')} - " +
                              f"{user_info.get('topic', 'No topic')}")
                else:
                    print("No active sessions found")

            else:
                print("Invalid choice. Please try again.")

        print("\nTesting complete!")

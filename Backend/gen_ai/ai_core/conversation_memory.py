import uuid

class Conversation:
    def __init__(self):
        """Initialize a new Conversation instance."""
        self.conversation_history = []
        self.conversation_id = None

    def start_conversation(self):
        """Start a new conversation."""
        self.conversation_history = []
        self.conversation_id = str(uuid.uuid4())
        return self.conversation_id

    def get_conversation_id(self):
        return self.conversation_id

    def add_message(self, role, content, name=None):
        """Add a message to the conversation."""
        if content is None:
            return
        if name is not None:
            self.conversation_history.append(
                {"role": role, "content": content, "name": name}
            )
        else:
            self.conversation_history.append({"role": role, "content": content})

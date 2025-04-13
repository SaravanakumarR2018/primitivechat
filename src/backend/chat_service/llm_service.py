import os
import sys
import logging
from collections import OrderedDict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_models import ChatOllama
from langchain_core.runnables import RunnableLambda
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory


# Default log format (can be overridden later)
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configure logging
logging.basicConfig(level=logging.DEBUG, format=log_format)
logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, max_conversations=200, buffer_size=30):
        logger.info("Initializing LLMService")

        # Read host and port from environment variables
        ollama_host = os.getenv("OLLAMA_HOST")
        ollama_port = os.getenv("OLLAMA_PORT")
        model_name = os.getenv("OLLAMA_MODEL")

        if not ollama_host or not ollama_port or not model_name:
            logger.error("Environment variables OLLAMA_HOST, OLLAMA_PORT, and OLLAMA_MODEL must be set.")
            raise ValueError("Missing required environment variables.")

        try:
            self.llm = ChatOllama(
                model=model_name,
                base_url=f"http://{ollama_host}:{ollama_port}",
                temperature=0.7
            )
            logger.info("ChatOllama initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatOllama: {e}")
            raise RuntimeError(f"Failed to initialize ChatOllama: {e}")

        self.max_conversations = max_conversations
        self.buffer_size = buffer_size
        self.histories = OrderedDict()

    def _evict_if_needed(self):
        while len(self.histories) > self.max_conversations:
            oldest_key, _ = self.histories.popitem(last=False)
            logger.info(f"Evicted LRU conversation: {oldest_key}")

    def get_or_create_history(self, session_id):
        if session_id not in self.histories:
            history = ConversationBufferWindowMemory(k=self.buffer_size)
            history.chat_memory.add_message(SystemMessage(content="You are a helpful assistant."))
            self.histories[session_id] = history
            self._evict_if_needed()
            logger.info(f"New buffered conversation history created for session_id: {session_id}")
        else:
            self.histories.move_to_end(session_id)
        return self.histories[session_id]

    def get_response(self, question, user_id, customer_guid, chat_id):
        session_id = f"{user_id}:{customer_guid}:{chat_id}"
        
        # Get or create the conversation history
        history = self.get_or_create_history(session_id)
        
        # Add the user message to history
        history.chat_memory.add_message(HumanMessage(content=question))
        
        # Get all messages from history
        messages = history.chat_memory.messages        
        # Generate response
        response = self.llm.invoke(messages)
        
        # Add the assistant's response to history
        history.chat_memory.add_message(AIMessage(content=response.content))
        
        return response

    def get_conversation_history(self, user_id, customer_guid, chat_id):
        session_id = f"{user_id}:{customer_guid}:{chat_id}"
        return self.histories.get(session_id)


# ---------------------------
# Interactive CLI Chat
# ---------------------------
if __name__ == "__main__":
    try:
        # Override log format specifically for CLI usage
        log_format = "%(asctime)s - [MAIN] - %(levelname)s - %(message)s"
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(level=logging.DEBUG, format=log_format)

        os.environ.setdefault("OLLAMA_HOST", "host.docker.internal")
        os.environ.setdefault("OLLAMA_PORT", "11434")
        os.environ.setdefault("OLLAMA_MODEL", "llama3.2:3b")

        service = LLMService()
        user_id, customer_guid, chat_id = "cli_user", "cli_customer", "cli_chat"

        print("\n🤖 Chatbot is ready! Type your message below.")
        print("Type 'exit' or 'quit' to stop.\n")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break

            response = service.get_response(user_input, user_id, customer_guid, chat_id)
            print(f"Assistant: {response.content}\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

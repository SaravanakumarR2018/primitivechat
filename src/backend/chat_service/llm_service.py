import os
import logging
from collections import OrderedDict
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_models import ChatOllama
from src.backend.db.database_manager import DatabaseManager, SenderType
from src.backend.lib.logging_config import log_format
from pydantic import BaseModel
from src.backend.lib.default_ai_response import DEFAULTAIRESPONSE

# Configure logging
logging.basicConfig(level=logging.DEBUG, format=log_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

db_manager = DatabaseManager()

class LLMService:
    """
    Service to manage interactions with the LLM and maintain conversation history.
    """
    llm_response = "NONLLM"  # Static variable to toggle response mode
    max_conversations = 200
    buffer_size = 32
    histories = OrderedDict()
    llm = None

    def __init__(self, max_conversations=200, buffer_size=32):
        logger.info("Initializing LLMService")
        LLMService.max_conversations = max_conversations
        LLMService.buffer_size = buffer_size

        # Initialize ChatOllama
        ollama_host = os.getenv("OLLAMA_HOST")
        ollama_port = os.getenv("OLLAMA_PORT")
        model_name = os.getenv("OLLAMA_MODEL")

        if not ollama_host or not ollama_port or not model_name:
            logger.error("Environment variables OLLAMA_HOST, OLLAMA_PORT, and OLLAMA_MODEL must be set.")
            raise ValueError("Missing required environment variables.")

        try:
            LLMService.llm = ChatOllama(
                model=model_name,
                base_url=f"http://{ollama_host}:{ollama_port}",
                temperature=0.7
            )
            logger.info("ChatOllama initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatOllama: {e}")
            raise RuntimeError(f"Failed to initialize ChatOllama: {e}")

    @classmethod
    def set_llm_response(cls, mode):
        if mode not in ["NONLLM", "LLM"]:
            raise ValueError("Invalid mode. Use 'NONLLM' or 'LLM'.")
        cls.llm_response = mode
        logger.info(f"LLM response mode set to: {cls.llm_response}")

    @classmethod
    def get_llm_response(cls):
        return cls.llm_response

    def _evict_if_needed(self):
        while len(LLMService.histories) > LLMService.max_conversations:
            oldest_key, _ = LLMService.histories.popitem(last=False)
            logger.debug(f"Evicted LRU conversation: {oldest_key}")

    def get_or_create_history(self, session_id, user_id, customer_guid, chat_id):
        logger.debug(f"Getting or creating history for session_id: {session_id}")
        if session_id not in LLMService.histories:
            logger.debug(f"[NEW] Creating new history for session_id: {session_id}")
            history = ConversationBufferWindowMemory(k=self.buffer_size)
            history.chat_memory.add_message(SystemMessage(content="You are a helpful assistant."))

            # Fetch messages from the database
            messages = db_manager.get_paginated_chat_messages(customer_guid, chat_id, page=1, page_size=self.buffer_size * 3)
            
            messages.sort(key=lambda msg: msg['timestamp'])
            logger.debug(f"DB Messages: {messages}")

            # Add messages to chat memory
            for msg in messages:
                if msg['sender_type'] == SenderType.CUSTOMER.value:
                    history.chat_memory.add_message(HumanMessage(content=msg['message']))
                elif msg['sender_type'] == SenderType.SYSTEM.value:
                    history.chat_memory.add_message(AIMessage(content=msg['message']))

            LLMService.histories[session_id] = history
            self._evict_if_needed()
            logger.debug("New buffered conversation history created for session_id: %s", session_id)  # Fixed logging
        else:
            logger.debug(f"[SKIP] Session {session_id} already exists in memory.")
            LLMService.histories.move_to_end(session_id)
        return LLMService.histories[session_id]

    async def get_response(self, question, user_id, customer_guid, chat_id) -> AsyncGenerator[dict, None]:
        session_id = f"{user_id}:{customer_guid}:{chat_id}"
        history = self.get_or_create_history(session_id, user_id, customer_guid, chat_id)

        if not (history.chat_memory.messages and
                isinstance(history.chat_memory.messages[-1], HumanMessage) and
                history.chat_memory.messages[-1].content == question):
            history.chat_memory.add_message(HumanMessage(content=question))

        llm_response_mode = LLMService.get_llm_response()
        if llm_response_mode == "NONLLM":
            response_content = DEFAULTAIRESPONSE
            logger.debug("LLM_RESPONSE set to NONLLM. Returning default response for session_id: %s", session_id)
            response = AIMessage(content=response_content)
            history.chat_memory.add_message(response)
            yield {
                "chat_id": chat_id,
                "customer_guid": customer_guid,
                "user_id": user_id,
                "object": "chat.completion",
                "choices": [
                    {
                        "delta": {
                            "role": "assistant",
                            "content": response_content
                        },
                        "index": 0,
                        "finish_reason": "stop"
                    }
                ]
            }
        else:
            messages = history.chat_memory.messages
            logger.debug(f"Messages: {messages}")
            first_chunk = True
            full_content = ""

            async for chunk in LLMService.llm.astream(messages):
                content_piece = chunk.message.content if hasattr(chunk, "message") else chunk.content
                if not content_piece:
                    continue

                full_content += content_piece

                yield {
                    "chat_id": chat_id,
                    "customer_guid": customer_guid,
                    "user_id": user_id,
                    "object": "chat.completion",
                    "choices": [
                        {
                            "delta": {
                                "role": "assistant" if first_chunk else None,
                                "content": content_piece
                            },
                            "index": 0,
                            "finish_reason": None
                        }
                    ]
                }

                first_chunk = False

            history.chat_memory.add_message(AIMessage(content=full_content))

            # Final stop chunk
            yield {
                "chat_id": chat_id,
                "customer_guid": customer_guid,
                "user_id": user_id,
                "object": "chat.completion",
                "choices": [
                    {
                        "delta": {
                            "role": "assistant",
                            "content": ""
                        },
                        "index": 0,
                        "finish_reason": "stop"
                    }
                ]
            }

    def get_conversation_history(self, user_id, customer_guid, chat_id):
        session_id = f"{user_id}:{customer_guid}:{chat_id}"
        return LLMService.histories.get(session_id)
    
    def clear_histories(self):
        """
        Clear all conversation histories.
        """
        LLMService.histories.clear()
        logger.info("All conversation histories have been cleared.")


# FastAPI Router
app = APIRouter()

llm_service = LLMService()

class LLMModeRequest(BaseModel):
    mode: str  # Expected values: "usellm" or "nousellm"

@app.get("/get_llm_response_mode", tags=["LLM Management"])
async def get_llm_response_mode():
    """
    Get the current LLM response mode.
    """
    logger.debug("Entering get_llm_response_mode()")
    try:
        mode = LLMService.get_llm_response()
        return {"llm_response_mode": mode}
    except Exception as e:
        logger.error(f"Unexpected error in get_llm_response_mode(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    

@app.post("/clear_histories", tags=["LLM Management"])
async def clear_histories():
    """
    Clear all conversation histories stored in the LLMService.
    """
    logger.debug("Entering clear_histories()")
    try:
        llm_service.clear_histories()
        return {"message": "All conversation histories have been cleared."}
    except Exception as e:
        logger.error(f"Unexpected error in clear_histories(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while clearing histories.")

class LLMModeRequest(BaseModel):
    use_llm: bool  # Boolean to indicate whether to use LLM or not

@app.post("/use_llm_response", tags=["LLM Management"])
async def use_llm_response(request: LLMModeRequest):
    """
    Set the LLM response mode using a boolean value.
    - `true` to enable LLM responses.
    - `false` to disable LLM responses.
    """
    logger.debug("Entering use_llm_response() with use_llm: %s", request.use_llm)
    try:
        if request.use_llm:
            LLMService.set_llm_response("LLM")
            return {"message": "LLM response mode enabled"}
        else:
            LLMService.set_llm_response("NONLLM")
            return {"message": "LLM response mode disabled"}
    except Exception as e:
        logger.error(f"Unexpected error in use_llm_response(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/chat_unauth", tags=["Chat Management"])
async def chat_unauth(
    customer_guid: str,
    user_id: str,
    question: str,
    chat_id: Optional[str] = None
):
    """
    Unauthenticated chat endpoint where customer_guid, user_id, question are required, and chat_id is optional.
    """
    logger.debug(f"Entering chat_unauth() with customer_guid: {customer_guid}, chat_id: {chat_id}, user_id: {user_id}")
    try:
        # Validate inputs
        if not customer_guid or not user_id or not question:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        # Add user message to the database
        user_response = db_manager.add_message(
            user_id, customer_guid, question, sender_type=SenderType.CUSTOMER, chat_id=chat_id
        )

        # Ensure user_response is a dictionary and contains 'chat_id'
        if not isinstance(user_response, dict) or 'chat_id' not in user_response:
            logger.error(f"Invalid response from add_message: {user_response}")
            raise HTTPException(status_code=500, detail="Failed to add user message")
        
        # Get system response from LLMService
        system_response = llm_service.get_response(
            question=question,
            user_id=user_id,
            customer_guid=customer_guid,
            chat_id=user_response['chat_id']
        )

        # Ensure system_response has a 'content' attribute
        if not hasattr(system_response, 'content'):
            logger.error(f"Invalid response from get_response: {system_response}")
            raise HTTPException(status_code=500, detail="Failed to generate system response")

        # Add system response to the database
        system_response_result = db_manager.add_message(
            user_id, customer_guid, system_response.content, sender_type=SenderType.SYSTEM, chat_id=user_response['chat_id']
        )

        # Log if the system message was not added successfully
        if 'error' in system_response_result:
            logger.error(f"Error in adding system message: {system_response_result['error']}")

        logger.debug(f"Exiting chat_unauth() with customer_guid: {customer_guid}, chat_id: {chat_id}, user_id: {user_id}")
        return {
            "chat_id": user_response['chat_id'],
            "customer_guid": customer_guid,
            "user_id": user_id,
            "answer": system_response.content
        }
    except HTTPException as e:
        logger.error(f"HTTPException in chat_unauth(): {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in chat_unauth(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during chat processing")

# ---------------------------
# Interactive CLI Chat
# ---------------------------
if __name__ == "__main__":
    try:
        log_format = "%(asctime)s - [MAIN] - %(levelname)s - %(message)s"
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

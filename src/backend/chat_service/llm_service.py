import os
import logging
import httpx

from collections import OrderedDict
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from src.backend.db.database_manager import DatabaseManager, SenderType
from src.backend.lib.logging_config import get_primitivechat_logger
from pydantic import BaseModel
from src.backend.lib.default_ai_response import DEFAULTAIRESPONSE

from src.backend.lib.singleton_class import Singleton

from fastapi import Request
from pathlib import Path

# Configure logging
logger = get_primitivechat_logger(__name__)

db_manager = DatabaseManager()


class LLMService(metaclass=Singleton):
=======
# ---------------------------------------
# Add these HTTPX logging hooks below your imports
# ---------------------------------------
def _log_request(request: httpx.Request):
    logger.debug(f"HTTPX Request ▶ {request.method} {request.url}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    if request.content:
        try:
            logger.debug(f"Request body: {request.content.decode()}")
        except Exception:
            logger.debug(f"Request body (bytes): {request.content}")

def _log_response(response: httpx.Response):
    logger.debug(f"HTTPX Response ◀ {response.status_code} {response.url}")
    logger.debug(f"Response headers: {dict(response.headers)}")
    logger.debug(f"Response body: {response.text}")
    return response

class LLMService:

    """
    Service to manage interactions with the LLM and maintain conversation history.
    """
    llm_response = "NONLLM"  # Static variable to toggle response mode
    max_conversations = 200
    buffer_size = 32
    histories = OrderedDict()
    llm = None
    LLMProvider = "OLLAMA"  # Default provider
    model = os.getenv("OLLAMA_MODEL")  # Default model name

    def __init__(self, max_conversations=200, buffer_size=32):
        logger.info("Initializing LLMService")
        LLMService.max_conversations = max_conversations
        LLMService.buffer_size = buffer_size

        # Initialize LLM
        LLMService.llm = self._initialize_llm(LLMService.LLMProvider, LLMService.model)

    def _initialize_llm(self, provider, model_name):
        """
        Initialize the LLM based on the given provider and model.
        Returns the initialized LLM object or raises an exception if initialization fails.
        """
        if provider == "OLLAMA":
            return self._initialize_ollama(model_name)
        elif provider == "KRUTRIM":
            return self._initialize_krutrim(model_name)
        elif provider == "GEMINI":
            return self._initialize_gemini(model_name)
        elif provider == "OPENAI":
            return self._initialize_openai(model_name)
        else:
            logger.error(f"Unsupported LLM provider: {provider}")
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
   
    def _initialize_ollama(self, model_name):
        ollama_host = os.getenv("OLLAMA_HOST")
        ollama_port = os.getenv("OLLAMA_PORT")
        model_name = os.getenv("OLLAMA_MODEL")

        if not ollama_host or not ollama_port or not model_name:
            logger.error("Environment variables OLLAMA_HOST, OLLAMA_PORT, and OLLAMA_MODEL must be set.")
            raise ValueError("Missing required environment variables.")

        try:
            llm = ChatOllama(
                model=model_name,
                base_url=f"http://{ollama_host}:{ollama_port}",
                temperature=0.7
            )
            logger.info("ChatOllama initialized successfully")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize ChatOllama: {e}")
            raise RuntimeError(f"Failed to initialize ChatOllama: {e}")

 # ...existing code...

    def _initialize_openai_llm(self, api_key, model_name, base_url,
                               temperature=None, max_tokens=None, model_kwargs=None):
        """
        Shared initializer for any OpenAI‑compatible ChatOpenAI models.
        """
        if not api_key or not model_name:
            logger.error("API key and model name must be provided.")
            raise ValueError("Missing required credentials for OpenAI LLM.")

        try:
            client = httpx.Client(
                event_hooks={
                    "request": [_log_request],
                },
            )
            init_kwargs = {
                "api_key": api_key,
                "model": model_name,
                "base_url": base_url,
                "http_client": client,
            }
            if temperature is not None:
                init_kwargs["temperature"] = temperature

            llm = ChatOpenAI(**init_kwargs)

            if max_tokens is not None:
                llm.max_tokens = max_tokens
            if model_kwargs:
                llm.model_kwargs = model_kwargs
            
             # ▶️ Validate LLM by sending a dummy "ping"
            try:
                llm([HumanMessage(content="ping")])
                logger.info(f"✅ LLM '{model_name}' endpoint validated at {base_url}")
            except Exception as e:
                logger.error(f"❌ LLM '{model_name}' validation failed: {e}")
                raise RuntimeError(f"LLM validation failed for model '{model_name}': {e}")


            logger.info(f"OpenAI model '{model_name}' initialized at {base_url}")
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {e}")
            raise RuntimeError(f"Failed to initialize OpenAI LLM: {e}")

    def _initialize_openai(self, model_name):
        """
        Initialize OpenAI ChatOpenAI via the shared initializer.
        Reads OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = "https://api.openai.com/v1"
        temperature = 0.7
        max_tokens = 1024

        if not api_key or not model_name:
            logger.error("Environment variables OPENAI_API_KEY and OPENAI_MODEL must be set.")
            raise ValueError("Missing required environment variables for OpenAI.")

        return self._initialize_openai_llm(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            temperature=float(temperature) if temperature else None,
            max_tokens=int(max_tokens) if max_tokens else None
        )
    def _initialize_gemini(self, model_name):
        """
        Delegate Gemini setup to the shared OpenAI initializer.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        return self._initialize_openai_llm(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            max_tokens=1024,
            temperature=0.7
        )

    def _initialize_krutrim(self, model_name):
        """
        Delegate Krutrim setup to the shared OpenAI initializer.
        """
        api_key = os.getenv("KRUTRIM_API_KEY")
        endpoint = "https://cloud.olakrutrim.com/v1"
        krutrim_kwargs = {
            "top_p": 0.7,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["<|eot_id|>", "<|im_start|>", "<|im_end|>"]
        }
        return self._initialize_openai_llm(
            api_key=api_key,
            model_name=model_name,
            base_url=endpoint,
            max_tokens=1024,
            temperature=0.7,
            model_kwargs=krutrim_kwargs
        )

# ...existing code...
    @classmethod
    def set_llm_response(cls, mode):
        if mode not in ["NONLLM", "LLM"]:
            raise ValueError("Invalid mode. Use 'NONLLM' or 'LLM'.")
        cls.llm_response = mode
        logger.info(f"LLM response mode set to: {cls.llm_response}")

    @classmethod
    def get_llm_response(cls):
        return cls.llm_response

    @classmethod
    def set_llm_provider(cls, provider):
        cls.LLMProvider = provider if provider else "OLLAMA"
        logger.info(f"LLM provider set to: {cls.LLMProvider}")

    @classmethod
    def get_llm_provider(cls):
        return cls.LLMProvider

    @classmethod
    def set_model(cls, model_name):
        cls.model = model_name if model_name else os.getenv("OLLAMA_MODEL")
        logger.info(f"Model set to: {cls.model}")

    @classmethod
    def get_model(cls):
        return cls.model

    def _evict_if_needed(self):
        while len(LLMService.histories) > LLMService.max_conversations:
            oldest_key, _ = LLMService.histories.popitem(last=False)
            logger.debug(f"Evicted LRU conversation: {oldest_key}")

    def get_or_create_history(self, session_id, user_id, customer_guid, chat_id):
        logger.debug(f"Getting or creating history for session_id: {session_id}")
        if session_id not in LLMService.histories:
            logger.debug(f"[NEW] Creating new history for session_id: {session_id}")
            history = ConversationBufferWindowMemory(k=self.buffer_size)
            history.chat_memory.add_message(SystemMessage(content="You are a customer support agent. You will be provided context from RAG system to provide answers to user's questions .If there is no context, you can answer from your knowledge. Do not hallucinate. If the user is enabling greetings, then you can talk without context. Make the tone a bit professional. Avoid Inner monologue or first-person thoughts. Keep the <think> tags within 1 or 2 sentences."))

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

    def changing_llm(self, provider, model_name):
        """
        Change the LLM provider and model if they differ from the current ones.
        Initialize the LLM and handle errors if the provider or model is unsupported.
        Raise exceptions for API use.
        """
        if LLMService.LLMProvider == provider and LLMService.model == model_name:
            logger.info("No change in LLM provider or model. No action taken.")
            return

        # Attempt to initialize the LLM with the new provider and model
        try:
            result = self._initialize_llm(provider, model_name)
            LLMService.llm = result
            LLMService.LLMProvider = provider
            LLMService.model = model_name
            logger.info(f"LLM provider and model updated to: {LLMService.LLMProvider}, {LLMService.model}")
        except ValueError as ve:
            logger.error(f"ValueError: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        except RuntimeError as re:
            logger.error(f"RuntimeError: {re}")
            raise HTTPException(status_code=500, detail=str(re))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")


# FastAPI Router
app = APIRouter()

llm_service = LLMService()

class LLMModeRequest(BaseModel):
    use_llm: bool  # Boolean to indicate whether to use LLM or not
    llmprovider: Optional[str] = None  # Optional LLM provider
    model: Optional[str] = None  # Optional model name

@app.get("/get_llm_response_mode", tags=["LLM Management"])
async def get_llm_response_mode():
    """
    Get the current LLM response mode and provider details.
    """
    logger.debug("Entering get_llm_response_mode()")
    try:
        mode = LLMService.get_llm_response()
        return {"llm_response_mode": mode, "llmprovider": LLMService.get_llm_provider(), "model": LLMService.get_model()}
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

@app.post("/use_llm_response", tags=["LLM Management"])
async def use_llm_response(request: LLMModeRequest):
    """
    Set the LLM response mode using a boolean value.
    - `true` to enable LLM responses.
    - `false` to disable LLM responses.
    Optionally specify `llmprovider` and `model`.
    """
    logger.debug("Entering use_llm_response() with use_llm: %s, llmprovider: %s, model: %s", request.use_llm, request.llmprovider, request.model)
    try:
        if request.use_llm:
            llmprovider = request.llmprovider if request.llmprovider else "OLLAMA"  
            model = request.model if request.model else os.getenv("OLLAMA_MODEL")
            logger.debug("Changing LLM provider and model to: %s, %s", llmprovider, model)
            llm_service.changing_llm(llmprovider, model)
            LLMService.set_llm_response("LLM")
            return {"message": "LLM response mode enabled", "llmprovider": LLMService.get_llm_provider(), "model": LLMService.get_model()}
        else:
            LLMService.set_llm_response("NONLLM")
            return {"message": "LLM response mode disabled"}
    except HTTPException as e:
        logger.error(f"HTTPException in use_llm_response(): {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in use_llm_response(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

class LogLevelRequest(BaseModel):
    path_or_filename: str  # The filename or module name
    log_level: str  # The desired log level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)


@app.post("/update_log_level", tags=["Logging Management"])
async def update_log_level(request: LogLevelRequest):
    """
    Update the log level for a specific file, module, or external library.
    If the input matches a filename, it searches for matches in the project directory.
    If the input matches a module name, it updates the module's logger directly.
    """
    logger.debug(f"Entering update_log_level() with path_or_filename: {request.path_or_filename}, log_level: {request.log_level}")
    try:
        # Validate the log level
        log_level = request.log_level.upper()
        if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise HTTPException(status_code=400, detail="Invalid log level. Use DEBUG, INFO, WARNING, ERROR, or CRITICAL.")

        project_root = Path(__file__).parent.parent.parent.parent  # Adjust as needed
        input_path = Path(request.path_or_filename)

        # Check if the input matches an external module
        if request.path_or_filename in logging.Logger.manager.loggerDict:
            external_logger = logging.getLogger(request.path_or_filename)
            external_logger.setLevel(getattr(logging, log_level))
            logger.info(f"Log level for external module '{request.path_or_filename}' updated to {log_level}")
            return {
                "message": f"Log level for external module '{request.path_or_filename}' updated to {log_level}",
                "external_module": request.path_or_filename
            }

        # If not an external module, treat as a file or module path
        if input_path.is_absolute() or "/" in request.path_or_filename or "\\" in request.path_or_filename:
            # Treat as a full path
            full_path = project_root / input_path
            if not full_path.exists():
                raise HTTPException(status_code=404, detail=f"File not found: {request.path_or_filename}")
            matches = [full_path]
        else:
            # Treat as a filename and search for matches
            matches = list(project_root.rglob(request.path_or_filename))

        if not matches:
            raise HTTPException(status_code=404, detail=f"No file or module found matching '{request.path_or_filename}'.")

        if len(matches) > 1:
            # Return conflict error with the list of matches
            conflict_details = [str(match.relative_to(project_root)) for match in matches]
            raise HTTPException(
                status_code=409,
                detail={
                    "message": f"Multiple matches found for '{request.path_or_filename}'.",
                    "conflicts": conflict_details
                }
            )

        # Resolve the single match to a module path
        matched_file = matches[0]
        # Print the matched file path
        logger.info(f"Matched file: {matched_file}")
        module_path = str(matched_file.relative_to(project_root)).replace("/", ".").replace("\\", ".")
        if module_path.endswith(".py"):
            module_path = module_path[:-3]
        # Print the module path
        print(f"Module path: {module_path}")
        # Get the logger for the resolved module path
        target_logger = logging.getLogger(module_path)

        # Update the log level
        target_logger.setLevel(getattr(logging, log_level))
        logger.info(f"Log level for '{module_path}' updated to {log_level}")

        return {
            "message": f"Log level for '{module_path}' updated to {log_level}",
            "matched_file": str(matched_file),
            "module_path": module_path
        }
    except HTTPException as e:
        logger.error(f"HTTPException in update_log_level(): {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in update_log_level(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while updating the log level.")
# ---------------------------
# Interactive CLI Chat
# ---------------------------
if __name__ == "__main__":
    try:

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

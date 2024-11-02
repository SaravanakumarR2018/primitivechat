import logging
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db.database_manager import DatabaseManager  # Assuming the provided code is in database_connector.py
from db.database_manager import SenderType

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow CORS if necessary
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_manager = DatabaseManager()


# Pydantic models for the API inputs
class ChatRequest(BaseModel):
    customer_guid: str
    question: str
    chat_id: str = None


class GetAllChatsRequest(BaseModel):
    customer_guid: str
    chat_id: str
    page: int = 1
    page_size: int = 10


class DeleteChatsRequest(BaseModel):
    customer_guid: str
    chat_id: str


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    logger.info(f"Request received with Correlation ID: {correlation_id}")

    response = await call_next(request)

    # Add correlation ID to response headers
    response.headers['X-Correlation-ID'] = correlation_id
    return response


# API endpoint to add a new customer
@app.post("/addcustomer", tags=["Customer Management"])
async def add_customer(request: Request):
    logger.debug(f"Entering add_customer() with Correlation ID: {request.state.correlation_id}")
    customer_guid = db_manager.add_customer()
    if customer_guid is None:
        logger.error("Failed to create customer")
        raise HTTPException(status_code=500, detail="Failed to create customer")
    logger.debug(f"Exiting add_customer() with Correlation ID: {request.state.correlation_id}")
    return {"customer_guid": customer_guid}


# API endpoint to handle chat messages
@app.post("/chat", tags=["Chat Management"])
async def chat(request: Request, chat_request: ChatRequest):
    logger.debug(f"Entering chat() with Correlation ID: {request.state.correlation_id}")
    chat_id = db_manager.add_message(chat_request.customer_guid, chat_request.question,
                                     sender_type=SenderType.CUSTOMER, chat_id=chat_request.chat_id)

    if chat_id is None:
        logger.error("Chat ID not found or invalid")
        raise HTTPException(status_code=404, detail="Chat ID not found or invalid")

    system_response = "You will get the correct answer once AI is integrated."
    db_manager.add_message(chat_request.customer_guid, system_response, sender_type=SenderType.SYSTEM, chat_id=chat_id)

    logger.debug(f"Exiting chat() with Correlation ID: {request.state.correlation_id}")
    return {"chat_id": chat_id, "customer_guid": chat_request.customer_guid, "answer": system_response}


# API endpoint to retrieve chat messages in reverse chronological order (paginated)
@app.post("/getallchats", tags=["Chat Management"])
async def get_all_chats(request: Request, get_all_chats_request: GetAllChatsRequest):
    logger.debug(f"Entering get_all_chats() with Correlation ID: {request.state.correlation_id}")
    messages = db_manager.get_paginated_chat_messages(get_all_chats_request.customer_guid,
                                                      get_all_chats_request.chat_id,
                                                      get_all_chats_request.page, get_all_chats_request.page_size)
    if not messages:
        logger.error("No chats found for this customer and chat ID")
        raise HTTPException(status_code=404, detail="No chats found for this customer and chat ID")
    logger.debug(f"Exiting get_all_chats() with Correlation ID: {request.state.correlation_id}")
    return {"messages": messages}


# API endpoint to delete a specific chat
@app.post("/deletechat", tags=["Chat Management"])
async def delete_chats(request: Request, delete_chats_request: DeleteChatsRequest):
    logger.debug(f"Entering delete_chats() with Correlation ID: {request.state.correlation_id}")
    result = db_manager.delete_chat_messages(delete_chats_request.customer_guid, delete_chats_request.chat_id)
    if result is None:
        logger.error("Failed to delete chats")
        raise HTTPException(status_code=500, detail="Failed to delete chats")
    logger.debug(f"Exiting delete_chats() with Correlation ID: {request.state.correlation_id}")
    return {"message": "Chat deleted successfully"}


# Health check endpoint at the root path to verify the server is up
@app.get("/", tags=["Health Check"])
async def check_server_status(request: Request):
    logger.debug(f"Entering check_server_status() with Correlation ID: {request.state.correlation_id}")
    logger.debug(f"Exiting check_server_status() with Correlation ID: {request.state.correlation_id}")
    return {"message": "The server is up and running!"}


# Run the server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

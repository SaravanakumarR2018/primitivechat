import logging
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.backend.db.database_manager import DatabaseManager  # Assuming the provided code is in database_connector.py
from src.backend.db.database_manager import SenderType
from src.backend.minio.minio_manager import MinioManager
from src.backend.weaviate.weaviate_manager import WeaviateManager

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
    minio_manager=  MinioManager()
    weaviate_manager=WeaviateManager()

    if customer_guid is None:
        logger.error("Failed to create customer")
        raise HTTPException(status_code=500, detail="Failed to create customer")

    #create a MinIO bucket
    try:
        minio_status=minio_manager.add_storage_bucket(customer_guid)
    except Exception as e:
        logger.error(f"Error creating MinIO bucket: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating MinIO bucket: {e}")

    #create a Weaviate class
    try:
        weaviate_status=weaviate_manager.add_weaviate_customer_class(customer_guid)
    except Exception as e:
        logger.error(f"Error creating Weaviate schema:{e}")
        raise HTTPException(status_code=500, detail=f"Error creating Weaviate schema:{e}")

    logger.debug(f"Exiting add_customer() with Correlation ID: {request.state.correlation_id}")
    return {
        "customer_guid": customer_guid,
        "minio_bucket_status":minio_status,
        "weaviate_schema_status":weaviate_status
    }

@app.post("/chat", tags=["Chat Management"])
async def chat(request: Request, chat_request: ChatRequest):
    logger.debug(f"Entering chat() with Correlation ID: {request.state.correlation_id}")

    # Call the add_message function for the user's question
    user_response = db_manager.add_message(
        chat_request.customer_guid,
        chat_request.question,
        sender_type=SenderType.CUSTOMER,
        chat_id=chat_request.chat_id
    )

    # Check if the response indicates an error
    if 'error' in user_response:
        logger.error(
            f"Error in adding user message (Correlation ID: {request.state.correlation_id}): {user_response['error']}")
        raise HTTPException(status_code=400, detail=user_response['error'])

    # Now handle the system response
    system_response = "You will get the correct answer once AI is integrated."
    system_response_result = db_manager.add_message(
        chat_request.customer_guid,
        system_response,
        sender_type=SenderType.SYSTEM,
        chat_id=user_response['chat_id']  # Use the chat_id returned from user message
    )

    # Log if the system message was not added successfully
    if 'error' in system_response_result:
        logger.error(
            f"Error in adding system message (Correlation ID: {request.state.correlation_id}): {system_response_result['error']}")
        # Do not raise an exception, just log the error

    logger.debug(f"Exiting chat() with Correlation ID: {request.state.correlation_id}")

    # Return both chat_id and system response, indicating success regardless of the system message status
    return {
        "chat_id": user_response['chat_id'],
        "customer_guid": chat_request.customer_guid,
        "answer": system_response
    }


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
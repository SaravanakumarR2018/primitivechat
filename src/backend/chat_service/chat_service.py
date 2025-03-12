import logging
from http import HTTPStatus

from sqlalchemy.exc import SQLAlchemyError

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from src.backend.lib.auth_utils import get_decoded_token  # Import auth_utils
from src.backend.lib.auth_decorator import Authenticate_and_check_role
from src.backend.lib.utils import CustomerService

from src.backend.db.database_manager import DatabaseManager, SenderType
from src.backend.minio.minio_manager import MinioManager
from src.backend.weaviate.weaviate_manager import WeaviateManager

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


app = APIRouter()

# Allow CORS if necessary

db_manager = DatabaseManager()
minio_manager = MinioManager()
weaviate_manager = WeaviateManager()
customer_service = CustomerService()

# Pydantic models for the API inputs
class ChatRequest(BaseModel):
    question: str
    chat_id: str = None


class GetAllChatsRequest(BaseModel):
    chat_id: str
    page: int = 1
    page_size: int = 10


class DeleteChatsRequest(BaseModel):
    chat_id: str

# API endpoint to add a new customer
@app.post("/addcustomer", tags=["Customer Management"])
@Authenticate_and_check_role(allowed_roles=["org:admin"])
async def add_customer(request: Request):
    """Create a new customer, set up DBs, and add an entry in the common_db table."""
    logger.debug(f"Entering add_customer()")

    try:
        decoded_token = get_decoded_token(request)
        org_id = decoded_token.get("org_id")
        if not org_id:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Org ID not found in token")

        logger.debug(f"Entering add_customer() with org_id from token: {org_id}")

        # Check if customer already exists for the given org_id
        existing_customer_guid = db_manager.get_customer_guid_from_clerk_orgId(org_id)
        if (existing_customer_guid):
            logger.info(f"Customer already exists for org_id: {org_id}, GUID: {existing_customer_guid}")
            return {"org_id": org_id, "customer_guid": existing_customer_guid}

        # Create new customer GUID
        customer_guid = db_manager.add_customer()
        if customer_guid is None:
            logger.error("Failed to create customer")
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to create customer")

        logger.info(f"Customer created with GUID: {customer_guid}")

        # Create a MinIO bucket
        try:
            minio_manager.add_storage_bucket(customer_guid)
            logger.info(f"MinIO bucket created for customer GUID: {customer_guid}")
        except Exception as e:
            logger.error(f"MinIO creation failed. Error: {e}")
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to create customer storage")

        # Create a Weaviate class
        try:
            weaviate_manager.add_weaviate_customer_class(customer_guid)
            logger.info(f"Weaviate class created for customer GUID: {customer_guid}")
        except Exception as e:
            logger.error(f"Weaviate schema creation failed. Error: {e}")
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to create customer schema")
        
        # Add extra row in common_db table
        try:
            mapping_result = db_manager.map_clerk_orgid_with_customer_guid(org_id, customer_guid)
            logger.info(f"Entry added in common_db for org_id: {mapping_result.get('org_id')}, customer_guid: {mapping_result.get('customer_guid')}")
        except SQLAlchemyError as e:
            logger.error(f"Database error while inserting into common_db: {e}")
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Database error occurred")


        logger.debug(f"Exiting add_customer() with Customer GUID: {mapping_result.get('customer_guid')}")

        return {"org_id": mapping_result['org_id'], "customer_guid": mapping_result['customer_guid']}

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")


#API endpoint for UploadFile api
@app.post("/uploadFile",tags=["File Management"])
@Authenticate_and_check_role(allowed_roles=["org:admin"])
async def upload_File(request: Request, file:UploadFile=File(...)):
    logger.debug(f"Entering upload_file() with Correlation ID:{request.state.correlation_id}")
    try:
        logger.info(f"uploading file '{file.filename} of type '{file.content_type}'")

        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            logger.error("Invalid or missing customer_guid in token")
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        #call MinioManager to Upload the file
        minio_manager.upload_file(
            bucket_name=customer_guid,
            filename=file.filename,
            file_data=file.file
        )
        db_manager.insert_customer_file_status(customer_guid=customer_guid, filename=file.filename)
        logger.info(f"File '{file.filename}' uploaded to bucket '{customer_guid}' successfully.")
        return {"message":"File uploaded SuccessFully"}

    except Exception as e:
        if isinstance(e, HTTPException):
            logger.error(f"Invalid customer_guid: {e.detail}")
            raise e
        else:
            logger.error(f"Error in file upload:{e}")
            raise HTTPException(status_code=500,detail="Error uploading the file")
    finally:
        logger.debug(f"Exiting upload_file() with Correlation ID:{request.state.correlation_id}")


@app.get("/listfiles", tags=["File Management"])
@Authenticate_and_check_role(allowed_roles=["org:admin"])
async def list_files(request: Request):
    logger.debug(f"Entering list_files() with Correlation ID: {request.state.correlation_id}")
    try:
        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        # Call MinioManager to get the file list
        file_list = minio_manager.list_files(bucket_name=customer_guid)
        if file_list:
            logger.info(f"Files retrieved for bucket '{customer_guid}':{file_list}")
        else:
            logger.info(f"No files found in bucket '{customer_guid}'")

        return {"files": file_list}
    except Exception as e:
        if isinstance(e, HTTPException):
            if e.status_code == 404:
                logger.error(f"Invalid customer_guid:{e.detail}")
                raise HTTPException(status_code=404, detail=e.detail)
            else:
                logger.error(f"Unexpected error while listing a files: {e}")
                raise HTTPException(status_code=500, detail="Unexpected error while listing a files in bucket")
        else:
            logger.error(f"Error listing files:'{customer_guid}': {e}")
            raise HTTPException(status_code=500, detail="Error listing files")
    finally:
        logger.debug(f"Exiting list_files() with Correlation ID: {request.state.correlation_id}")


@app.get("/downloadfile", tags=["File Management"])
@Authenticate_and_check_role(allowed_roles=["org:admin"])
async def download_file(request: Request, filename: str):
    logger.debug(f"Entering download_file() with Correlation ID:{request.state.correlation_id}")
    try:

        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        file_stream=minio_manager.download_file(
            customer_guid,
            filename
        )
        if isinstance(file_stream,dict) and "error" in file_stream:
            logger.error(f"Error downloading file '{filename}' from bucket '{customer_guid}'")
            raise HTTPException(status_code=500, detail=file_stream["error"])

        logger.info(f"Successfully retrieved file '{filename}' from bucket '{customer_guid}'")
        return StreamingResponse(
            file_stream,
            media_type="application/octet-stream",
            headers={
            "Content-Disposition":f"attachment; filename={filename}"
        })
    except Exception as e:
        if isinstance(e, HTTPException):
            if e.status_code==404:
                logger.error(f"Invalid customer_guid:{e.detail}")
                raise HTTPException(status_code=404, detail=e.detail)
            else:
                logger.error(f"File '{filename}' does not exist in bucket {e.detail}")
                raise HTTPException(status_code=400, detail=e.detail)
        else:
            logger.error(f"Error downloading file:{e}")
            raise HTTPException(status_code=500, detail="Error downloading file")
    finally:
        logger.debug(f"Exiting download_file() with Correlation ID:{request.state.correlation_id}")


@app.post("/chat", tags=["Chat Management"])
@Authenticate_and_check_role(allowed_roles=["org:admin"])
async def chat(request: Request, chat_request: ChatRequest):
    logger.debug(f"Entering chat() with Correlation ID: {request.state.correlation_id}")

    try:
        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        # Call the add_message function for the user's question
        user_response = db_manager.add_message(
            customer_guid,
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
            customer_guid,
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
            "customer_guid": customer_guid,
            "answer": system_response
        }
    except HTTPException as e:
        logger.error(f"HTTPException in chat(): {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in chat(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during chat processing")


# API endpoint to retrieve chat messages in reverse chronological order (paginated)
@app.get("/getallchats", tags=["Chat Management"])
@Authenticate_and_check_role(allowed_roles=["org:admin"])
async def get_all_chats(
        request: Request,
        chat_id: str,
        page: int = 1,
        page_size: int = 10
):
    logger.debug(f"Entering get_all_chats() with Correlation ID: {request.state.correlation_id}")

    try:
        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        # Call the database manager to get paginated chat messages
        messages = db_manager.get_paginated_chat_messages(customer_guid, chat_id, page, page_size)

        if not messages:
            logger.error("No chats found for this customer and chat ID")
            raise HTTPException(status_code=404, detail="No chats found for this customer and chat ID")

        logger.debug(f"Exiting get_all_chats() with Correlation ID: {request.state.correlation_id}")
        return {"messages": messages}

    except HTTPException as e:
        logger.error(f"HTTPException in get_all_chats(): {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in get_all_chats(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving chats")


# API endpoint to delete a specific chat
@app.post("/deletechat", tags=["Chat Management"])
@Authenticate_and_check_role(allowed_roles=["org:admin"])
async def delete_chats(request: Request, delete_chats_request: DeleteChatsRequest):
    logger.debug(f"Entering delete_chats() with Correlation ID: {request.state.correlation_id}")
    try:
        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")
        result = db_manager.delete_chat_messages(customer_guid, delete_chats_request.chat_id)
        if result is None:
            logger.error("Failed to delete chats")
            raise HTTPException(status_code=500, detail="Failed to delete chats")
        logger.debug(f"Exiting delete_chats() with Correlation ID: {request.state.correlation_id}")
        return {"message": "Chat deleted successfully"}
    except HTTPException as e:
        logger.error(f"HTTPException in delete_chats(): {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in delete_chats(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting chats")

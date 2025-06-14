import logging
import json
from http import HTTPStatus

from sqlalchemy.exc import SQLAlchemyError

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from src.backend.lib.auth_utils import get_decoded_token  # Import auth_utils
from src.backend.lib.utils import CustomerService, auth_admin_dependency
from sse_starlette.sse import EventSourceResponse

from src.backend.db.database_manager import DatabaseManager, SenderType
from src.backend.minio.minio_manager import MinioManager
from src.backend.weaviate.weaviate_manager import WeaviateManager
from src.backend.lib.logging_config import get_primitivechat_logger
from src.backend.chat_service.llm_service import LLMService

# Setup logging configuration
logger = get_primitivechat_logger(__name__)

app = APIRouter()

# Allow CORS if necessary

db_manager = DatabaseManager()
minio_manager = MinioManager()
weaviate_manager = WeaviateManager()
customer_service = CustomerService()
llm_service = LLMService()

# Pydantic models for the API inputs
class ChatRequest(BaseModel):
    question: str
    chat_id: str = None
    stream: bool = False  # Default value is False


class GetAllChatsRequest(BaseModel):
    chat_id: str
    page: int = 1
    page_size: int = 10


class DeleteChatsRequest(BaseModel):
    chat_id: str

class AdvancedSearchRequest(BaseModel):
    question: str
    top_k: int = 3
    alpha: float = 0.5

# API endpoint to add a new customer
@app.post("/addcustomer", tags=["Customer Management"])
async def add_customer(request: Request, auth=Depends(auth_admin_dependency)):
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
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")


#API endpoint for UploadFile api
@app.post("/uploadFile",tags=["File Management"])
async def upload_File(request: Request, auth=Depends(auth_admin_dependency), file:UploadFile=File(...)):
    logger.debug(f"Entering upload_file() with Correlation ID:{request.state.correlation_id}")
    try:
        logger.info(f"uploading file '{file.filename} of type '{file.content_type}'")

        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            logger.error("Invalid or missing customer_guid in token")
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

         # Check if the filename already exists for the customer
        if db_manager.check_filename_exists(customer_guid, file.filename):
            logger.error(f"File '{file.filename}' already exists for customer_guid: {customer_guid}")
            raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=f"File '{file.filename}' already exists in the system.")

        # Generate a unique file ID
        file_id = db_manager.generate_file_id()

        #call MinioManager to Upload the file
        minio_manager.upload_file(
            bucket_name=customer_guid,
            filename=file.filename,
            file_data=file.file
        )
        db_manager.insert_customer_file_status(customer_guid=customer_guid, filename=file.filename, file_id=file_id)
        logger.info(f"File '{file.filename}' uploaded to bucket '{customer_guid}' with file_id: {file_id} successfully.")
        return {"message":"File uploaded SuccessFully", "file_id": file_id}

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
async def list_files(request: Request, auth=Depends(auth_admin_dependency)):
    logger.debug(f"Entering list_files() with Correlation ID: {request.state.correlation_id}")
    try:
        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        # Get filenames from the database
        filenames = db_manager.get_filenames_from_database(customer_guid)

        if not filenames:
            logger.info(f"No files found for customer_guid: {customer_guid}")
            return {"files": []}

        logger.info(f"Returning {len(filenames)} files for customer_guid: {customer_guid}")
        return {"files": filenames}
    except HTTPException as e:
        raise e    
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
async def download_file(filename: str, request: Request, auth=Depends(auth_admin_dependency)):
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

@app.delete("/deletefile", tags=["File Management"])
async def delete_file(filename: str,request: Request,auth=Depends(auth_admin_dependency)):
    logger.debug(f"Entering delete_file() with filename: {filename}")
    try:
        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        if not db_manager.check_filename_exists(customer_guid, filename):
            logger.info(f"File '{filename}' doesn't exist for customer_guid: {customer_guid}")
            raise HTTPException(status_code=401, detail="File does not exist")

        # Check if the filename already delete for the customer
        if db_manager.check_delete_filename_already_exists(customer_guid, filename):
            logger.info(f"File '{filename}' already exists for customer_guid: {customer_guid}")
            return {"message": "File already marked for deletion"}

        # Mark file for deletion
        db_manager.mark_file_for_deletion(customer_guid, filename)

        return {"message": "File marked for deletion", "filename": filename}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in delete_file: {e}")
        raise HTTPException(status_code=500, detail="Error processing delete request")
    finally:
        logger.debug(f"Exiting delete_file() with filename: {filename}")


@app.get("/file/{file_id}/embeddingstatus", tags=["Vectorize Management"])
async def get_file_embedding_status(file_id: str, request: Request, auth=Depends(auth_admin_dependency)):
    logger.debug(f"Entering get_file_embedding_status() with file_id: {file_id}")
    try:
        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            logger.error("Invalid or missing customer_guid in token")
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        # Fetch the file status directly using file_id
        file_status = db_manager.get_file_embedding_status_from_file_id(customer_guid, file_id)
        if not file_status:
            logger.error(f"File with file_id: {file_id} not found for customer_guid: {customer_guid}")
            raise HTTPException(status_code=400, detail="Filename not found")

        filename, status, error_retry = file_status

        # Map the database status to a user-friendly processing stage
        status_mapping = {
            "todo": "EXTRACTING",
            "extract_error": "EXTRACTING",
            "extracted": "CHUNKING",
            "chunk_error": "CHUNKING",
            "chunked": "EMBEDDING",
            "vectorize_error": "EMBEDDING",
            "completed": "SUCCESS",
            "error": "FILE_EMBEDDING_FAILED",
            "file_vectorization_failed": "FILE_EMBEDDING_FAILED"
        }

        processing_stage = status_mapping.get(status, "UNKNOWN")
        logger.info(f"File {file_id} is in stage: {processing_stage}")

        return {
            "file_id": file_id,
            "filename": filename,
            "processing_stage": processing_stage,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching file embedding status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        logger.debug(f"Exiting get_file_embedding_status() with file_id: {file_id}")


@app.get("/file/list", tags=["Vectorize Management"])
async def paginated_list_files(
    request: Request,
    page: int = 1,
    page_size: int = 10,
    auth=Depends(auth_admin_dependency)
):
    logger.debug(f"Entering list_files() with page: {page}, page_size: {page_size}")

    try:
        # Get customer_guid from the token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            logger.error("Invalid or missing customer_guid in token")
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        # Fetch paginated files from the database
        files = db_manager.get_paginated_files(customer_guid, page, page_size)
        if not files:
            logger.info(f"No files found for customer_guid: {customer_guid}")
            return []

        # Map database status to user-friendly embedding status
        status_mapping = {
            "todo": "EXTRACTING",
            "extract_error": "EXTRACTING",
            "extracted": "CHUNKING",
            "chunk_error": "CHUNKING",
            "chunked": "EMBEDDING",
            "vectorize_error": "EMBEDDING",
            "completed": "SUCCESS",
            "error": "FILE_EMBEDDING_FAILED",
            "file_vectorization_failed": "FILE_EMBEDDING_FAILED"
        }

        # Format the response
        response = [
            {
                "fileid": file["file_id"],
                "filename": file["filename"],
                "embeddingstatus": status_mapping.get(file["status"], "UNKNOWN"),
                "uploaded_time": file["uploaded_time"]
            }
            for file in files
        ]

        logger.info(f"Returning {len(response)} files for customer_guid: {customer_guid}")
        return response

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in list_files: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")

@app.get("/files/deletionstatus", tags=["Vectorize Management"])
async def get_files_deletion_status(request: Request, page: int = 1, page_size: int = 10, auth=Depends(auth_admin_dependency)
):
    logger.debug(f"Entering get_files_deletion_status (page:{page}, size:{page_size}")
    try:
        # Get customer_guid from token
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            logger.error("Invalid or missing customer_guid in token")
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        files = db_manager.get_files_with_deletion_status(customer_guid, page, page_size)

        if not files:
            logger.info(f"No files found for customer_guid: {customer_guid}")
            return []

        # Status mapping
        status_mapping = {
            "todo": "PENDING_DELETION",
            "in_progress": "DELETION_IN_PROGRESS",
            "completed": "DELETION_COMPLETED",
            "error": "DELETION_FAILED"
        }

        # Format response with mapped status
        response = [
            {
                "file_id": file["file_id"],
                "filename": file["filename"],
                "deletion_status": status_mapping.get(file["delete_status"],"UNKNOWN_STATUS"),
                "uploaded_time": file["uploaded_time"],
                "delete_request_timestamp":file["delete_request_timestamp"]
            }
            for file in files
        ]

        logger.info(f"Returning {len(response)} files with deletion status")
        return response

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in get_files_deletion_status: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,detail="An unexpected error occurred")

@app.post("/chat", tags=["Chat Management"])
async def chat(chat_request: ChatRequest, request: Request, auth=Depends(auth_admin_dependency)):
    logger.debug(f"Entering chat() with Correlation ID: {request.state.correlation_id}")

    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        user_id = customer_service.get_user_id_from_token(request)
        if not user_id:
            raise HTTPException(status_code=404, detail="Missing required parameter: user_id")

        user_response = db_manager.add_message(
            user_id,
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
        chat_id = user_response['chat_id']

        # Get streaming generator from LLM
        response_stream = llm_service.get_response(
            question=chat_request.question,
            user_id=user_id,
            customer_guid=customer_guid,
            chat_id=chat_id
        )

        if chat_request.stream:
            full_answer = ""

            async def event_generator():
                nonlocal full_answer
                async for chunk in response_stream:
                    yield json.dumps(chunk)  # No "data:" prefix
                    if "choices" in chunk and chunk["choices"]:
                        delta = chunk["choices"][0].get("delta", {})
                        full_answer += delta.get("content", "")
                yield "[DONE]"
                # Save system response to DB after fully sending
                db_manager.add_message(
                    user_id,
                    customer_guid,
                    full_answer,
                    sender_type=SenderType.SYSTEM,
                    chat_id=chat_id
                )

            return EventSourceResponse(event_generator())

        else:
            # Not streaming — accumulate response from chunks
            full_answer = ""
            async for chunk in response_stream:
                logger.debug(f"Received chunk: {chunk}")
                if "choices" in chunk and chunk["choices"]:
                    delta = chunk["choices"][0].get("delta", {})
                    full_answer += delta.get("content", "")

            # Save system response to DB
            db_manager.add_message(
                user_id,
                customer_guid,
                full_answer,
                sender_type=SenderType.SYSTEM,
                chat_id=chat_id
            )

            return {
                "chat_id": chat_id,
                "customer_guid": customer_guid,
                "user_id": user_id,
                "answer": full_answer
            }

    except HTTPException as e:
        logger.error(f"HTTPException in chat(): {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in chat(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during chat processing")

# API endpoint to retrieve chat messages in reverse chronological order (paginated)
@app.get("/getallchats", tags=["Chat Management"])
async def get_all_chats(
        request: Request,
        chat_id: str,
        page: int = 1,
        page_size: int = 10,
        auth=Depends(auth_admin_dependency),
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

@app.get("/getallchatids", tags=["Chat Management"])
async def get_all_chat_ids(
        request: Request,
        page: int = 1,
        page_size: int = 10,
        auth=Depends(auth_admin_dependency),
):
    logger.debug(f"Entering get_all_chat_ids() with Correlation ID: {request.state.correlation_id}")

    try:
        # Get user_id from the token
        logger.debug("Fetching user_id from token")
        try:
            user_id = customer_service.get_user_id_from_token(request)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid or expired token")

        logger.debug(f"Extracted user_id: {user_id}")
        if not user_id:
            logger.error("Invalid user_id provided")
            raise HTTPException(status_code=404, detail="Invalid user_id provided")

        # Get customer_guid from the token
        logger.debug("Fetching customer_guid from token")
        customer_guid = customer_service.get_customer_guid_from_token(request)
        logger.debug(f"Extracted customer_guid: {customer_guid}")

        if not customer_guid:
            logger.error("Invalid customer_guid provided")
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        logger.info(f"Fetching all chat IDs for User ID: {user_id}, Customer GUID: {customer_guid}")

        # Call database function to get chat IDs
        logger.debug(f"Calling get_all_chat_ids() with customer_guid={customer_guid}, user_id={user_id}, page={page}, page_size={page_size}")
        chat_ids = db_manager.get_all_chat_ids(customer_guid, user_id, page, page_size)

        # If no chat messages are found, return an empty list
        if chat_ids is None:
            logger.warning(f"No chat messages found for User ID: {user_id}")
            chat_ids = []  # Instead of returning early, ensure chat_ids is always a list

        logger.debug(f"Exiting get_all_chat_ids() with Correlation ID: {request.state.correlation_id}")
        return {"chat_ids": chat_ids}

    except HTTPException as e:
        logger.error(f"HTTPException in get_all_chat_ids(): {e.detail}")
        raise e  # Re-raise known HTTP errors

    except Exception as e:
        logger.error(f"Unexpected error in get_all_chat_ids(): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error occurred while retrieving chat IDs")

# API endpoint to delete a specific chat
@app.post("/deletechat", tags=["Chat Management"])
async def delete_chats(delete_chats_request: DeleteChatsRequest, request: Request, auth=Depends(auth_admin_dependency)):
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


@app.post("/advanced_search", tags=["Chat Management"])
async def advanced_search(
    search_request: AdvancedSearchRequest,
    request: Request,
    auth=Depends(auth_admin_dependency)
):
    logger.debug(f"Entering advanced_search() with Correlation ID: {request.state.correlation_id}")

    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)
        if not customer_guid:
            raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

        # Call the advanced search function
        results = weaviate_manager.search_query_advanced(
            customer_guid=customer_guid,
            question=search_request.question,
            top_k=search_request.top_k,
            alpha=search_request.alpha
        )
        return results

    except HTTPException as e:
        logger.error(f"HTTPException in advanced_search(): {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in advanced_search(): {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during advanced search")
import logging
import re
from datetime import datetime
from http import HTTPStatus
from typing import List, Optional, Dict, Any, Union

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, StrictBool
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError

from src.backend.db.database_manager import DatabaseManager  # Assuming the provided code is in database_connector.py
from src.backend.lib.utils import CustomerService, auth_admin_dependency
from src.backend.lib.logging_config import get_primitivechat_logger

# Setup logging configuration
logger = get_primitivechat_logger(__name__)


app = APIRouter()

# Initialize DatabaseManager instance
db_manager = DatabaseManager()

#Intialize CustomerService Instance
customer_service=CustomerService()

# Custom Field Pydantic Model
class CustomField(BaseModel):
    field_name: str
    field_type: str
    required: StrictBool

class CustomFieldResponse(BaseModel):
    field_name: str
    field_type: str
    required: bool

# Tickets Pydantic Model
class Ticket(BaseModel):
    ticket_id: Union[str, int]
    chat_id: Optional[str]
    title: str
    description: Optional[str]
    priority: str
    status: str
    reported_by: Optional[str]
    assigned: Optional[str]
    created_at: datetime
    updated_at: datetime
    custom_fields: Optional[Dict[str, Union[Any, None]]] = None

class TicketRequest(BaseModel):
    chat_id: Optional[str]
    title: str
    description: Optional[str]
    priority: str
    reported_by: Optional[str]
    assigned: Optional[str]
    custom_fields: Optional[Dict[str, Any]] = None

class TicketResponse(BaseModel):
    ticket_id: Union[str, int]
    status: str

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    reported_by: Optional[str] = None
    assigned: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class TicketByChatId(BaseModel):
    ticket_id: Union[str, int]
    title: str
    status: str
    created_at: datetime

class TicketByCustomerId(BaseModel):
    ticket_id: int
    title: str
    status: str
    priority:str
    reported_by:str
    assigned:str
    created_at:datetime

# Comments Pydantic Model
class Comment(BaseModel):
    comment_id: Union[str, int]
    ticket_id: Union[str, int]
    posted_by: str
    comment: str
    is_edited: bool
    created_at: datetime
    updated_at: datetime

class CommentRequest(BaseModel):
    ticket_id: Union[str, int]
    posted_by: str
    comment: str

class CommentUpdate(BaseModel):
    comment: str
    posted_by: str

class CommentDeleteResponse(BaseModel):
    comment_id: Union[str, int]
    status: str

# Custom Fields Management APIs
@app.post("/custom_fields", response_model=CustomField, status_code=HTTPStatus.CREATED, tags=["Custom Field Management"])
async def add_custom_field(custom_field: CustomField, request: Request, auth=Depends(auth_admin_dependency)):
    """Add a new custom field to a customer's tickets"""
    try:
        # Retrieve the mapped customer_guid
        existing_customer_guid = customer_service.get_customer_guid_from_token(request)
        # Add custom field to the database using retrieved customer_guid
        success = db_manager.add_custom_field(
            str(existing_customer_guid),
            custom_field.field_name,
            custom_field.field_type,
            custom_field.required,
        )

        if success:
            return custom_field
        else:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Failed to add custom field")

    except ValueError as ve:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(ve))
    except HTTPException as e:
        raise e
    except Exception as e:
        if "Database connectivity issue" in str(e):
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@app.get("/custom_fields", response_model=List[CustomFieldResponse], tags=["Custom Field Management"])
async def list_custom_fields(
    request: Request,
    auth=Depends(auth_admin_dependency),
    page: int = 1,
    page_size: int = 10
):
    """List all custom fields for a customer with pagination."""
    try:
        # Retrieve the mapped customer_guid
        customer_guid = customer_service.get_customer_guid_from_token(request)
        # Call the modified list_paginated_custom_fields to get paginated results
        paginated_fields = db_manager.list_paginated_custom_fields(str(customer_guid), page, page_size)

        if not paginated_fields:
            logger.info(f"No custom fields found for customer {customer_guid}")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"No custom fields found for customer {customer_guid}",
            )

        # Construct and return the structured response with pagination
        return [
                CustomFieldResponse(
                    field_name=field["field_name"],
                    field_type=field["field_type"],
                    required=field["required"],
                )
                for field in paginated_fields
            ]

    except ValueError as e:
        logger.error(f"Validation error while listing custom fields: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing custom fields: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Database error occurred.")

    except HTTPException as e:
        raise e

    except Exception as e:
        if "Database connectivity issue" in str(e):
            logger.error(f"Database connectivity error: {e}")
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later.",
            )
        logger.error(f"Unexpected error while listing custom fields: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Internal server error.")

@app.delete("/custom_fields/{field_name}", tags=["Custom Field Management"])
async def delete_custom_field(field_name: str, request: Request, auth=Depends(auth_admin_dependency)):
    """Delete a custom field"""
    try:
        existing_customer_guid = customer_service.get_customer_guid_from_token(request)
        result = db_manager.delete_custom_field(str(existing_customer_guid), field_name)

        if result["status"] == "deleted":
            return {"field_name": field_name, "status": "deleted"}

        elif result["status"] == "not_found":
            return {"message": f"Custom field '{field_name}' was not found, no action needed"}

        elif result["status"] == "unknown_db":
            logger.error("Unknown Database error occurred: " + result["reason"])
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=result["reason"]
            )

        elif result["status"] == "db_unreachable":
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )

        else:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete Custom Field '{field_name}': {result['reason']}"
            )

    except HTTPException as e:
        raise e
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during custom field deletion: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the custom field."
        )


#Tickets APIS
@app.post("/tickets", response_model=TicketResponse, status_code=HTTPStatus.CREATED, tags=["Ticket Management"])
async def create_ticket(ticket: TicketRequest, request: Request, auth=Depends(auth_admin_dependency)):
    """Create a new ticket"""
    try:
        existing_customer_guid = customer_service.get_customer_guid_from_token(request)

        logger.debug(f"Received ticket data: {ticket}")
        # Call the database method to create the ticket
        db_response = db_manager.create_ticket(
            str(existing_customer_guid),
            ticket.chat_id,
            ticket.title,
            ticket.description,
            ticket.priority,
            ticket.reported_by,
            ticket.assigned,
            ticket.custom_fields if ticket.custom_fields else {}
        )

        return TicketResponse(ticket_id=str(db_response["ticket_id"]), status="created")

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))

    except OperationalError as e:
        logger.error(f"Operational error: {e}")
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="The database is currently unreachable. Please try again later."
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="The database is currently unreachable. Please try again later."
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in creating ticket: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@app.get("/tickets/{ticket_id}", response_model=Ticket, tags=["Ticket Management"])
async def get_ticket(ticket_id: str, request: Request, auth=Depends(auth_admin_dependency)):
    """Retrieve a ticket by ID"""
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)
    except HTTPException as e:
        raise e
    try:
        ticket = db_manager.get_ticket_by_id(ticket_id, str(customer_guid))

        if ticket is None:
            logger.info(f"Ticket with ticket_id {ticket_id} not found for customer {customer_guid}")
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Ticket with ticket_id {ticket_id} not found for customer {customer_guid}")  # Correctly raise 404 error if not found
        else:
            return ticket
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Ticket with ticket_id {ticket_id} not found for customer {customer_guid}")
    except Exception as e:
        if "Database connectivity issue" in str(e):
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@app.get("/tickets", response_model=List[TicketByChatId], tags=["Ticket Management"])
async def get_tickets_by_chat_id(
        request: Request,
        chat_id: str,
        page: int = 1,
        page_size: int = 10,
        auth=Depends(auth_admin_dependency),
):
    """Retrieve all tickets for a specific chat_id with pagination"""
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)
    except HTTPException as e:
        raise e
    try:
        tickets = db_manager.get_paginated_tickets_by_chat_id(str(customer_guid), chat_id, page, page_size)

        if not tickets:
            logger.info(f"No tickets found for chat_id {chat_id} and customer {customer_guid}")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"No tickets found for chat_id {chat_id}"
            )
        return tickets
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        logger.info(f"No tickets found for chat_id {chat_id} and customer {customer_guid}")
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"No tickets found for chat_id {chat_id}"
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving tickets: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Database error")
    except Exception as e:
        if "Database connectivity issue" in str(e):
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@app.put("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Ticket Management"])
async def update_ticket(ticket_id: str, ticket_update: TicketUpdate, request: Request, auth=Depends(auth_admin_dependency)):
    """Update an existing ticket"""
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)

        update_status = db_manager.update_ticket(ticket_id, str(customer_guid), ticket_update)

        if update_status["status"] == "updated":
            return TicketResponse(ticket_id=ticket_id, status="updated")
        elif update_status["status"] == "not_found":
            logger.error(update_status["reason"])
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=update_status["reason"]
            )
        elif update_status["status"] == "unknown_db":
            logger.error("Unknown Database error occurred: " + update_status["reason"])
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=update_status["reason"]
            )
        elif update_status["status"] == "bad_request":
            original_error = update_status["reason"]
            logger.info(f"Original_error: {original_error}")
            formatted_error = extract_core_error_details(original_error)
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=formatted_error
            )
        elif update_status["status"] == "db_unreachable":
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )
        else:
            logger.error(update_status["reason"])
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {update_status['reason'] or 'Unknown cause.'}"
            )

    except HTTPException as e:
            raise e
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred."
        )

@app.delete("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Ticket Management"])
async def delete_ticket(ticket_id: str, request: Request, auth=Depends(auth_admin_dependency)):
    """Delete a ticket and corresponding custom fields"""
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)

        result = db_manager.delete_ticket(ticket_id, str(customer_guid))

        if result["status"] == "deleted":
            return TicketResponse(ticket_id=ticket_id, status="deleted")

        elif result["status"] == "not_found":
            return TicketResponse(ticket_id=ticket_id, status="deleted")

        elif result["status"] == "dependency_error":
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Unable to delete Ticket ID {ticket_id} due to dependent data: {result['reason']}"
            )
        elif result["status"] == "unknown_db":
            logger.error(logger.error("Unknown Database error occurred: " + result["reason"]))
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=result["reason"]
            )
        elif result["status"] == "db_unreachable":
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )

        else:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete Ticket ID {ticket_id}: {result['reason']}"
            )
    except HTTPException as e:
        raise e
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during ticket deletion: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the ticket."
        )


def extract_core_error_details(message):
    """Extract and format the core error details for readability."""
    patterns = [
        r"Unknown column '(.+?)' in 'field list'",  # Matches "Unknown column" errors
        r"Data truncated for column '(.+?)'",       # Matches "Data truncated" errors
        r"Incorrect integer value: '(.*?)' for column '(.+?)'",# Matches "Incorrect integer value" errors
        r"Incorrect datetime value: '(.*?)' for column '(.+?)'",
    ]

    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            # Format the error details based on the matched pattern
            if "Unknown column" in pattern:
                return f"Unknown custom field column: '{match.group(1)}'."
            elif "Data truncated" in pattern:
                if match.group(1)== "priority":
                    return (
                        f"Value Not allowed for column: '{match.group(1)}'. use [Low, Medium, High]"
                    )
                return f"Incorrect value for column: {match.group(1)}."
            elif "Incorrect integer value" in pattern:
                return f"Incorrect value: '{match.group(1)}' for column: '{match.group(2)}'."
            elif "Incorrect datetime value" in pattern:
                return f"Incorrect value: '{match.group(1)}' for column: '{match.group(2)}'."

    # Default message if no pattern matches
    return "An unknown conflict occurred. Please check the error details."


#Comments APIS
@app.post("/add_comment", response_model=Comment, status_code=HTTPStatus.CREATED, tags=["Comment Management"])
async def create_comment(comment: CommentRequest, request: Request, auth=Depends(auth_admin_dependency)):
    """Create a new comment for a ticket"""
    logger.debug(f"Received comment data: {comment}")
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)
        # Call the database method to create the comment
        logger.debug("Calling DBManager.create_comment")
        db_response = db_manager.create_comment(
            str(customer_guid),
            comment.ticket_id,
            comment.posted_by,
            comment.comment
        )

        logger.debug(f"Database response: {db_response}")
        return Comment(comment_id=str(db_response["comment_id"]), ticket_id=str(db_response["ticket_id"]), posted_by=str(db_response["posted_by"]), comment=str(db_response["comment"]), is_edited=db_response["is_edited"], created_at=db_response["created_at"], updated_at=db_response["updated_at"])

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))

    except OperationalError as e:
        logger.error(f"Operational error: {e}")
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="The database is currently unreachable. Please try again later."
        )
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="The database is currently unreachable. Please try again later."
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except HTTPException as e:
            raise e
    except Exception as e:
        logger.error(f"Unexpected error in creating comment: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@app.get("/tickets/{ticket_id}/comments/{comment_id}", response_model=Comment, tags=["Comment Management"])
async def get_comment(comment_id: str, ticket_id: str, request: Request, auth=Depends(auth_admin_dependency)):
    """Retrieve a comment by ID"""
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)
    except HTTPException as e:
        raise e
    try:
        comment = db_manager.get_comment_by_id(comment_id, str(customer_guid), ticket_id)

        if comment is None:
            logger.info(f"Comment with comment_id {comment_id} not found for customer {customer_guid}")
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Comment with comment_id {comment_id} not found for customer {customer_guid}")
        else:
            return comment
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"Comment with comment_id {comment_id} not found for ticket id {ticket_id}")
    except Exception as e:
        if "Database connectivity issue" in str(e):
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@app.get("/tickets/{ticket_id}/comments", response_model=List[Comment], tags=["Comment Management"])
async def get_comments_by_ticket_id(
        request: Request,
        ticket_id: str,
        page: int = 1,
        page_size: int = 10,
        auth=Depends(auth_admin_dependency)
):
    """Retrieve all comments for a specific ticket_id"""
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)
    except HTTPException as e:
        raise e
    try:
        comments = db_manager.get_paginated_comments_by_ticket_id(str(customer_guid), ticket_id, page, page_size)

        if not comments:
            logger.info(f"No comments found for ticket_id {ticket_id} and customer {customer_guid}")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"No comments found for ticket_id {ticket_id}"
            )
        return comments
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        logger.info(f"No comments found for ticket_id {ticket_id} and customer {customer_guid}")
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"No comments found for ticket_id {ticket_id}"
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving comments: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Database error")
    except Exception as e:
        if "Database connectivity issue" in str(e):
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@app.put("/update_comment", response_model=Comment, tags=["Comment Management"])
async def update_comment(ticket_id: str, comment_id: str, comment_update: CommentUpdate, request: Request, auth=Depends(auth_admin_dependency)):
    """Update an existing comment"""
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)
        logger.debug(f"Updating comment - Ticket ID: {ticket_id}, Comment ID: {comment_id}, Update: {comment_update}, Customer GUID: {customer_guid}")
        update_status = db_manager.update_comment(ticket_id, comment_id, str(customer_guid), comment_update)

        if update_status["status"] == "updated":
            comment_data = update_status.get("comment_data", {})
            return Comment(**comment_data)
        elif update_status["status"] == "not_found":
            logger.error(update_status["reason"])
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=update_status["reason"]
            )
        elif update_status["status"] == "conflict":
            original_error = update_status["reason"]
            formatted_error = extract_core_error_details(original_error)
            logger.error(f"Conflict error occurred:\n{formatted_error}")
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=formatted_error
            )
        elif update_status["status"] == "unknown_db":
            logger.error("Unknown Database error occurred: " + update_status["reason"])
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=update_status["reason"]
            )
        elif update_status["status"] == "bad_request":
            original_error = update_status["reason"]
            if "You are not authorized to update this comment" not in update_status["reason"]:
                formatted_error = extract_core_error_details(original_error)
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=formatted_error
                )
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=update_status["reason"]
            )
        elif update_status["status"] == "db_unreachable":
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )
        else:
            logger.error(update_status["reason"])
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {update_status['reason'] or 'Unknown cause.'}"
            )

    except HTTPException as e:
        raise e
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred."
        )

@app.delete("/delete_comment", response_model=CommentDeleteResponse, tags=["Comment Management"])
async def delete_comment(ticket_id: str, comment_id: str, request: Request, auth=Depends(auth_admin_dependency)):
    """Delete a comment for a specific ticket."""
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)

        result = db_manager.delete_comment(ticket_id, comment_id, str(customer_guid))

        if result["status"] == "deleted":
            return CommentDeleteResponse(comment_id=comment_id, status="deleted")

        elif result["status"] == "not_found":
            logger.error(result["reason"])
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=result["reason"]
            )

        elif result["status"] == "unknown_db":
            logger.error("Unknown Database error occurred: " + result["reason"])
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=result["reason"]
            )

        elif result["status"] == "db_unreachable":
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )

        else:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete Comment ID {comment_id}: {result['reason']}"
            )

    except HTTPException as e:
        raise e
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during comment deletion: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the comment."
        )

@app.get("/customer/tickets/", response_model=List[TicketByCustomerId], tags=["Ticket Management"])
async def get_tickets_by_customer_guid(
    request: Request,
    auth=Depends(auth_admin_dependency),
    page: int = 1,
    page_size: int = 10
):
    """Retrieve all tickets for a specific customer_guid with pagination"""
    try:
        customer_guid = customer_service.get_customer_guid_from_token(request)
    except HTTPException as e:
        raise e
    try:
        logger.debug(f"Received customer_guid: {customer_guid}, page: {page}, page_size: {page_size}")
        tickets = db_manager.get_paginated_tickets_by_customer_guid(str(customer_guid), page, page_size)

        if not tickets:
            logger.info(f"No tickets found for customer {customer_guid}")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"No tickets found for customer {customer_guid}"
            )
        return tickets

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        logger.info(f"No tickets found for customer {customer_guid}")
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"No tickets found for customer {customer_guid}"
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving tickets: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Database error")
    except Exception as e:
        if "Database connectivity issue" in str(e):
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="The database is currently unreachable. Please try again later."
            )
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Internal Server Error")

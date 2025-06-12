import logging
import re
from datetime import datetime
from http import HTTPStatus
from typing import List, Optional, Dict, Any, Union

import json # For parsing potential JSON string from LLM
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, StrictBool
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError

from src.backend.db.database_manager import DatabaseManager, SenderType
from src.backend.lib.utils import CustomerService, auth_admin_dependency
from src.backend.lib.logging_config import get_primitivechat_logger
from src.backend.chat_service.llm_service import LLMService 
from langchain_core.messages import HumanMessage, SystemMessage
# from src.backend.lib.auth_utils import get_customer_guid_from_token # Not used in the new logic, auth object is used

# Setup logging configuration
logger = get_primitivechat_logger(__name__)


app = APIRouter()

# Initialize DatabaseManager instance
db_manager = DatabaseManager()
llm_service = LLMService() # Instantiating LLMService

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

class TicketByConversationBase(BaseModel):
    chat_id: str
    reported_by: str

class TicketByConversationResponse(BaseModel):
    ticket_id: int

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
@app.post("/create_ticket_by_conversation", response_model=TicketByConversationResponse, tags=["Ticket Management"])
async def create_ticket_from_conversation(
    ticket_data: TicketByConversationBase,
    request: Request,
    auth=Depends(auth_admin_dependency),  # auth contains user details
    message_count: int = 200  # Default to 200 if not provided
):
    try:
        # 1. Get customer_guid from token
        try:
            customer_guid = customer_service.get_customer_guid_from_token(request)
            if not customer_guid:
                raise ValueError("Customer GUID not found in token")
        except ValueError as e:
            logger.error(f"Failed to get customer_guid: {e}")
            raise HTTPException(status_code=404, detail=f"Database customer_{customer_guid} does not exists")

        logger.info(f"Creating ticket from conversation for user: {ticket_data.reported_by}")
        current_user_id = ticket_data.reported_by  # Get user_id for 'reported_by'
        # 2. Get chat messages
        # Assuming get_paginated_chat_messages returns messages sorted by created_at DESC (newest first)
        chat_messages_data = db_manager.get_paginated_chat_messages(
            customer_guid=str(customer_guid), # Ensure customer_guid is a string
            chat_id=ticket_data.chat_id,
            page=1, # Fetch the first page
            page_size=message_count # Fetch up to message_count messages
        )
        
        # The method returns a dict with 'messages' and 'total_count'
        actual_chat_messages = chat_messages_data or []

        if not actual_chat_messages:
            raise HTTPException(status_code=404, detail=f"No messages found for chat_id {ticket_data.chat_id} or chat is empty.")

        # Format messages for LLM (oldest first for proper context)
        actual_chat_messages.reverse() 
        chat_context = "\n".join([f"{SenderType(msg['sender_type']).name if isinstance(msg['sender_type'], int) else msg['sender_type']}: {msg['message']}" for msg in actual_chat_messages])


        # 3. Call LLM to extract ticket fields
        if not LLMService.llm: # Ensure LLM is initialized
             logger.info("LLM not initialized, initializing now.")
             llm_service._initialize_llm(LLMService.LLMProvider, LLMService.model) # Use instance to call _initialize_llm
        
        prompt_messages = [
            SystemMessage(content="You are an AI assistant tasked with creating a support ticket from a conversation transcript. "
                                  "Extract the following fields: title, description, priority, and optionally 'assigned' (if mentioned) and 'custom_fields' (if any specific key-value pairs are clearly indicated for a ticket). "
                                  "The user requesting this is: " + current_user_id + ". "
                                  "Set 'reported_by' to this user. "
                                  "If priority is not mentioned, default to 'Medium'. "
                                  "Respond with a JSON object containing these fields. For example: "
                                  "{\"title\": \"Issue with login\", \"description\": \"User cannot log in after password reset.\", \"priority\": \"High\", \"reported_by\": \"" + current_user_id + "\", \"assigned\": null, \"custom_fields\": {\"product_id\": \"XYZ123\"}}"),
            HumanMessage(content=f"Here is the chat context:\n{chat_context}")
        ]
        
        llm_response = LLMService.llm.invoke(prompt_messages)
        
        raw_content = ""
        extracted_fields = None

        if hasattr(llm_response, 'content'):
            raw_content = llm_response.content
        elif isinstance(llm_response, str): # If LLM directly returns a string
            raw_content = llm_response
        elif isinstance(llm_response, dict): # If LLM directly returns a dict
            extracted_fields = llm_response # No parsing needed
            # Ensure critical fields are present or defaulted if necessary
            extracted_fields.setdefault("title", "Untitled Ticket from Conversation")
            extracted_fields.setdefault("description", "No description provided by LLM.")
            extracted_fields.setdefault("priority", "Medium")
            # reported_by should be set from auth context later, but ensure key exists if LLM provides it
            if "reported_by" not in extracted_fields:
                 extracted_fields.setdefault("reported_by", current_user_id)
            extracted_fields.setdefault("assigned", None)
            extracted_fields.setdefault("custom_fields", {})
        else:
            # Fallback for unexpected llm_response type
            logger.error(f"Unexpected LLM response type: {type(llm_response)}. Response: {llm_response}")
            raise HTTPException(status_code=500, detail="Unexpected LLM response format, cannot extract content.")

        if extracted_fields is None and isinstance(raw_content, str): # Only parse if not already a dict
            # Strip markdown fences if content is a string
            cleaned_content = raw_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:] # Remove ```json
            elif cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:] # Remove ```
            
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3] # Remove trailing ```
            
            cleaned_content = cleaned_content.strip() # Remove any leading/trailing whitespace leftover

            try:
                extracted_fields = json.loads(cleaned_content)
            except json.JSONDecodeError:
                logger.error(f"LLM did not return valid JSON after cleaning. Content: {cleaned_content}", exc_info=True)
                # print(f"LLM did not return valid JSON after cleaning. Content: {cleaned_content}") # Temporary
                raise HTTPException(status_code=500, detail=f"LLM did not return valid JSON after cleaning. Raw response: {raw_content}")
        elif extracted_fields is None: # If raw_content wasn't a string and not a dict, implies error or unexpected type
             logger.error(f"Cannot parse LLM response. Raw content type: {type(raw_content)}, Extracted fields is None.")
             raise HTTPException(status_code=500, detail="Failed to parse LLM response due to unexpected content type.")

        # Prepare ticket data (this part remains largely the same)

        # 1. Fetch and process defined custom fields for the customer
        allowed_field_details = {} # Stores full details: name -> {type, required}
        try:
            # Ensure customer_guid is a string for the DB call
            defined_custom_fields_list = db_manager.list_paginated_custom_fields(
                customer_guid=str(customer_guid),
                page=1,
                page_size=1000  # Assuming a reasonably high number to get all fields
            )
            if defined_custom_fields_list: # Ensure it's not None or empty before processing
                for field_detail in defined_custom_fields_list:
                    if isinstance(field_detail, dict) and 'field_name' in field_detail:
                        allowed_field_details[field_detail['field_name']] = {
                            'field_type': field_detail.get('field_type', '').upper(), # Store type, uppercase for consistency
                            'required': field_detail.get('required', False)
                        }
            logger.info(f"Allowed custom field details for customer {customer_guid}: {allowed_field_details}")

        except Exception as e:
            logger.error(f"Error fetching or processing defined custom fields for customer {customer_guid}: {e}", exc_info=True)
            # They use allowed_field_details (which is now populated) to filter LLM fields and add missing required ones.
        llm_custom_fields = extracted_fields.get("custom_fields", {})
        final_ticket_custom_fields = {} # This will be populated by logic in subsequent subtasks.
        
        # 2. Filter LLM-extracted Custom Fields
        if isinstance(llm_custom_fields, dict):
            for field_name, value in llm_custom_fields.items():
                if field_name in allowed_field_details: # Check against the keys of the detailed dictionary
                    # If the field name is recognized as a defined custom field for this customer
                    final_ticket_custom_fields[field_name] = value
                    logger.info(f"LLM suggested custom field '{field_name}' is valid and was added.")
                else:
                    logger.info(f"LLM suggested custom field '{field_name}' which is not defined for customer {customer_guid}. Ignoring.")
        elif llm_custom_fields: # If it's not a dict but also not None/empty (e.g., a list or string)
            logger.warning(f"LLM extracted 'custom_fields' but it was not a dictionary: {llm_custom_fields} for customer {customer_guid}. No custom fields will be processed from LLM.")
        
        # 3. Populate Missing Required Custom Fields
        if allowed_field_details: # Only proceed if we have details of allowed fields
            for field_name, details in allowed_field_details.items():
                # NEW condition:
                required_value = details.get('required')
                is_field_required = False
                if isinstance(required_value, str):
                    is_field_required = required_value.lower() in ['true', '1', 'yes']
                elif isinstance(required_value, int):
                    is_field_required = required_value == 1
                elif isinstance(required_value, bool):
                    is_field_required = required_value is True # Explicit True for bool

                if is_field_required and field_name not in final_ticket_custom_fields:
                    field_type = details.get('field_type', '').upper() # Already uppercased when populating details
                    
                    default_value = None
                    if field_type.startswith('VARCHAR') or field_type.startswith('TEXT') or field_type.startswith('MEDIUMTEXT'):
                        default_value = "(Not Provided)"
                    elif field_type.startswith('INT'):
                        default_value = 0
                    elif field_type.startswith('FLOAT'):
                        default_value = 0.0
                    elif field_type.startswith('BOOLEAN') or field_type.startswith('TINYINT(1)'):
                        default_value = False 
                    elif field_type.startswith('DATETIME'):
                        try:
                            default_value = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                        except Exception as dt_e:
                            logger.error(f"Could not generate default datetime for required field {field_name}: {dt_e}")
                            default_value = "1970-01-01 00:00:00" # Fallback default datetime string
                    else:
                        default_value = f"(Default for required {field_type})" 
                        logger.warning(f"Required custom field '{field_name}' has an unrecognized type '{field_type}'. Using generic default.")
                    
                    final_ticket_custom_fields[field_name] = default_value
                    logger.info(f"Populated missing required custom field '{field_name}' with default value: {default_value} (required status was: {required_value})")

        # Existing logic for standard fields (title, description, priority, reported_by, assigned)
        ticket_title = extracted_fields.get("title", "Untitled Ticket from Conversation")
        ticket_description = extracted_fields.get("description", "No description provided by LLM.")
        ticket_priority = extracted_fields.get("priority", "Medium")
        valid_priorities = ["Low", "Medium", "High"] # Consider making this case-insensitive if needed
        if ticket_priority not in valid_priorities: # Basic check, db might be more strict
            ticket_priority = "Medium"
        
        ticket_reported_by = current_user_id # Always use authenticated user
        ticket_assigned = extracted_fields.get("assigned")

        # Call create_ticket with the now complete final_ticket_custom_fields
        db_response = db_manager.create_ticket(
            customer_guid=str(customer_guid),
            chat_id=ticket_data.chat_id,
            title=ticket_title, 
            description=ticket_description, 
            priority=ticket_priority, 
            reported_by=ticket_reported_by, 
            assigned=ticket_assigned, 
            custom_fields=final_ticket_custom_fields
        )

        if "ticket_id" not in db_response:
            logger.error(f"Failed to create ticket in database. DB response: {db_response}")
            raise HTTPException(status_code=500, detail=f"Failed to create ticket in database.")
        
        ticket_id = db_response["ticket_id"]

        # Add comment to the ticket
        comment_response = db_manager.create_comment(
            ticket_id=ticket_id,
            comment=chat_context,
            posted_by=ticket_reported_by,
            customer_guid=str(customer_guid),
        )

        # 5. Return ticket_id
        return TicketByConversationResponse(ticket_id=ticket_id)

    except HTTPException as he:
        raise he
    except ValueError as ve: 
        logger.error(f"ValueError creating ticket from conversation: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating ticket from conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

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

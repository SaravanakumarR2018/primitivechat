import logging
from typing import List, Optional, Dict, Union, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from src.backend.db.database_manager import DatabaseManager  # Assuming the provided code is in database_connector.py

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = APIRouter()

# Initialize DatabaseManager instance
db_manager = DatabaseManager()


# Custom Fields Management APIs

class CustomField(BaseModel):
    customer_guid: UUID
    field_name: str
    field_type: str
    required: bool


class CustomFieldResponse(BaseModel):
    field_name: str
    field_type: str
    required: bool


@app.post("/custom_fields", response_model=CustomField, tags=["Custom Field Management"])
async def add_custom_field(custom_field: CustomField):
    """Add a new custom field to a customer's tickets"""
    try:
        success = db_manager.add_custom_field(
            str(custom_field.customer_guid),
            custom_field.field_name,
            custom_field.field_type,
            custom_field.required,
        )
        if success:
            return custom_field
        else:
            raise HTTPException(status_code=400, detail="Failed to add custom field")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/custom_fields", response_model=List[CustomFieldResponse], tags=["Custom Field Management"])
async def list_custom_fields(customer_guid: UUID):
    """List all custom fields for a customer"""
    try:
        # Fetch custom fields for the customer
        fields = db_manager.list_custom_fields(str(customer_guid))

        # Check if fields are empty and raise a 404 if so
        if not fields:
            raise HTTPException(status_code=404, detail=f"No custom fields found for customer {customer_guid}")

        # If fields are found, return them as structured response
        return [
            CustomFieldResponse(
                field_name=field["field_name"],
                field_type=field["field_type"],
                required=field["required"],
            )
            for field in fields
        ]

    except SQLAlchemyError as e:
        # Log database specific errors and raise HTTPException with 500 error
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred.")

    except HTTPException as e:
        raise HTTPException(status_code=404, detail="There is No custom_fields to show")

    except Exception as e:
        # Catch other unexpected errors
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.delete("/custom_fields/{field_name}", tags=["Custom Field Management"])
async def delete_custom_field(field_name: str, customer_guid: UUID = Query(...)):
    """Delete a custom field"""
    try:
        result = db_manager.delete_custom_field(str(customer_guid), field_name)
        if result["status"] == "deleted":
            return {"field_name": field_name, "status": "deleted"}
        elif result["status"] == "not_found":
            return {
                "message": f"Custom field '{field_name}' was not found, no action needed",
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class Ticket(BaseModel):
    ticket_id: str
    chat_id: str
    title: str
    description: str
    priority: str
    status: str
    custom_fields: Optional[Dict[str, Union[str, None]]] = None

class TicketRequest(BaseModel):
    customer_guid: str
    chat_id: str
    title: str
    description: str
    priority: str
    custom_fields: Optional[Dict[str, str]] = None

class TicketResponse(BaseModel):
    ticket_id: str
    status: str

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str]=None
    status: Optional[str] = None
    priority: Optional[str] = None
    custom_fields: Optional[dict[str, Any]] = None

class TicketByChatId(BaseModel):
    ticket_id: str
    title: str
    status: str

@app.post("/tickets", response_model=TicketResponse, tags=["Ticket Management"])
async def create_ticket(ticket: TicketRequest):
    """Create a new ticket"""
    try:
        # Log the received ticket data for debugging
        logger.debug(f"Received ticket data: {ticket}")

        # Call the database method to create the ticket
        db_response = db_manager.create_ticket(
            ticket.customer_guid,
            ticket.chat_id,
            ticket.title,
            ticket.description,
            ticket.priority,
            ticket.custom_fields if ticket.custom_fields else {}  # Directly use the custom_fields dictionary
        )

        if db_response["status"] == "created":
            # Use the ticket_id generated by the database
            return TicketResponse(ticket_id=db_response["ticket_id"], status="created")
        else:
            raise HTTPException(status_code=400, detail="Failed to create ticket")

    except ValueError as e:
        # Handle the ValueError for invalid custom fields
        logger.error(f"Custom field validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Log and return a generic error for unexpected issues
        logger.error(f"Unexpected error in creating ticket: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.get("/tickets/{ticket_id}", response_model=Ticket, tags=["Ticket Management"])
async def get_ticket(ticket_id: str, customer_guid: UUID):
    """Retrieve a ticket by ID"""
    try:
        ticket = db_manager.get_ticket_by_id(ticket_id, str(customer_guid))

        if ticket is None:
            logger.info(f"Ticket with ticket_id {ticket_id} not found for customer {customer_guid}")
            raise HTTPException(status_code=404, detail=f"Ticket with ticket_id {ticket_id} not found for customer {customer_guid}")  # Correctly raise 404 error if not found
        else:
            return ticket
    except HTTPException as e:
        raise HTTPException(status_code=404, detail=f"Ticket with ticket_id {ticket_id} not found for customer {customer_guid}")
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving ticket: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/tickets", response_model=List[TicketByChatId], tags=["Ticket Management"])
async def get_tickets_by_chat_id(customer_guid: UUID, chat_id: str):
    """Retrieve all tickets for a specific chat_id"""
    try:
        ticket = db_manager.get_tickets_by_chat_id(str(customer_guid), chat_id)

        if ticket is None:
            logger.info(f"Ticket with chat_id {chat_id} not found for customer {customer_guid}")
            raise HTTPException(status_code=404, detail=f"Tickets not found for chat_id {chat_id}")  # Correctly raise 404 error if not found
        else:
            return ticket
    except HTTPException as e:
        raise HTTPException(status_code=404, detail=f"Tickets not found for chat_id {chat_id}")
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving ticket: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.put("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Ticket Management"])
async def update_ticket(ticket_id: str, ticket_update: TicketUpdate, customer_guid: str):
    """Update an existing ticket"""
    try:
        updated = db_manager.update_ticket(ticket_id, customer_guid, ticket_update)
        if updated:
            return TicketResponse(ticket_id=ticket_id, status="updated")
        else:
            raise HTTPException(status_code=400, detail="Failed to update ticket")
    except HTTPException as e:
        raise HTTPException(status_code=404, detail=f"Ticket with ticket_id {ticket_id} not found for customer {customer_guid}")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Ticket Management"])
async def delete_ticket(ticket_id: str, customer_guid: str):
    """Delete a ticket and corresponding custom fields"""
    try:
        deleted = db_manager.delete_ticket(ticket_id, customer_guid)
        if deleted:
            return TicketResponse(ticket_id=ticket_id, status="deleted")
        else:
            # If ticket doesn't exist, no action is needed
            return TicketResponse(ticket_id=ticket_id, status=f"Ticket ID {ticket_id} Not exist. No action needed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
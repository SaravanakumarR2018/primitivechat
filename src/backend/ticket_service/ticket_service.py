import logging
from typing import List
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

@app.post("/custom_fields", response_model=CustomField)
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

# ***Need to handle error for empty custom_fields****
@app.get("/custom_fields", response_model=List[CustomFieldResponse])
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


@app.delete("/custom_fields/{field_name}")
async def delete_custom_field(field_name: str, customer_guid: UUID = Query(...)):
    """Delete a custom field"""
    try:
        deleted = db_manager.delete_custom_field(str(customer_guid), field_name)
        if deleted:
            return {"field_name": field_name, "status": "deleted"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"No custom field found with name '{field_name}' to delete",
            )
    except HTTPException as e:
        raise HTTPException(
            status_code=400,
            detail=f"No custom field found with name '{field_name}' to delete",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

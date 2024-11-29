import logging
import uuid
from uuid import UUID
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from src.backend.db.database_manager import DatabaseManager  # Assuming the provided code is in database_connector.py

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DatabaseManager instance
db_manager = DatabaseManager()

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    logger.info(f"Request received with Correlation ID: {correlation_id}")

    response = await call_next(request)

    # Add correlation ID to response headers
    response.headers['X-Correlation-ID'] = correlation_id
    return response


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint at the root path to verify the server is up
@app.get("/", tags=["Health Check"])
async def check_server_status(request: Request):
    logger.debug(f"Entering check_server_status() with Correlation ID: {request.state.correlation_id}")
    logger.debug(f"Exiting check_server_status() with Correlation ID: {request.state.correlation_id}")
    return {"message": "The server is up and running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html

from src.backend.chat_service.chat_service import app as chat_router
from src.backend.ticket_service.ticket_service import app as ticket_router
from src.backend.auth_router.auth_router import app as auth_router
from src.backend.lib.logging_config import log_format
from src.backend.chat_service.llm_service import app as llm_service_router  # Import the LLMService router

# Create the main FastAPI app
main_app = FastAPI()


logging.basicConfig(level=logging.DEBUG, format=log_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Mount chat_service and ticket_service to different paths
main_app.include_router(chat_router)
main_app.include_router(ticket_router)
main_app.include_router(auth_router)
main_app.include_router(llm_service_router, prefix="/llm_service")  # Include the LLMService router

main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@main_app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    logger.debug(f"Request received with Correlation ID: {correlation_id}")

    response = await call_next(request)

    # Add correlation ID to response headers
    response.headers['X-Correlation-ID'] = correlation_id
    return response

# Health check endpoint at the root path to verify the server is up
@main_app.get("/", tags=["Health Check"])
async def check_server_status(request: Request):
    logger.debug(f"Entering check_server_status() with Correlation ID: {request.state.correlation_id}")
    logger.debug(f"Exiting check_server_status() with Correlation ID: {request.state.correlation_id}")
    return {"message": "The server is up and running!"}

# Custom OpenAPI schema with Bearer token support
def custom_openapi():
    if main_app.openapi_schema:
        return main_app.openapi_schema
    openapi_schema = get_openapi(
        title="Main Application API",
        version="1.0.0",
        description="API with Bearer Token support",
        routes=main_app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"  # Optional
        }
    }
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation.setdefault("security", []).append({"BearerAuth": []})
    main_app.openapi_schema = openapi_schema
    return main_app.openapi_schema

main_app.openapi = custom_openapi

@main_app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=main_app.openapi_url,
        title="Main Application - Swagger UI"
    )

# Run this file to start the server
if __name__ == "__main__":
    import uvicorn
    import os

    chat_service_port = int(os.environ.get("CHAT_SERVICE_PORT"))
    uvicorn.run(main_app, host="0.0.0.0", port=chat_service_port, reload=True)

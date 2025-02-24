import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.backend.chat_service.chat_service import app as chat_router
from src.backend.ticket_service.ticket_service import app as ticket_router
from src.backend.auth_router.auth_router import app as auth_router

# Create the main FastAPI app
main_app = FastAPI()


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mount chat_service and ticket_service to different paths
main_app.include_router(chat_router)
main_app.include_router(ticket_router)
main_app.include_router(auth_router)


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
    logger.info(f"Request received with Correlation ID: {correlation_id}")

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

# Run this file to start the server
if __name__ == "__main__":
    import uvicorn
    import os

    chat_service_port = int(os.environ.get("CHAT_SERVICE_PORT"))
    uvicorn.run(main_app, host="0.0.0.0", port=chat_service_port, reload=True)
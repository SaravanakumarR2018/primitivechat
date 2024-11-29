from fastapi import FastAPI
from src.backend.chat_service.chat_service import app as chat_app
from src.backend.ticket_service.ticket_service import app as ticket_app

# Create the main FastAPI app
main_app = FastAPI()

# Mount chat_service and ticket_service to different paths
main_app.mount("/chat", chat_app)
main_app.mount("/ticket", ticket_app)

@main_app.get("/", tags=["Health Check"])
async def check_server_status():
    return {"message": "The server is up and running!"}

# Run this file to start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(main_app, host="0.0.0.0", port=8000, reload=True)

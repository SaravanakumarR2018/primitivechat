import os

import httpx
import jwt  # PyJWT library
from clerk_backend_api import Clerk
from clerk_backend_api.models import ClerkErrors
import logging
from fastapi import APIRouter, HTTPException, Request
from http import HTTPStatus

CLERK_BACKEND_API_KEY="sk_test_E4BB52JT40lgX8O6Nx76e7fdjqb42Z88LAw07zCLZp"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = APIRouter()

BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT', 8000)}"

def decode_token(token):
    # Decode JWT to extract session_id (without verifying signature)
    decoded_token = jwt.decode(token, options={"verify_signature": False})

    # Extract session_id
    session_id = decoded_token.get("sid")
    user_id=decoded_token.get("sub")
    logger.info(f"Decoded Token: {decoded_token}")
    logger.info(f"Session ID: {session_id}")

    return user_id

def get_user_by_id(user_id="user_2s1SvCH01Jd96ww6kSWxdm7cOYb"):
    with Clerk(
            bearer_auth=CLERK_BACKEND_API_KEY,
    ) as clerk:
        response = clerk.users.get(user_id=user_id)

        assert response is not None

        # Handle response
    logger.info(f"Current User Info: {response}" )
    return response

def update_public_metadata(user_id, customer_guid, organization_name):
    try:
        with Clerk(bearer_auth=CLERK_BACKEND_API_KEY) as clerk:
            updated_public_metadata = {
                "organisation": organization_name,
                "customer_guid": customer_guid,
                "roles": ["admin", "agent"]
            }

            response = clerk.users.update(user_id=user_id, public_metadata=updated_public_metadata)
            logging.debug(f"Updated response: {response}")
            return response


    except ClerkErrors as e:
        error_data = e.data  # This is the ClerkErrorsData object
        logging.error(f"Clerk API Error: {error_data}")
        # Assuming the message is within 'errors' and you can access it like this
        if error_data.errors:  # Check if there are any errors
            error_message = error_data.errors[0].message  # Accessing the first error message
            if error_message == "not found":
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail="User not found. Please provide a valid user_id."
                )
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating public metadata."
        )

async def call_add_customer():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/addcustomer")
        return response.json()


@app.post("/create_admin", tags=["Authentication Management"])
async def create_admin(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException( status_code=HTTPStatus.UNAUTHORIZED, detail= "Missing or invalid token")

    body = await request.json()
    organization_name = body.get("organization_name")

    if not organization_name:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Organization name is required")

    token = auth_header.split(" ")[1]
    logger.info(f"token: {token}")

    HARD_CODED_SESSION_TOKEN = "eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDExMUFBQSIsImtpZCI6Imluc18yamhucExZcmtvajVZOWFNdTFQZzJORkNDMVAiLCJ0eXAiOiJKV1QifQ.eyJhenAiOiJodHRwczovL3JlYWN0LXNhYXMuY29tIiwiZXhwIjoxNzM4MTUxNzM4LCJmdmEiOlsxOTA4LC0xXSwiaWF0IjoxNzM4MTUxNjc4LCJpc3MiOiJodHRwczovL2NsZXJrLnJlYWN0LXNhYXMuY29tIiwibmJmIjoxNzM4MTUxNjY4LCJvcmdfaWQiOiJvcmdfMnNGMkdmbTVSVjhSbEJGRGs1MkZ1VTQyOEdYIiwib3JnX3Blcm1pc3Npb25zIjpbXSwib3JnX3JvbGUiOiJvcmc6YWRtaW4iLCJvcmdfc2x1ZyI6Im5ldy1vcmctYW5pLXNhdGlvbiIsInNpZCI6InNlc3NfMnNGMmtHZUR1Z1NYQjNBNnpoaDcyV1c5blEyIiwic3ViIjoidXNlcl8yc0YyOUZZNzlPb29IZFdIeW45bEZJSDh5OHUifQ.e58VDitBlNvzIU9ezjwK7EaI7_P3QEedKJKg_EmVUWuVcf9jYxHw2kxtbs52yxToSkxCLHsRLZvC9PzfqLZfeh-KYp5-HfGQy4OndPhy4YdrnIAxCHWSnWr9yHmYhdm69r6IbiQ6O-SOyfoWfuAon3n3o3fpEc3dKExLPo0yL34aXMu0RZNYddq1bczQq5X7yDU97slKYkaMilKxWhywbmG1LW59fFJtwHLwPMR9tALDxeXNm_VjILCGNkrlweH8VJq6wiWarBJOFrfWjjG9kaElG5GUFZD_to-iwYregWbr0LJPnOCLyp6skbfw1THLW7UJzfPYrrCAoVun31IRkA"
    user_id=decode_token(HARD_CODED_SESSION_TOKEN)
    logger.info(f"user_id: {user_id}")

    current_user=get_user_by_id()
    logger.info(f"Current User Info: {current_user}")

    public_metadata = current_user.public_metadata
    logger.info(f"Private Metadata: {public_metadata}")

    response = await call_add_customer()
    customer_guid=response["customer_guid"]
    logger.info(f"customer_guid: {customer_guid}")

    HARD_CODED_USER_ID="user_2s1SvCH01Jd96ww6kSWxdm7cOYb"

    return update_public_metadata(HARD_CODED_USER_ID, customer_guid,  organization_name)
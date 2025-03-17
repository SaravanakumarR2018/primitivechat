import logging
import os

from clerk_backend_api import Clerk
from clerk_backend_api.jwks_helpers import AuthenticateRequestOptions
from fastapi import APIRouter, Request, HTTPException, Depends
from src.backend.lib.auth_utils import get_decoded_token  # Import the new utility function
from src.backend.lib.utils import auth_admin_dependency
from starlette.responses import JSONResponse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a new router for authentication
app = APIRouter()

# Initialize Clerk client
clerk_client = Clerk(bearer_auth=os.getenv('CLERK_SECRET_KEY'))

@app.get("/checkauth", tags=["Authentication"])
async def check_auth(request: Request, auth=Depends(auth_admin_dependency)):
    try:

        logger.info("Checking authentication status: Calling /checkauth")

        # Authenticate the incoming request
        auth_result = clerk_client.authenticate_request(
            request,
            AuthenticateRequestOptions()
        )

        authenticated = auth_result.is_signed_in
        logger.info(f"Current request authenticated? {authenticated}")

        if not authenticated:
            return JSONResponse(content={"authenticated": False})
        
        # Use the utility function to get the decoded token
        decoded_token = get_decoded_token(request)

        # Fetch user details
        user_details = clerk_client.users.get(user_id=auth_result.payload['sub'])
        if user_details is None:
            logger.error("User details not found")

        # Fetch organization details
        org_details = clerk_client.organizations.get(organization_id=auth_result.payload['org_id'], include_members_count=False)
        if org_details is None:
            logger.error("Organization details not found") 

        #Fetch organisation memberships
        org_memberships = clerk_client.users.get_organization_memberships(user_id=auth_result.payload['sub'], limit=20, offset=0)
        if org_memberships is None:
            logger.error("Organization memberships not found")  

        return JSONResponse(content={
            "authenticated": authenticated,
            "user_details": user_details.dict(),
            "org_details": org_details.dict(),
            "org_memberships": org_memberships.dict(),
            "decoded_token": decoded_token
        })

    except HTTPException as e:
        logger.error(f"Error in check_auth endpoint: {e}")
        raise e
    except Exception as e:
        logger.error(f"Error in check_auth endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

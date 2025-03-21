import logging
from http import HTTPStatus
from src.backend.db.database_manager import DatabaseManager
from src.backend.lib.auth_utils import get_decoded_token
from fastapi import HTTPException, Request
from src.backend.lib.logging_config import log_format
from src.backend.lib.auth_decorator import authenticate_and_check_role

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG, format=log_format)
logger = logging.getLogger(__name__)


async def auth_admin_dependency(request: Request):
    return await authenticate_and_check_role(request, allowed_roles=["org:admin"])

async def auth_admin_member_dependency(request: Request):
    return await authenticate_and_check_role(request, allowed_roles=["org:admin", "org:member"])

async def auth_admin_member_user_dependency(request: Request):
    return await authenticate_and_check_role(request, allowed_roles=["org:admin", "org:member", "org:user"])

class CustomerService:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def get_customer_guid_from_token(self, request: Request):
        decoded_token = get_decoded_token(request)
        org_id = decoded_token.get("org_id")
        if not org_id:
            logger.error("Org ID not found in token")
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Org ID not found in token")

        logger.debug(f"Entering with org_id from token: {org_id}")

        # Check if customer already exists for the given org_id
        customer_guid = self.db_manager.get_customer_guid_from_clerk_orgId(org_id)

        return customer_guid
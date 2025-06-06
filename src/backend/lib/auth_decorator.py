# libs/auth_decorator.py
import logging
import os

import jwt
from clerk_backend_api import Clerk
from clerk_backend_api.jwks_helpers import AuthenticateRequestOptions
from fastapi import HTTPException, Request
from src.backend.lib.config import TEST_TOKEN_PREFIX, TEST_SECRET, JWKS_URL  # Import from config
from src.backend.lib.logging_config import get_primitivechat_logger

logger = get_primitivechat_logger(__name__)

# Initialize Clerk client
clerk_client = Clerk(bearer_auth=os.getenv('CLERK_SECRET_KEY'))

# Retrieve the JWKS URL from environment variables
# JWKS_URL = os.getenv('JWKS_URL') # moved to config
if not JWKS_URL:
    raise ValueError("JWKS_URL is not set in the environment variables.")

# Test token configurations (move to a config file if needed)
# TEST_TOKEN_PREFIX = "test_" # moved to config
# TEST_SECRET = "test_secret" # moved to config

async def call_backend_and_verify_auth(request: Request, allowed_roles: list):
    try:
        logger.info("Calling function for Clerk authentication")
        # Authenticate the incoming request
        auth_result = clerk_client.authenticate_request(
            request,
            AuthenticateRequestOptions()
        )

        # Check if the user is authenticated
        if not auth_result.is_signed_in:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Extract user ID and organization ID from the authentication payload
        user_id = auth_result.payload.get('sub')
        org_id = auth_result.payload.get('org_id')

        if not user_id or not org_id:
            raise HTTPException(status_code=400, detail="User ID or Organization ID missing")

        # Fetch organization memberships for the user
        org_memberships = clerk_client.users.get_organization_memberships(user_id=user_id)

        # Find the membership corresponding to the current organization
        user_role = None
        for membership in org_memberships.data:
            if membership.organization.id == org_id:
                user_role = membership.role
                break

        if not user_role:
            raise HTTPException(status_code=403, detail="User is not a member of the organization")

        # Check if the user's role is in the list of allowed roles
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")

        logger.info("Clerk authentication successful")

    except HTTPException as e:
        logger.error(f"Error in Clerk authentication: {e}")
        raise e
    except Exception as e:
        logger.error(f"Error in Clerk authentication: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def jwt_verifier(request: Request, allowed_roles: list):
    """
    Verify the JWT token and ensure the user has an allowed role.
    """
    try:
        # Extract the token from the Authorization header
        logger.debug("Verifying JWT token")
        authorization: str = request.headers.get('Authorization')
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Authorization header missing or malformed")
        token_parts = authorization.split(' ')
        if len(token_parts) != 2 or not token_parts[1].strip():
            raise HTTPException(status_code=401, detail="Bearer token missing")
        token = token_parts[1].strip()
        # Check if it's a test token
        if token.startswith(TEST_TOKEN_PREFIX):
            try:
                logger.debug("Verifying test token")
                # Remove the test prefix before decoding
                test_token = token[len(TEST_TOKEN_PREFIX):]
                logger.debug(f"Decoding test token {test_token}")
                decoded_token = jwt.decode(test_token, TEST_SECRET, algorithms=["HS256"])  # Use a specific algorithm
                logger.debug(f"Decoded test token {decoded_token}")
                user_role = decoded_token.get('org_role')
                if user_role not in allowed_roles:
                    raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
                logger.debug("Test JWT authentication successful")
                return  # Test token is valid, exit the function
            except jwt.DecodeError:
                raise HTTPException(status_code=401, detail="Invalid test token")

        # If not a test token, proceed with JWKS verification
        jwk_client = jwt.PyJWKClient(JWKS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(token)  # Pass JWT, not JWKS
        public_key = signing_key.key
        options = {
            'verify_exp': True,
            'verify_nbf': True,
        }
        CLOCK_TOLERANCE = 300  # 5 minutes
        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            options=options,
            leeway=CLOCK_TOLERANCE
        )
        user_role = decoded_token.get('org_role')
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
        logger.info("JWT authentication successful")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.ImmatureSignatureError:
        raise HTTPException(status_code=401, detail="Token is not yet valid")
    except jwt.InvalidTokenError:
        try:
            logger.debug("Retrying JWT verification after fetching public key")
            jwk_client = jwt.PyJWKClient(JWKS_URL)
            signing_key = jwk_client.get_signing_key_from_jwt(token)  # Pass JWT, not JWKS
            public_key = signing_key.key
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                options=options,
                leeway=CLOCK_TOLERANCE
            )
            user_role = decoded_token.get('org_role')
            if user_role not in allowed_roles:
                raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
            logger.info("JWT authentication successful after retry")
        except Exception as e:
            if isinstance(e, HTTPException) and e.status_code == 403:
                logger.info(f"JWT verification failed with 403: {e}")
                raise e
            else:
                logger.error(f"JWT verification failed after retry: {e}")
                raise HTTPException(status_code=401, detail="Invalid token after retrying public key fetch")

async def authenticate_and_check_role(request: Request, allowed_roles: list):
    """Dependency to authenticate and authorize based on roles."""
    if request is None:
        raise HTTPException(status_code=400, detail="Request object is required")
    try:
        await jwt_verifier(request, allowed_roles)
    except HTTPException as e:
        if e.status_code == 403:
            logger.info(f"JWT verification failed with 403: {e}")
            raise e
        else:
            logger.error(f"JWT verification failed: {e}. Calling Clerk to verify authentication")
            await call_backend_and_verify_auth(request, allowed_roles)
    except Exception as e:
        logger.error(f"JWT verification failed: {e}. Calling Clerk to verify authentication")
        await call_backend_and_verify_auth(request, allowed_roles)

    return request  # Return request for further processing if needed
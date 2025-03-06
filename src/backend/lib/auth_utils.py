import jwt
from fastapi import Request, HTTPException
from src.backend.lib.config import TEST_TOKEN_PREFIX, TEST_SECRET


def get_decoded_token(request: Request):
    """
    Retrieve the authorization header from the request and decode the JWT token.
    Handles test tokens differently.
    """
    # Retrieve the token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.split(' ')[1]

    # Check if it's a test token
    if token.startswith(TEST_TOKEN_PREFIX):
        try:
            # Remove the test prefix before decoding
            test_token = token[len(TEST_TOKEN_PREFIX):]
            decoded_token = jwt.decode(test_token, TEST_SECRET, algorithms=["HS256"])  # Use a specific algorithm
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="Invalid test token")
    else:
        # Decode the JWT token
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="Invalid token")

    return decoded_token



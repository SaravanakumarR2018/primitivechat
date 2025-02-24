import jwt
from fastapi import Request, HTTPException

def get_decoded_token(request: Request):
    """
    Retrieve the authorization header from the request and decode the JWT token.
    """
    # Retrieve the token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.split(' ')[1]

    # Decode the JWT token
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return decoded_token
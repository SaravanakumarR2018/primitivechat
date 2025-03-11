import requests
import logging
import os
import uuid
import jwt
from src.backend.lib.config import TEST_TOKEN_PREFIX, TEST_SECRET
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

def create_test_token(
    org_id: str,
    org_role: str,
    azp: str = "http://localhost:3000",
    # exp: int = 1741280040, # Remove the default expiry
    fva: list = [2, -1],
    iat: int = int(time.time()), # Set iat to current time
    iss: str = "https://valued-phoenix-52.clerk.accounts.dev",
    nbf: int = 1741279970,
    org_permissions: list = [],
    org_slug: str = "simple",
    sid: str = "sess_2tx3NSrSqGUYSSVpgp58jImNzLq",
    sub: str = "user_2t4DF5pHXlYpHZ6n5yjVzFVrctQ",
    expiry_in_seconds: int = 365 * 24 * 3600 # Add expiry time
):
    """
    Creates a test token given a set of optional parameters.
    org_id and org_role are required.
    """
    payload = {
        "azp": azp,
        "exp": int(time.time()) + expiry_in_seconds, # Set expiry time
        "fva": fva,
        "iat": iat,
        "iss": iss,
        "nbf": nbf,
        "org_id": org_id,
        "org_permissions": org_permissions,
        "org_role": org_role,
        "org_slug": org_slug,
        "sid": sid,
        "sub": sub,
    }
    encoded_token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
    return TEST_TOKEN_PREFIX + encoded_token


def make_api_request(org_id: str, org_role: str, url: str, method: str, payload: dict = None, headers: dict = None):
    """
    Makes an API request with a test token in the header.

    Args:
        org_id: The organization ID to include in the token.
        org_role: The organization role to include in the token.
        url: The URL to make the request to.
        method: HTTP method to use (e.g., "GET", "POST", "PUT", "DELETE").
        payload: The request payload (dictionary). Defaults to None.
        headers: The request headers (dictionary). Defaults to None.

    Returns:
        The JSON response from the API.
    """
    if headers is None:
        headers = {}

    # Create a test token
    token = create_test_token(org_id=org_id, org_role=org_role)

    # Add the token to the headers
    headers['Authorization'] = f'Bearer {token}'

    logger.info(f"Sending {method} request to {url} with payload: {payload} and headers: {headers}")

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=payload)  # Use params for GET payload
        elif method == "POST":
            response = requests.post(url, json=payload, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=payload, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, json=payload)  # Some DELETE requests might need a body
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise e


def add_customer(org_id: str):
    unique_id = str(uuid.uuid4())  # Generate a UUID
    merged_org_id = f"{org_id}_{unique_id}"  # Merge org_id with UUID

    url = f"{BASE_URL}/addcustomer"
    headers = {"Content-Type": "application/json"}

    logger.info(f"Generated unique org_id: {merged_org_id}")
    logger.info(f"Sending POST request to {url}")

    try:
        response = make_api_request(org_id=merged_org_id, org_role="org:admin", url=url, method="POST", headers=headers)
        #response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        data = response

        logger.debug(f"Response Data: {data}")

        if "customer_guid" not in data:
            raise ValueError("'customer_guid' not found in response data.")

        data["org_id"] = merged_org_id

        logger.info(f"Successfully added customer. Received response: {data}")
        return data

    except requests.RequestException as e:
        logger.error(f"Failed to add customer: {e}")
        raise e



# Example Usage
if __name__ == "__main__":
    # customer_data = add_customer("test_org_1234")
    # print("Customer Data:", customer_data)

    # Example usage of make_api_request
    api_url = f"{BASE_URL}/addcustomer"  # Replace with your actual API endpoint
    api_payload = {}  # Replace with your actual payload
    api_headers = {"Content-Type": "application/json"}

    try:
        response_data = make_api_request(
            org_id="test_org_123",
            org_role="org:admin",
            url=api_url,
            method="POST",
            payload=api_payload,
            headers=api_headers
        )
        print("API Response:", response_data)
    except Exception as e:
        print(f"Error: {e}")

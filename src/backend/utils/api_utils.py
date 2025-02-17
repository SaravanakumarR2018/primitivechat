import requests
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT', 8000)}"


def add_customer(org_id: str):
    """
    Sends a request to add a customer and returns the response data.

    :param org_id: Organization ID for the customer.
    :return: Response JSON containing 'customer_guid'.
    :raises: Exception if the request fails.
    """
    url = f"{BASE_URL}/addcustomer"
    payload = {"org_id": org_id}
    headers = {"Content-Type": "application/json"}

    logger.info(f"Sending POST request to {url} with payload: {payload}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        data = response.json()

        if "customer_guid" not in data:
            raise ValueError("'customer_guid' not found in response data.")

        logger.info(f"Successfully added customer. Received response: {data}")
        return data

    except requests.RequestException as e:
        logger.error(f"Failed to add customer: {e}")
        raise

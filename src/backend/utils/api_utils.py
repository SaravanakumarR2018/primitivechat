import requests
import logging
import os
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT', 8000)}"

def add_customer(org_id: str):
    unique_id = str(uuid.uuid4())  # Generate a UUID
    merged_org_id = f"{org_id}_{unique_id}"  # Merge org_id with UUID

    url = f"{BASE_URL}/addcustomer"
    payload = {"org_id": merged_org_id}
    headers = {"Content-Type": "application/json"}

    logger.info(f"Generated unique org_id: {merged_org_id}")
    logger.info(f"Sending POST request to {url} with payload: {payload}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        data = response.json()

        logger.debug(f"Response Data: {data}")

        if "customer_guid" not in data:
            raise ValueError("'customer_guid' not found in response data.")

        logger.info(f"Successfully added customer. Received response: {data}")
        return data

    except requests.RequestException as e:
        logger.error(f"Failed to add customer: {e}")
        raise

# Example Usage
if __name__ == "__main__":
    customer_data = add_customer("test_org_1234")
    print("Customer Data:", customer_data)

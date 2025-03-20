import logging
import os
import unittest
import requests

from src.backend.lib.logging_config import log_format
from utils.api_utils import add_customer, create_token_without_org_id, create_token_without_org_role

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

class TestAddCustomerAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def test_add_customer(self):
        """Test that a customer can be added successfully."""
        logger.info("Executing test_add_customer: Testing customer addition functionality.")
        start_org_id = "test_org"
        data = add_customer(start_org_id)

        logger.info("Processing response data to check for 'customer_guid'.")

        self.assertIn("customer_guid", data, "'customer_guid' not found in response data.")
        self.assertIn("org_id", data, "'org_id' not found in response data.")
        logger.info("'customer_guid' and 'org_id' found in response data, verifying their types.")

        self.assertIsInstance(data["customer_guid"], str, "'customer_guid' is not a string.")
        self.assertIsInstance(data["org_id"], str, "'org_id' is not a string.")

        self.assertTrue(data["org_id"].startswith(start_org_id), f"org_id does not start with {start_org_id}")

        logger.info("Test completed successfully for test_add_customer.")
        
    def test_addcustomer_without_token(self):
        logger.info("Executing addcustomer_without_token: Testing error handling for missing token")

        url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(url)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 401)
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Authentication required")
        logger.info("Test completed successfully for test_addcustomer_without_token.")

    def test_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        headers = {"Authorization": "Bearer corrupted_token"}
        url = f"{self.BASE_URL}/addcustomer"

        logger.info("Testing API request with corrupted token")
        response = requests.post(url, headers=headers)
        self.assertEqual(response.status_code, 401, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")
        logger.info("Test completed successfully test_corrupted_token")

    def test_addcustomer_token_without_org_role(self):
        logger.info("Testing addcustomer API with a token missing org_role")
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")

        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(url, headers=headers)

        self.assertEqual(response.status_code, 403, "Expected status code 403 for missing org_role")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

        logger.info("Test completed successfully test_addcustomer_token_without_org_role")

    def test_addcustomer_token_without_org_id(self):
        logger.info("Testing addcustomerAPI with a token missing org_id")

        headers = {'Authorization': f'Bearer {create_token_without_org_id("org:admin")}'}
        url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(url, headers=headers)

        # Expect 400 Bad Request
        self.assertEqual(response.status_code, 400, "Expected status code 400 for missing org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

        logger.info("Test completed successfully test_addcustomer_token_without_org_id")


if __name__ == "__main__":
    unittest.main()

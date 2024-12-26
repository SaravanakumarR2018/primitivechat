import unittest
from http import HTTPStatus
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestDeleteCustomFieldAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"

    def setUp(self):
        """Setup function to initialize valid customer GUID and custom field."""
        logger.info("=== Initializing test setup ===")

        # Assuming an endpoint `/addcustomer` to create a new customer
        customer_url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(customer_url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create customer")
        self.valid_customer_guid = response.json().get("customer_guid")
        logger.info(f"Valid customer_guid initialized: {self.valid_customer_guid}")

        # Adding custom fields for the valid customer
        custom_field_url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "test_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        response = requests.post(custom_field_url, json=data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to add custom field during setup")

    def test_delete_custom_field_success(self):
        """Test deleting a custom field successfully."""
        url = f"{self.BASE_URL}/custom_fields/{'test_field'}?customer_guid={self.valid_customer_guid}"
        logger.info("Testing positive case for deleting custom field.")
        response = requests.delete(url)

        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete custom field")
        response_data = response.json()
        self.assertEqual(response_data["field_name"], "test_field")
        self.assertEqual(response_data["status"], "deleted")
        logger.info("Positive test case for deleting custom field passed.")

    def test_delete_custom_field_not_found(self):
        """Test deleting a custom field that doesn't exist."""
        url = f"{self.BASE_URL}/custom_fields/{'non_existent_field'}?customer_guid={self.valid_customer_guid}"
        logger.info("Testing deletion of non-existent custom field.")
        response = requests.delete(url)

        self.assertEqual(response.status_code, HTTPStatus.OK, "Expected 200 even when field does not exist")
        response_data = response.json()
        self.assertEqual(response_data["field_name"], "non_existent_field")
        self.assertEqual(response_data["status"], "deleted")
        logger.info("Negative test case for deleting non-existent custom field passed.")

    def test_delete_custom_field_invalid_customer_guid(self):
        """Test deleting a custom field with an invalid customer GUID."""
        invalid_customer_guid = "ae0ae9ed-26dd-4319-9f40-0354990ad101"
        url = f"{self.BASE_URL}/custom_fields/{'test_field'}?customer_guid={invalid_customer_guid}"
        logger.info(f"Testing deletion with invalid customer GUID: {invalid_customer_guid}")
        response = requests.delete(url)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid customer GUID should result in 400")
        self.assertIn(f"Database customer_{invalid_customer_guid} does not exist", response.text)
        logger.info("Negative test case for invalid customer GUID passed.")

    def tearDown(self):
        """Clean up resources if necessary."""
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

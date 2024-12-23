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

class TestListCustomFieldsAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"

    def setUp(self):
        """Setup function to initialize valid customer GUID."""
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
            "field_name": "test_field12",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        response = requests.post(custom_field_url, json=data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to add custom field during setup")

    def test_list_custom_fields_positive(self):
        """Test listing custom fields for a valid customer."""
        url = f"{self.BASE_URL}/custom_fields?customer_guid={self.valid_customer_guid}"
        logger.info("Testing positive case for listing custom fields.")
        response = requests.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to list custom fields")
        response_data = response.json()

        self.assertIsInstance(response_data, list, "Response should be a list")
        self.assertGreater(len(response_data), 0, "Custom fields list should not be empty")
        self.assertEqual(response_data[0]["field_name"], "test_field12")
        self.assertEqual(response_data[0]["field_type"], "VARCHAR(255)")
        self.assertTrue(response_data[0]["required"])
        logger.info("Positive test case for listing custom fields passed.")

    def test_list_custom_fields_invalid_customer_guid(self):
        """Test listing custom fields for an invalid customer GUID."""
        invalid_customer_guid = "ae0ae9ed-26dd-4319-9f40-0354990ad101"
        url = f"{self.BASE_URL}/custom_fields?customer_guid={invalid_customer_guid}"
        logger.info(f"Testing invalid customer GUID: {invalid_customer_guid}")
        response = requests.get(url)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid customer GUID should result in 400")
        self.assertIn("Database customer_ae0ae9ed-26dd-4319-9f40-0354990ad101 does not exist", response.text)
        logger.info("Negative test case for invalid customer GUID passed.")

    def test_list_custom_fields_no_fields(self):
        """Test listing custom fields for a customer with no fields."""
        # Create a new customer without adding custom fields
        customer_url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(customer_url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create customer")
        new_customer_guid = response.json().get("customer_guid")

        url = f"{self.BASE_URL}/custom_fields?customer_guid={new_customer_guid}"
        logger.info(f"Testing customer with no custom fields: {new_customer_guid}")
        response = requests.get(url)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "No custom fields should result in 404")
        self.assertIn(f"No custom fields found for customer {new_customer_guid}", response.text)
        logger.info("Negative test case for no custom fields passed.")

    def tearDown(self):
        """Clean up resources if necessary."""
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

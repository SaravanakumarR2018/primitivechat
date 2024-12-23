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

class TestCustomFieldAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"
    MYSQL_CONTAINER_NAME = "mysql_db"

    def setUp(self):
        """Setup function to initialize valid customer GUID."""
        logger.info("=== Initializing test setup ===")

        # Assuming an endpoint `/addcustomer` to create a new customer
        customer_url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(customer_url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create customer")
        self.valid_customer_guid = response.json().get("customer_guid")
        logger.info(f"Valid customer_guid initialized: {self.valid_customer_guid}")

    def test_add_valid_custom_field(self):
        """Test adding a valid custom field."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "test_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        logger.info(f"Testing valid custom field addition with data: {data}")
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to add custom field")
        response_data = response.json()
        self.assertEqual(response_data["field_name"], "test_field")
        logger.info("Test case for valid custom field addition passed.")

    def test_add_custom_field_missing_required_field(self):
        """Test adding a custom field with missing required field."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "missing_required_field",
            "field_type": "VARCHAR(255)"
            # 'required' field is missing
        }
        logger.info(f"Testing missing 'required' field with data: {data}")
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY, "Missing required field should result in 422")
        self.assertIn("field required", response.text.lower())
        logger.info("Test case for missing required field passed.")

    def test_add_custom_field_invalid_customer_guid(self):
        """Test adding a custom field with invalid customer_guid."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": "256128e2-b963-4019-b870-d6e82db0d631", # Invalid or random customer_guid
            "field_name": "test_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        logger.info(f"Testing invalid customer GUID with data: {data}")
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid customer_guid should result in 400")
        self.assertIn(f"Database customer_{data['customer_guid']} does not exist", response.text)
        logger.info("Test case for invalid customer_guid passed.")

    def test_add_duplicate_custom_field_name(self):
        """Test adding a custom field with a duplicate field name."""
        url = f"{self.BASE_URL}/custom_fields"
        initial_data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "duplicate_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }

        # Add the custom field for the first time
        logger.info(f"Adding initial custom field with data: {initial_data}")
        response = requests.post(url, json=initial_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to add the initial custom field")

        # Add the same custom field with identical data
        duplicate_data_matching = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "duplicate_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        logger.info(f"Adding duplicate custom field with matching data: {duplicate_data_matching}")
        response = requests.post(url, json=duplicate_data_matching)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Duplicate field with matching data should result in 200")

        # Add the same custom field with conflicting data
        duplicate_data_conflicting = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "duplicate_field",
            "field_type": "INT",  # Different field_type
            "required": False  # Different required value
        }
        logger.info(f"Adding duplicate custom field with conflicting data: {duplicate_data_conflicting}")
        response = requests.post(url, json=duplicate_data_conflicting)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Duplicate field with conflicting data should result in 400")
        self.assertIn(
            f"A custom field with this name {duplicate_data_conflicting['field_name']} already exists, but the field type or required flag differs.",
            response.text
        )
        logger.info("Duplicate custom field with conflicting data test case passed.")

    def test_add_custom_field_invalid_field_type(self):
        """Test adding a custom field with an invalid field type."""
        url = f"{self.BASE_URL}/custom_fields"
        invalid_field_type = "INVALID_TYPE"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "invalid_field_type_test",
            "field_type": invalid_field_type,
            "required": True
        }

        # Attempt to add a custom field with an invalid field type
        logger.info(f"Testing invalid field type with data: {data}")
        response = requests.post(url, json=data)

        # Assert that the API returns a 400 status code
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid field type should result in 400")

        # Expected error response
        expected_message = {
            "detail": f"Unsupported field type: {invalid_field_type}. Allowed types are: VARCHAR(255), MEDIUMTEXT, BOOLEAN, INT, DATE"
        }

        # Convert the response to JSON for comparison
        actual_response = response.json()

        # Assert the entire response matches the expected structure
        self.assertEqual(actual_response, expected_message, "Response does not match the expected structure")

        logger.info("Test case for invalid field type passed.")

    def tearDown(self):
        """Clean up resources if necessary."""
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

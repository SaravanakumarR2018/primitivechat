import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer, create_test_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestCustomFieldAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"
    MYSQL_CONTAINER_NAME = "mysql_db"
    ORG_ROLE='org:admin'

    def setUp(self):
        """Setup function to initialize valid customer GUID."""
        logger.info("=== Initializing test setup ===")

        self.headers = {}

        # Assuming an endpoint `/addcustomer` to create a new customer
        self.data =  add_customer("test_org")
        self.valid_customer_guid=self.data.get("customer_guid")
        self.org_id=self.data.get("org_id")

        #Create Test Token
        self.token = create_test_token(org_id=self.org_id, org_role=self.ORG_ROLE)
        self.headers['Authorization'] = f'Bearer {self.token}'
        logger.info(f"Valid customer_guid initialized: {self.valid_customer_guid}")
        logger.info(f"Starting test: {self._testMethodName}")

    def test_add_valid_custom_field(self):
        """Test adding a valid custom field."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "field_name": "test_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        logger.info(f"Testing valid custom field addition with data: {data}")
        response = requests.post(url, json=data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to add custom field")
        response_data = response.json()
        self.assertEqual(response_data["field_name"], "test_field")
        logger.info("Test case for valid custom field addition passed.")

    def test_add_custom_field_missing_required_field(self):
        """Test adding a custom field with missing required field."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "field_name": "missing_required_field",
            "field_type": "VARCHAR(255)"
            # 'required' field is missing
        }
        logger.info(f"Testing missing 'required' field with data: {data}")
        response = requests.post(url, json=data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY, "Missing required field should result in 422")
        self.assertIn("required", response.text.lower())
        logger.info("Test case for missing required field passed.")

    def test_add_custom_field_invalid_org_id_or_customer_guid(self):
        """Test adding a custom field with an invalid org_id."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "field_name": "test_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        invalid_token = create_test_token(org_id="invalid_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}

        logger.info(f"Testing invalid org_id with data: {data}")
        response = requests.post(url, json=data, headers=headers)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid org_id/customer_guid should result in 400")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Test case for invalid org_id/customer_guid passed.")

    def test_add_duplicate_custom_field_name(self):
        """Test adding a custom field with a duplicate field name."""
        url = f"{self.BASE_URL}/custom_fields"
        initial_data = {
            "field_name": "duplicate_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }

        # Add the custom field for the first time
        logger.info(f"Adding initial custom field with data: {initial_data}")
        response = requests.post(url, json=initial_data, headers=self.headers)
        logger.info(f"Response: {response.status_code}, Payload: {response.json()}")
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to add the initial custom field")
        response_data = response.json()
        for key, value in initial_data.items():
            self.assertEqual(response_data.get(key), value, f"Response should include the correct {key} value")

        # Add the same custom field with identical data
        duplicate_data_matching = {
            "field_name": "duplicate_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        logger.info(f"Adding duplicate custom field with matching data: {duplicate_data_matching}")
        response = requests.post(url, json=duplicate_data_matching, headers=self.headers)
        logger.info(f"Response: {response.status_code}, Payload: {response.json()}")
        self.assertEqual(response.status_code, HTTPStatus.CREATED,
                         "Duplicate field with matching data should result in 200")
        response_data = response.json()
        for key, value in duplicate_data_matching.items():
            self.assertEqual(response_data.get(key), value, f"Response should include the correct {key} value")

        # Add the same custom field with conflicting data
        duplicate_data_conflicting = {
            "field_name": "duplicate_field",
            "field_type": "INT",  # Different field_type
            "required": False  # Different required value
        }
        logger.info(f"Adding duplicate custom field with conflicting data: {duplicate_data_conflicting}")
        response = requests.post(url, json=duplicate_data_conflicting, headers=self.headers)
        logger.info(f"Response: {response.status_code}, Payload: {response.json()}")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                         "Duplicate field with conflicting data should result in 400")
        self.assertIn(
            f"A custom field with this name {duplicate_data_conflicting['field_name']} already exists, but the field type or required flag differs.",
            response.text,
            "Error message for conflicting duplicate should be present in the response"
        )
        logger.info("Duplicate custom field with conflicting data test case passed.")

    def test_add_custom_field_invalid_field_type(self):
        """Test adding a custom field with an invalid field type."""
        url = f"{self.BASE_URL}/custom_fields"
        invalid_field_type = "INVALID_TYPE"
        data = {
            "field_name": "invalid_field_type_test",
            "field_type": invalid_field_type,
            "required": True
        }

        # Attempt to add a custom field with an invalid field type
        logger.info(f"Testing invalid field type with data: {data}")
        response = requests.post(url, json=data, headers=self.headers)

        # Assert that the API returns a 400 status code
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid field type should result in 400")

        # Expected error response
        expected_message = {
            "detail": f"Unsupported field type: {invalid_field_type}. Allowed types are: VARCHAR(255), INT, BOOLEAN, DATETIME, MEDIUMTEXT, FLOAT, TEXT"
        }

        # Convert the response to JSON for comparison
        actual_response = response.json()

        # Assert the entire response matches the expected structure
        self.assertEqual(actual_response, expected_message, "Response does not match the expected structure")

        logger.info("Test case for invalid field type passed.")

    def test_add_custom_field_empty_field_name(self):
        """Test adding a custom field with an empty field name."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "",  # Empty field name
            "field_type": "VARCHAR(255)",  # Valid field type
            "required": True
        }

        # Attempt to add a custom field with an empty field name
        logger.info(f"Testing empty field name with data: {data}")
        response = requests.post(url, json=data, headers=self.headers)

        # Assert that the API returns a 400 status code
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Empty field name should result in 400")

        # Expected error response
        expected_message = {
            "detail": "Invalid field name ''. Field names can only contain letters, numbers, and underscores."
        }

        # Convert the response to JSON for comparison
        actual_response = response.json()

        # Assert the entire response matches the expected structure
        self.assertEqual(actual_response, expected_message, "Response does not match the expected structure")

        logger.info("Test case for empty field name passed.")

    def test_add_custom_field_varchar(self):
        self._test_add_custom_field("VARCHAR(255)")

    def test_add_custom_field_int(self):
        self._test_add_custom_field("INT")

    def test_add_custom_field_boolean(self):
        self._test_add_custom_field("BOOLEAN")

    def test_add_custom_field_date(self):
        self._test_add_custom_field("DATETIME")

    def test_add_custom_field_mediumtext(self):
        self._test_add_custom_field("MEDIUMTEXT")

    def test_add_custom_field_float(self):
        self._test_add_custom_field("FLOAT")

    def test_add_custom_field_text(self):
        self._test_add_custom_field("TEXT")

    def _test_add_custom_field(self, field_type):
        """Helper method to test adding a custom field with a specific type."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "field_name": f"test_field_{field_type.lower().replace('(', '').replace(')', '').replace(' ', '_')}",
            "field_type": field_type,
            "required": True
        }
        logger.info(f"Testing custom field addition with field type: {field_type} and data: {data}")
        response = requests.post(url, json=data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to add custom field with type {field_type}")
        response_data = response.json()
        self.assertEqual(response_data["field_name"], data["field_name"])
        self.assertEqual(response_data["field_type"], data["field_type"])
        self.assertTrue(response_data["required"])
        logger.info(f"Test case for custom field with type {field_type} passed.")

    def test_invalid_required_field_value(self):
        """Test providing invalid values for the 'required' field."""
        invalid_values = ["Yes", "No", 123, None, {}, []]
        for value in invalid_values:
            with self.subTest(value=value):
                url = f"{self.BASE_URL}/custom_fields"
                data = {
                    "field_name": "test_invalid_required",
                    "field_type": "VARCHAR(255)",
                    "required": value
                }
                logger.info(f"Testing invalid required field value: {value} with data: {data}")
                response = requests.post(url, json=data, headers=self.headers)

                # Assert response status code
                self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY,
                                 f"Expected 422 for required field value: {value}")

                logger.info(f"Testtest_invalid_required_field_value case for invalid required field value {value} passed.")

    def test_field_name_too_long(self):
        """Test providing a 'field_name' value that exceeds the maximum allowed length."""
        long_field_name = "this_field_name_is_way_too_long_and_should_cause_an_error_because_it_exceeds_the_max_length_allowed_by_mysql"
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": long_field_name,
            "field_type": "VARCHAR(255)",
            "required": True
        }
        logger.info(f"Testing long field_name with length {len(long_field_name)}: {long_field_name}")
        response = requests.post(url, json=data, headers=self.headers)

        # Assert response status code
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                         "Expected BAD_REQUEST for overly long field_name")

        # Parse response data
        response_data = response.json()

        # Assert error detail in response
        expected_error_message = (
            f"Field name '{long_field_name[:20]}...' is too long. The maximum length allowed is 64 characters."
        )
        self.assertIn("detail", response_data, "Error message key 'detail' is missing in response")
        self.assertEqual(response_data["detail"], expected_error_message,
                         f"Unexpected error message for long field_name: {long_field_name}")

        logger.info(f"Test case for overly long field_name passed.")

    def tearDown(self):
        """Clean up resources if necessary."""
        logger.info(f"Finished test: {self._testMethodName}")
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

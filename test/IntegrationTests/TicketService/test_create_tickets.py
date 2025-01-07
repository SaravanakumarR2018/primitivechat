import logging
import os
import unittest
from http import HTTPStatus

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestCreateTicketAPI(unittest.TestCase):
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT')}"

    allowed_custom_field_sql_types = ["VARCHAR(255)", "INT", "BOOLEAN", "DATETIME", "MEDIUMTEXT", "FLOAT", "TEXT"]

    def setUp(self):
        """Set up test environment: create customer, chat, and custom fields."""
        logger.info("=== Setting up test environment ===")

        # Add customer
        customer_url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(customer_url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create a customer")
        self.valid_customer_guid = response.json().get("customer_guid")

        # Add chat
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "Initial question"
        }
        response = requests.post(chat_url, json=chat_data)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create a chat")
        self.valid_chat_id = response.json().get("chat_id")

        # Add custom fields
        custom_fields_url = f"{self.BASE_URL}/custom_fields"
        self.custom_fields = {}
        for field_type in self.allowed_custom_field_sql_types:
            field_name = f"field_{field_type.split('(')[0].lower()}"
            payload = {
                "customer_guid": self.valid_customer_guid,
                "field_name": field_name,
                "field_type": field_type,
                "required": False
            }
            response = requests.post(custom_fields_url, json=payload)
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create custom field {field_name}")
            self.custom_fields[field_name] = field_type

        logger.info(f"Test setup complete: customer_guid={self.valid_customer_guid}, chat_id={self.valid_chat_id}")
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_create_ticket_with_out_custom_fields(self):
        """Test creating a ticket with valid custom field values."""
        url = f"{self.BASE_URL}/tickets"
        payload = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "title": "Valid Custom Fields Test",
            "description": "This ticket has valid custom fields.",
            "priority": "low",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }

        logger.info("Testing ticket creation with valid custom field values.")
        response = requests.post(url, json=payload)

        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Ticket creation with valid custom fields should return 201.")
        self.assertIn("ticket_id", response.json())
        logger.info("Positive test case for valid custom fields passed.")

    def test_create_ticket_with_valid_custom_fields(self):
        """Test creating a ticket with valid custom field values."""
        url = f"{self.BASE_URL}/tickets"
        payload = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "title": "Valid Custom Fields Test",
            "description": "This ticket has valid custom fields.",
            "priority": "low",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com",
            "custom_fields": {
                "field_varchar": "Sample text",
                "field_int": 42, #int field can accept int, string of int values ("42")
                "field_boolean": True, #boolean types can accept true, false, "0", "1"
                "field_datetime": "2023-12-31 23:59:59",
                "field_mediumtext": "A" * 1000,
                "field_float": 42.42, #float field can accept float, string of float values ("42.0"), int (42)
                "field_text": "Short text"
            }
        }

        logger.info("Testing ticket creation with valid custom field values.")
        response = requests.post(url, json=payload)

        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Ticket creation with valid custom fields should return 201.")
        self.assertIn("ticket_id", response.json())
        logger.info("Positive test case for valid custom fields passed.")

    def test_create_ticket_with_individual_invalid_custom_field_values(self):
        """Test creating a ticket with each invalid custom field value individually."""
        url = f"{self.BASE_URL}/tickets"

        invalid_custom_fields = {
            "field_int": "1.0",  # Invalid: INT should not accept string, float, string of int, string of float
            "field_float": "string",  # Invalid: FLOAT should not accept string
            "field_boolean": "string_value", # Invalid: BOOLEAN should not accept strings or string of boolean ("true", "false") except "0" or "1"
            "field_datetime": "31-12-2023",  # Invalid: incorrect format and without timestamp
            "field_varchar": 123,  # Invalid: VARCHAR should not accept non-string
            "field_text": False,  # Invalid: TEXT should not accept boolean
            "field_mediumtext": 1000,  # Invalid: TEXT should not accept boolean, int, float
        }

        for field, invalid_value in invalid_custom_fields.items():
            with self.subTest(field=field, value=invalid_value):
                payload = {
                    "customer_guid": self.valid_customer_guid,
                    "chat_id": self.valid_chat_id,
                    "title": f"Invalid Custom Field Test for {field}",
                    "description": f"Testing invalid value for {field}.",
                    "priority": "medium",
                    "reported_by": "user@example.com",
                    "assigned": "agent@example.com",
                    "custom_fields": {
                        field: invalid_value
                    }
                }

                logger.info(f"Testing {field} with invalid value: {invalid_value}")
                response = requests.post(url, json=payload)

                # Assert the API returns a 400 BAD REQUEST
                self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                                 f"Invalid value for {field} should return 400.")
                response_data = response.json()

                # Assert the error message contains the invalid field
                self.assertIn(field, response_data.get("detail", {}), f"Error for {field} should be in response.")

        logger.info("Negative test case for individual invalid custom fields passed.")

    def test_create_ticket_invalid_priority(self):
        """Test creating a ticket with an invalid priority."""
        url = f"{self.BASE_URL}/tickets"
        payload = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "title": "Invalid Priority Test",
            "description": "Testing invalid priority field.",
            "priority": "urgent",  # Invalid priority
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }

        logger.info("Testing ticket creation with invalid priority.")
        response = requests.post(url, json=payload)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid priority should return 400.")
        self.assertIn("Invalid priority", response.text)
        logger.info("Negative test case for invalid priority passed.")

    def test_create_ticket_with_missing_required_custom_fields(self):
        """Test creating a ticket with each required custom field missing its value."""
        url = f"{self.BASE_URL}/tickets"
        custom_fields_url = f"{self.BASE_URL}/custom_fields"

        # Iterate over all allowed custom field types and create each with 'required' set to True
        for field_type in self.allowed_custom_field_sql_types:
            field_name = f"required_field_{field_type.split('(')[0].lower()}"
            payload = {
                "customer_guid": self.valid_customer_guid,
                "field_name": field_name,
                "field_type": field_type,
                "required": True
            }
            response = requests.post(custom_fields_url, json=payload)
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create custom field {field_name}")
            logger.info(f"Created custom field {field_name} with required:true")

            # Now test ticket creation with the custom field missing
            logger.info(f"Testing ticket creation with missing required custom field {field_name}")

            ticket_payload = {
                "customer_guid": self.valid_customer_guid,
                "chat_id": self.valid_chat_id,
                "title": f"Ticket without {field_name}",
                "description": f"This ticket does not include the required custom field '{field_name}'.",
                "priority": "medium",
                "reported_by": "user@example.com",
                "assigned": "agent@example.com"
            }

            response = requests.post(url, json=ticket_payload)

            # Assert that the response returns 400 Bad Request due to missing required custom field
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                             f"Missing required custom field {field_name} should return 400.")

            # Assert that the error message indicates the missing custom field
            response_data = response.json()
            self.assertIn("Missing required custom fields", response_data.get("detail", ""))
            self.assertIn(field_name, response_data["detail"],
                          f"Error message should include the missing custom field '{field_name}'.")

            logger.info(f"Test case for missing required custom field {field_name} passed.")

        logger.info("Test case for all missing required custom fields passed.")

    def test_create_ticket_with_non_existent_custom_field(self):
        """Test creating a ticket with a custom field that does not exist."""
        url = f"{self.BASE_URL}/tickets"
        non_existent_field = "random_field"  # Custom field name that does not exist

        payload = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "title": "Ticket with Non-Existent Custom Field",
            "description": "This ticket has a custom field that does not exist.",
            "priority": "medium",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com",
            "custom_fields": {
                non_existent_field: "Some value"  # Custom field does not exist
            }
        }

        logger.info(f"Testing ticket creation with non-existent custom field: {non_existent_field}")
        response = requests.post(url, json=payload)

        # Assert that the response returns 400 Bad Request or 404 Not Found
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                         f"Creating ticket with non-existent custom field should return 400.")

        # Assert that the error message contains the invalid field name
        response_data = response.json()
        self.assertIn("Unknown custom field", response_data.get("detail", ""),
                      f"Error message should indicate that the custom field '{non_existent_field}' is unknown.")

        logger.info(f"Test case for non-existent custom field '{non_existent_field}' passed.")

    def test_create_ticket_missing_mandatory_fields(self):
        """Test creating a ticket with each mandatory field missing individually."""
        url = f"{self.BASE_URL}/tickets"
        mandatory_fields = ["title", "description", "customer_guid", "chat_id", "reported_by", "assigned"]

        # Base payload with all fields
        base_payload = {
            "title": "Missing Mandatory Field Test",
            "description": "Testing missing mandatory fields.",
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "priority": "medium",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }

        for field in mandatory_fields:
            with self.subTest(missing_field=field):
                # Create a payload without the current field
                payload = base_payload.copy()
                payload.pop(field)

                logger.info(f"Testing missing mandatory field: {field}")
                response = requests.post(url, json=payload)

                # Assert that the API returns 422 Unprocessable Entity
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                    f"Missing mandatory field '{field}' should return 422."
                )

                # Assert the error message contains the missing field in the `loc` field
                response_data = response.json()
                missing_field_in_detail = any(
                    field in error.get("loc", []) for error in response_data.get("detail", [])
                )
                self.assertTrue(
                    missing_field_in_detail,
                    f"Error for missing field '{field}' should be in response detail."
                )

        logger.info("Test case for missing mandatory fields passed.")

    def test_create_ticket_invalid_customer_guid(self):
        """Test creating a ticket with an invalid customer_guid."""
        url = f"{self.BASE_URL}/tickets"

        # Invalid customer_guid
        invalid_customer_guid = "invalid_customer_guid_1234"
        payload = {
            "title": "Invalid Customer GUID Test",
            "description": "Testing invalid customer_guid.",
            "customer_guid": invalid_customer_guid,
            "chat_id": self.valid_chat_id,
            "priority": "medium",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }

        logger.info("Testing with invalid customer_guid.")
        response = requests.post(url, json=payload)

        # Assert that the API returns 400 Bad Request
        self.assertEqual(
            response.status_code,
            HTTPStatus.BAD_REQUEST,
            "Invalid customer_guid should return 400 Bad Request."
        )

        # Parse the response data
        response_data = response.json()

        # Assert the error message contains the expected invalid customer_guid
        self.assertIn(
            "detail",
            response_data,
            "Response should contain 'detail' key."
        )
        expected_message = f"Database customer_{invalid_customer_guid} does not exist"
        self.assertEqual(
            response_data["detail"],
            expected_message,
            f"Error message for invalid customer_guid is incorrect. Expected '{expected_message}', got '{response_data['detail']}'."
        )

        logger.info("Test case for invalid customer_guid with 400 Bad Request passed.")

    def test_create_ticket_invalid_chat_id(self):
        """Test creating a ticket with an invalid chat_id."""
        url = f"{self.BASE_URL}/tickets"

        # Invalid chat_id
        invalid_chat_id = "dd8347f7-846d-4e64-8dca-928c747e6881"
        payload = {
            "title": "Invalid Chat ID Test",
            "description": "Testing invalid chat_id.",
            "customer_guid": self.valid_customer_guid,
            "chat_id": invalid_chat_id,
            "priority": "high",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }

        logger.info("Testing with invalid chat_id.")
        response = requests.post(url, json=payload)

        # Assert that the API returns 400 Bad Request
        self.assertEqual(
            response.status_code,
            HTTPStatus.BAD_REQUEST,
            "Invalid chat_id should return 400 Bad Request."
        )

        # Parse the response data
        response_data = response.json()

        # Assert the error message contains the expected invalid chat_id
        self.assertIn(
            "detail",
            response_data,
            "Response should contain 'detail' key."
        )
        expected_message = f"Invalid chat_id: {invalid_chat_id} does not exist."
        self.assertEqual(
            response_data["detail"],
            expected_message,
            f"Error message for invalid chat_id is incorrect. Expected '{expected_message}', got '{response_data['detail']}'."
        )

        logger.info("Test case for invalid chat_id with 400 Bad Request passed.")

    def tearDown(self):
        """Clean up after tests."""
        logger.info(f"=== Test {self._testMethodName} completed and passed ===")
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

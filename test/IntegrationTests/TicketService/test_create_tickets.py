import unittest
from http import HTTPStatus
import requests
import logging
import os
from uuid import uuid4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestCreateTicketAPI(unittest.TestCase):
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT', 8000)}"

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

    def test_create_ticket_with_out_valid_custom_fields(self):
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
            "field_boolean": "string_value",
            # Invalid: BOOLEAN should not accept strings or string of boolean ("true", "false") except "0" or "1"
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

    def test_create_ticket_missing_required_fields(self):
        """Test creating a ticket with missing required fields."""
        url = f"{self.BASE_URL}/tickets"
        payload = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            # Missing title and description
            "priority": "medium",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }

        logger.info("Testing ticket creation with missing required fields.")
        response = requests.post(url, json=payload)

        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY, "Missing required fields should return 422.")
        self.assertIn("title", response.text)
        self.assertIn("description", response.text)
        logger.info("Negative test case for missing required fields passed.")

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

    def tearDown(self):
        """Clean up after tests."""
        logger.info(f"=== Test {self._testMethodName} completed and passed ===")
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

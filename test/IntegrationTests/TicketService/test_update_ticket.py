import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

from src.backend.lib.logging_config import get_primitivechat_logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer, create_test_token, create_token_without_org_id, create_token_without_org_role

# Set up logging
logger = get_primitivechat_logger(__name__)


class TestUpdateTicketEndpoint(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"
    ORG_ROLE = 'org:admin'
    def setUp(self):
        """Set up test environment: create customer, chat, and ticket."""
        logger.info("=== Setting up test environment ===")

        self.headers = {}

        # Create a valid customer
        self.data = add_customer("test_org")
        self.valid_customer_guid = self.data.get("customer_guid")
        self.org_id = self.data.get("org_id")

        # Create Test Token
        self.token = create_test_token(org_id=self.org_id, org_role=self.ORG_ROLE)
        self.headers['Authorization'] = f'Bearer {self.token}'
        logger.info(f"Valid customer_guid initialized: {self.valid_customer_guid}")

        # Add chat
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "question": "Initial question"
        }
        response = requests.post(chat_url, json=chat_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create a chat")
        self.valid_chat_id = response.json().get("chat_id")

        # Add a ticket
        ticket_url = f"{self.BASE_URL}/tickets"
        ticket_data = {
            "chat_id": self.valid_chat_id,
            "title": "Test Ticket",
            "description": "This is a test ticket.",
            "priority": "high",
            "reported_by": "support_agent_1",
            "assigned": "support_agent_1",
            "custom_fields": {}
        }
        response = requests.post(ticket_url, json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a ticket")
        self.valid_ticket_id = response.json().get("ticket_id")

        logger.info(f"Test setup complete: customer_guid={self.valid_customer_guid}, ticket_id={self.valid_ticket_id}")
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_update_ticket_title(self):
        """Test updating the ticket title."""
        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        update_data = {"title": "Updated Test Ticket"}
        response = requests.put(update_url, json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update the ticket title.")

        # Validate the update
        response = requests.get(update_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket.")
        self.assertEqual(response.json().get("title"), "Updated Test Ticket", "Ticket title update failed.")

    def test_update_ticket_description(self):
        """Test updating the ticket description."""
        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        update_data = {"description": "Updated description."}
        response = requests.put(update_url, json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update the ticket description.")

        # Validate the update
        response = requests.get(update_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket.")
        self.assertEqual(response.json().get("description"), "Updated description.",
                         "Ticket description update failed.")

    def test_update_ticket_status(self):
        """Test updating the ticket status."""
        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        update_data = {"status": "closed"}
        response = requests.put(update_url, json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update the ticket status.")

        # Validate the update
        response = requests.get(update_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket.")
        self.assertEqual(response.json().get("status"), "closed", "Ticket status update failed.")

    def test_update_ticket_priority(self):
        """Test updating the ticket priority."""
        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        update_data = {"priority": "low"}
        response = requests.put(update_url, json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update the ticket priority.")

        # Validate the update
        response = requests.get(update_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket.")
        self.assertEqual(response.json().get("priority"), "Low", "Ticket priority update failed.")

    def test_update_ticket_reported_by(self):
        """Test updating the ticket reported_by field."""
        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        update_data = {"reported_by": "support_agent_2"}
        response = requests.put(update_url, json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update the ticket reported_by field.")

        # Validate the update
        response = requests.get(update_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket.")
        self.assertEqual(response.json().get("reported_by"), "support_agent_2", "Ticket reported_by update failed.")

    def test_update_ticket_assigned(self):
        """Test updating the ticket assigned field."""
        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        update_data = {"assigned": "support_agent_3"}
        response = requests.put(update_url, json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update the ticket assigned field.")

        # Validate the update
        response = requests.get(update_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket.")
        self.assertEqual(response.json().get("assigned"), "support_agent_3", "Ticket assigned update failed.")

    def test_add_update_and_remove_custom_fields(self):
        """Test adding, updating, and removing custom fields."""
        custom_field_url = f"{self.BASE_URL}/custom_fields"
        allowed_custom_field_sql_types = [
            {"field_name": "field_varchar", "field_type": "VARCHAR(255)", "value": "Sample Text"},
            {"field_name": "field_int", "field_type": "INT", "value": 123},
            {"field_name": "field_boolean", "field_type": "BOOLEAN", "value": True},
            {"field_name": "field_datetime", "field_type": "DATETIME", "value": "2025-01-01T10:00:00"},
            {"field_name": "field_mediumtext", "field_type": "MEDIUMTEXT", "value": "A longer text field value."},
            {"field_name": "field_float", "field_type": "FLOAT", "value": 123.45},
            {"field_name": "field_text", "field_type": "TEXT", "value": "Another text field value."}
        ]

        # Step 1: Create custom fields for all allowed SQL types
        for custom_field in allowed_custom_field_sql_types:
            custom_field_data = {
                "field_name": custom_field["field_name"],
                "field_type": custom_field["field_type"],
                "required": True
            }
            response = requests.post(custom_field_url, json=custom_field_data, headers=self.headers)
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create custom field: {custom_field}")
            logger.info(f"Custom field created: {custom_field}")

        # Step 2: Update ticket with all custom fields
        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        custom_fields_payload = {
            custom_field["field_name"]: custom_field["value"] for custom_field in allowed_custom_field_sql_types
        }
        update_data = {"custom_fields": custom_fields_payload}
        response = requests.put(update_url, json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update ticket with custom fields.")
        logger.info(f"Ticket updated with custom fields: {custom_fields_payload}")

        # Step 3: Validate the custom field updates
        response = requests.get(update_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket.")
        retrieved_custom_fields = response.json().get("custom_fields", {})

        for custom_field in allowed_custom_field_sql_types:
            field_name = custom_field["field_name"]
            expected_value = custom_field["value"]
            self.assertEqual(retrieved_custom_fields.get(field_name), expected_value,
                             f"Custom field {field_name} update failed. Expected: {expected_value}, Got: {retrieved_custom_fields.get(field_name)}")
            logger.info(f"Custom field validated: {field_name} = {expected_value}")

        # Step 4: Update ticket with null values for custom fields (removal scenario)
        null_custom_fields_payload = {
            custom_field["field_name"]: None for custom_field in allowed_custom_field_sql_types
        }
        update_data_null = {"custom_fields": null_custom_fields_payload}
        response = requests.put(update_url, json=update_data_null, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update ticket with null custom fields.")
        logger.info(f"Ticket updated with null custom fields: {null_custom_fields_payload}")

        # Step 5: Validate custom fields are removed from ticket
        response = requests.get(update_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket.")
        retrieved_custom_fields = response.json().get("custom_fields", {})

        # Ensure that custom fields are no longer listed
        for custom_field in allowed_custom_field_sql_types:
            field_name = custom_field["field_name"]
            self.assertNotIn(field_name, retrieved_custom_fields,
                             f"Custom field {field_name} should not be in ticket data after removal.")
            logger.info(f"Custom field {field_name} removed from ticket.")

    def test_update_ticket_invalid_priority(self):
        """Test updating the ticket with an invalid priority value."""
        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        invalid_update_data = {"priority": "urgent"}  # Invalid priority value
        response = requests.put(update_url, json=invalid_update_data,
                                headers=self.headers)

        # Assert that the response status is 400 Bad Request
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                         "Invalid priority did not return 400 Bad Request.")

        # Assert that the error detail matches the expected message
        expected_error_message = "Value Not allowed for column: 'priority'. use [Low, Medium, High]"
        self.assertEqual(response.json().get("detail"), expected_error_message,
                         "Error message for invalid priority is incorrect.")

    def test_update_ticket_invalid_custom_field_column(self):
        """Test updating the ticket with a non-existent custom field."""
        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        invalid_custom_field_data = {
            "custom_fields": {
                "invalid_column": "Some Value"  # Non-existent custom field
            }
        }
        response = requests.put(update_url, json=invalid_custom_field_data,
                                headers=self.headers)

        # Assert that the response status is 400 Bad Request
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                         "Invalid custom field did not return 400 Bad Request.")

        # Assert that the error detail matches the expected message
        expected_error_message = "Unknown custom field column: 'invalid_column'."
        self.assertEqual(response.json().get("detail"), expected_error_message,
                         "Error message for invalid custom field is incorrect.")

    def add_custom_field(self, field_name, field_type):
        """Helper method to add a custom field."""
        custom_field_url = f"{self.BASE_URL}/custom_fields"
        custom_field_data = {
            "field_name": field_name,
            "field_type": field_type,
            "required": True
        }
        response = requests.post(custom_field_url, json=custom_field_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to add custom field: {field_name}.")

    def test_update_ticket_invalid_int_custom_field_value(self):
        """Test updating the ticket with an invalid INT custom field value."""
        # Add the INT custom field
        self.add_custom_field(field_name="int_field", field_type="INT")

        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        invalid_int_field_data = {
            "custom_fields": {
                "int_field": "invalid_int"  # Invalid value for INT field
            }
        }
        response = requests.put(update_url, json=invalid_int_field_data,
                                headers=self.headers)

        # Assert response status is 409 Conflict
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid INT field did not return 400 Conflict.")

        # Assert error message
        expected_error_message = "Incorrect value: 'invalid_int' for column: 'int_field'."
        self.assertEqual(response.json().get("detail"), expected_error_message,
                         "Error message for invalid INT field is incorrect.")

    def test_update_ticket_invalid_boolean_custom_field_value(self):
        """Test updating the ticket with an invalid BOOLEAN custom field value."""
        # Add the BOOLEAN custom field
        self.add_custom_field(field_name="bool_field", field_type="BOOLEAN")

        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        invalid_boolean_field_data = {
            "custom_fields": {
                "bool_field": "new"  # Invalid value for BOOLEAN field
            }
        }
        response = requests.put(update_url, json=invalid_boolean_field_data,
                                headers=self.headers)

        # Assert response status is 409 Conflict
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                         "Invalid BOOLEAN field did not return 400 Conflict.")

        # Assert error message
        expected_error_message = "Incorrect value: 'new' for column: 'bool_field'."
        self.assertEqual(response.json().get("detail"), expected_error_message,
                         "Error message for invalid BOOLEAN field is incorrect.")

    def test_update_ticket_invalid_datetime_custom_field_value(self):
        """Test updating the ticket with an invalid DATETIME custom field value."""
        # Add the DATETIME custom field
        self.add_custom_field(field_name="datetime_field", field_type="DATETIME")

        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        invalid_datetime_field_data = {
            "custom_fields": {
                "datetime_field": "invalid_date"  # Invalid value for DATETIME field
            }
        }
        response = requests.put(update_url, json=invalid_datetime_field_data,
                                headers=self.headers)

        # Assert response status is 409 Conflict
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                         "Invalid DATETIME field did not return 400 Conflict.")

        # Assert error message
        expected_error_message = "Incorrect value: 'invalid_date' for column: 'datetime_field'."
        self.assertEqual(response.json().get("detail"), expected_error_message,
                         "Error message for invalid DATETIME field is incorrect.")

    def test_update_ticket_invalid_float_custom_field_value(self):
        """Test updating the ticket with an invalid FLOAT custom field value."""
        # Add the FLOAT custom field
        self.add_custom_field(field_name="float_field", field_type="FLOAT")

        update_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        invalid_float_field_data = {
            "custom_fields": {
                "float_field": "invalid_float"  # Invalid value for FLOAT field
            }
        }
        response = requests.put(update_url, json=invalid_float_field_data,
                                headers=self.headers)

        # Assert response status is 409 Conflict
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid FLOAT field did not return 400 Conflict.")

        # Assert error message
        expected_error_message = "Incorrect value for column: float_field."
        self.assertEqual(response.json().get("detail"), expected_error_message,
                         "Error message for invalid FLOAT field is incorrect.")

    def test_update_ticket_with_invalid_org_id_or_customer_guid(self):
        """Test retrieving a ticket by ID with an invalid GUID."""
        invalid_token = create_test_token(org_id="invalid_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        payload={}
        response = requests.put(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            json=payload,
            headers=headers
        )

        # Check for 404 error with the appropriate detail message
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 BAD REQUEST for invalid GUID.")
        self.assertEqual(response.json(), {
            "detail": f"Database customer_None does not exist"
        })

    def test_update_ticket_not_found(self):
        """Test attempting to retrieve a ticket that does not exist."""
        invalid_ticket_id = "nonexistent_ticket_id"
        response = requests.get(
            f"{self.BASE_URL}/tickets/{invalid_ticket_id}",
            headers=self.headers
        )

        # Check if the response is as expected for invalid ticket ID
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected 404 NOT FOUND for invalid ticket ID.")
        self.assertEqual(response.json(), {
            "detail": f"Ticket with ticket_id {invalid_ticket_id} not found for customer {self.valid_customer_guid}"
        })

    def test_no_token(self):
        """Test API request without an authentication token."""
        data = {
            "chat_id": self.valid_chat_id,
            "title": "Valid Custom Fields Test",
            "description": "This ticket has valid custom fields.",
            "priority": "low",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        logger.info("Testing API request without token")
        response = requests.put(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            json=data
        )  # No headers
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Missing token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Missing Token leads to Unauthorized")

    def test_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        data = {
            "chat_id": self.valid_chat_id,
            "title": "Valid Custom Fields Test",
            "description": "This ticket has valid custom fields.",
            "priority": "low",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        headers = {"Authorization": "Bearer corrupted_token"}
        logger.info("Testing API request with corrupted token")
        response = requests.put(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            json=data,
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_missing_org_id_in_token(self):
        """Test API request where the token does not have an org_id."""
        data = {
            "chat_id": self.valid_chat_id,
            "title": "Valid Custom Fields Test",
            "description": "This ticket has valid custom fields.",
            "priority": "low",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        token = create_token_without_org_id(org_role=self.ORG_ROLE)  # No org_id
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("Testing API request with missing org_id in token")
        response = requests.put(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            json=data,
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Missing org_id should result in 400 Bad Request")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_missing_org_role_in_token(self):
        """Test API request where the token does not have an org_role."""
        url = f"{self.BASE_URL}/tickets"
        data = {
            "chat_id": self.valid_chat_id,
            "title": "Valid Custom Fields Test",
            "description": "This ticket has valid custom fields.",
            "priority": "low",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        logger.info("Testing API request with missing org_role in token")
        response = requests.put(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            json=data,
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN, "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_unauthorized_org_role(self):
        headers={}
        # Assuming an endpoint `/addcustomer` to create a new customer
        data = add_customer("test_org")
        org_id = data.get("org_id")

        # Create Test Token for member (not allowed)
        token = create_test_token(org_id=org_id, org_role="org:random_org_role")
        headers['Authorization'] = f'Bearer {token}'
        data = {
            "chat_id": self.valid_chat_id,
            "title": "Valid Custom Fields Test",
            "description": "This ticket has valid custom fields.",
            "priority": "low",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        response = requests.put(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            json=data,
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_invalid_org_id_no_mapped_customer_guid(self):
        """Test API request with an org_id that has no mapped customer_guid."""
        data = {
            "chat_id": self.valid_chat_id,
            "title": "Valid Custom Fields Test",
            "description": "This ticket has valid custom fields.",
            "priority": "low",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        invalid_token = create_test_token(org_id="unmapped_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        logger.info("Testing API request with org_id that has no mapped customer_guid")
        response = requests.put(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            json=data,
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Unmapped org_id should result in 400 Bad Request")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")

    def tearDown(self):
        """Clean up after tests."""
        logger.info(f"=== Test {self._testMethodName} completed and passed ===")
        logger.info("=== Test teardown complete ===")


if __name__ == "__main__":
    unittest.main()

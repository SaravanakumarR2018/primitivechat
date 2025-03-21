import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer, create_test_token, create_token_without_org_role, create_token_without_org_id
from src.backend.lib.logging_config import log_format

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=log_format
)
logger = logging.getLogger(__name__)


class TestDeleteTicketAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    allowed_custom_field_sql_types = ["VARCHAR(255)", "INT", "BOOLEAN", "DATETIME", "MEDIUMTEXT", "FLOAT", "TEXT"]
    ORG_ROLE = 'org:admin'
    def setUp(self):
        """Setup function to initialize a valid customer GUID, chat, and ticket."""
        logger.info("=== Initializing test setup for Delete Ticket API ===")

        self.headers = {}

        # Create a valid customer
        self.data = add_customer("test_org")
        self.valid_customer_guid = self.data.get("customer_guid")
        self.org_id = self.data.get("org_id")

        # Create Test Token
        self.token = create_test_token(org_id=self.org_id, org_role=self.ORG_ROLE)
        self.headers['Authorization'] = f'Bearer {self.token}'
        logger.info(f"Valid customer_guid initialized: {self.valid_customer_guid}")

        self.custom_fields = {}

        # Step 2: Create a new chat for the customer
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "question": "Initial question"
        }
        response = requests.post(chat_url, json=chat_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create chat")
        self.valid_chat_id = response.json().get("chat_id")
        logger.info(f"Chat created with ID: {self.valid_chat_id}")
        self.tickets=[]
        logger.info("Setup complete.")
        logger.info(f"Starting test: {self._testMethodName}")

    def test_delete_valid_ticket(self):
        ticket_url = f"{self.BASE_URL}/tickets"
        ticket_data = {
            "title": "Test Ticket",
            "description": "Test description",
            "chat_id": self.valid_chat_id,
            "priority": "medium",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        response = requests.post(ticket_url, json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create ticket")
        valid_ticket_id = response.json().get("ticket_id")
        logger.info(f"Ticket created with ID: {valid_ticket_id}")
        """Test deleting a valid ticket and verifying the response."""
        delete_url = f"{self.BASE_URL}/tickets/{valid_ticket_id}"
        logger.info(f"Deleting valid ticket with ID: {valid_ticket_id}")

        response = requests.delete(delete_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete valid ticket")
        response_data = response.json()
        self.assertEqual(response_data["ticket_id"], valid_ticket_id)
        self.assertEqual(response_data["status"], "deleted")
        logger.info("Successfully deleted valid ticket.")

        response = requests.get(f"{self.BASE_URL}/tickets/{valid_ticket_id}", headers=self.headers)
        logger.info(f"Get ticket {valid_ticket_id} response status: {response.status_code}")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,
                         f"Ticket {valid_ticket_id} should not exist but was found.")
        self.assertIn("not found", response.json().get("detail", "").lower(),
                      f"Unexpected error message for ticket {valid_ticket_id}: {response.json().get('detail')}")
        logger.info(f"Confirmed ticket {valid_ticket_id} does not exist.")

    def test_delete_non_existent_ticket(self):
        """Test deleting a non-existent ticket."""
        non_existent_ticket_id = "non_existent_ticket_12345"
        delete_url = f"{self.BASE_URL}/tickets/{non_existent_ticket_id}"
        logger.info(f"Deleting non-existent ticket with ID: {non_existent_ticket_id}")

        response = requests.delete(delete_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete non_existent_ticket_12345 ticket")
        response_data = response.json()
        self.assertEqual(response_data["ticket_id"], non_existent_ticket_id)
        self.assertEqual(response_data["status"], "deleted")
        logger.info("Successfully deleted valid ticket.")

    def test_delete_ticket_invalid_org_id_customer_guid(self):
        """Test deleting a ticket with an invalid customer GUID."""
        ticket_url = f"{self.BASE_URL}/tickets"
        ticket_data = {
            "title": "Test Ticket",
            "description": "Test description",
            "chat_id": self.valid_chat_id,
            "priority": "medium",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        response = requests.post(ticket_url, json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create ticket")
        valid_ticket_id = response.json().get("ticket_id")
        logger.info(f"Ticket created with ID: {valid_ticket_id}")
        """Test deleting a valid ticket and verifying the response."""
        invalid_token = create_test_token(org_id="invalid_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        delete_url = f"{self.BASE_URL}/tickets/{valid_ticket_id}"

        response = requests.delete(delete_url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 for invalid customer GUID")
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertEqual(response_data["detail"], f"Database customer_None does not exist")
        logger.info("Successfully validated deletion with invalid customer GUID.")

    def _generate_field_value(self, field_type):
        """Generate appropriate test values for each custom field type."""
        if "VARCHAR" in field_type:
            return "SampleText"
        if "TEXT" in field_type or "MEDIUMTEXT" in field_type:
            return "Detailed text value for testing."
        if "INT" in field_type:
            return 123
        if "BOOLEAN" in field_type:
            return False  # Use explicit False/True
        if "DATETIME" in field_type:
            return "2024-01-01 12:00:00"  # Ensure proper format
        if "FLOAT" in field_type:
            return 123.45
        return None

    def test_add_and_delete_tickets_with_custom_fields(self):
        """Test creating custom fields, adding tickets, and deleting them individually."""
        ticket_url = f"{self.BASE_URL}/tickets"
        custom_fields_url = f"{self.BASE_URL}/custom_fields"

        # Step 1: Dynamically Create Custom Fields
        for field_type in self.allowed_custom_field_sql_types:
            field_name = f"field_{field_type.split('(')[0].lower()}"
            payload = {
                "field_name": field_name,
                "field_type": field_type,
                "required": False
            }

            response = requests.post(custom_fields_url, json=payload, headers=self.headers)
            if response.status_code != HTTPStatus.CREATED:
                logger.error(f"Failed to create custom field '{field_name}': {response.text}")
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create custom field '{field_name}'")
            self.custom_fields[field_name] = field_type

        logger.info(f"Custom fields created: {self.custom_fields}")

        # Step 2: Add Tickets with Custom Fields
        for field_name, field_type in self.custom_fields.items():
            custom_field_value = self._generate_field_value(field_type)
            ticket_data = {
                "title": f"Ticket for {field_type}",
                "description": f"Testing ticket with custom field {field_name}",
                "chat_id": self.valid_chat_id,
                "priority": "medium",
                "reported_by": "user@example.com",
                "assigned": "agent@example.com",
                "custom_fields": {
                    field_name: custom_field_value
                }
            }

            response = requests.post(ticket_url, json=ticket_data, headers=self.headers)
            if response.status_code != HTTPStatus.CREATED:
                logger.error(f"Failed to create ticket for '{field_name}': {response.text}")
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create ticket with '{field_name}'")

            ticket_id = response.json().get("ticket_id")
            self.tickets.append(ticket_id)
            logger.info(f"Created ticket '{ticket_id}' with custom field '{field_name}'")

        # Step 3: Delete Tickets Individually
        for ticket_id in self.tickets:
            delete_url = f"{ticket_url}/{ticket_id}"
            response = requests.delete(delete_url, headers=self.headers)
            if response.status_code != HTTPStatus.OK:
                logger.error(f"Failed to delete ticket '{ticket_id}': {response.text}")
            self.assertEqual(response.status_code, HTTPStatus.OK, f"Failed to delete ticket '{ticket_id}'")
            logger.info(f"Successfully deleted ticket '{ticket_id}'")

            logger.info(f"Verifying ticket {ticket_id} no longer exists.")
            response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                    headers=self.headers)
            logger.info(f"Get ticket {ticket_id} response status: {response.status_code}")
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,
                             f"Ticket {ticket_id} should not exist but was found.")
            self.assertIn("not found", response.json().get("detail", "").lower(),
                          f"Unexpected error message for ticket {ticket_id}: {response.json().get('detail')}")
            logger.info(f"Confirmed ticket {ticket_id} does not exist.")

    def _add_50_tickets_with_custom_fields(self):
        """Add 50 tickets for a valid customer and chat with custom fields."""
        logger.info("Adding 50 tickets for the customer and chat with custom fields.")

        # Create custom fields dynamically
        custom_fields_url = f"{self.BASE_URL}/custom_fields"
        for field_type in self.allowed_custom_field_sql_types:
            field_name = f"field_{field_type.split('(')[0].lower()}"
            payload = {
                "field_name": field_name,
                "field_type": field_type,
                "required": False
            }
            response = requests.post(custom_fields_url, json=payload, headers=self.headers)
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create custom field {field_name}")
            self.custom_fields[field_name] = field_type

        logger.info(f"Custom fields created: {self.custom_fields}")

        # Create 50 tickets with custom fields
        tickets = [
            {
                "chat_id": self.valid_chat_id,
                "title": f"Ticket {i}",
                "description": f"Description for ticket {i}",
                "priority": "high" if i % 2 == 0 else "low",
                "reported_by": f"user{i}",
                "assigned": f"agent{i}",
                **{field: f"{field}_value_{i}" for field in self.custom_fields}  # Add custom fields
            }
            for i in range(1, 51)
        ]

        # Add each ticket via POST request
        for ticket in tickets:
            response = requests.post(f"{self.BASE_URL}/tickets", json=ticket, headers=self.headers)
            if response.status_code != HTTPStatus.CREATED:
                logger.error(f"Failed to add ticket: {ticket['title']}. Server response: {response.text}")
            self.assertEqual(
                response.status_code,
                HTTPStatus.CREATED,
                f"Failed to add ticket: {ticket['title']}"
            )

        logger.info("Successfully added 50 tickets with custom fields.")

    def test_delete_tickets_and_check_deleted_tickets_not_exist(self):
        """Test deleting tickets and verifying they no longer exist."""

        # Add tickets for testing
        self._add_50_tickets_with_custom_fields()

        # List of ticket IDs to delete for the test
        ticket_ids_to_delete = [10, 20, 25, 35, 42]

        # Step 1: Delete specific tickets
        for ticket_id in ticket_ids_to_delete:
            logger.info(f"Deleting ticket {ticket_id}.")
            response = requests.delete(f"{self.BASE_URL}/tickets/{ticket_id}",
                                       headers=self.headers)
            if response.status_code != HTTPStatus.OK:
                logger.error(f"Failed to delete ticket {ticket_id}. Server response: {response.text}")
            self.assertEqual(response.status_code, HTTPStatus.OK, f"Failed to delete ticket {ticket_id}")
            logger.info(f"Successfully deleted ticket {ticket_id}.")

        # Step 2: Verify the deleted tickets no longer exist
        for ticket_id in ticket_ids_to_delete:
            logger.info(f"Verifying ticket {ticket_id} no longer exists.")
            response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                    headers=self.headers)
            logger.info(f"Get ticket {ticket_id} response status: {response.status_code}")
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,
                             f"Ticket {ticket_id} should not exist but was found.")
            self.assertIn("not found", response.json().get("detail", "").lower(),
                          f"Unexpected error message for ticket {ticket_id}: {response.json().get('detail')}")
            logger.info(f"Confirmed ticket {ticket_id} does not exist.")

    def test_delete_tickets_no_token(self):
        """Test API request without an authentication token."""
        logger.info("Testing API request without token")
        ticket_id=1
        response = requests.delete(f"{self.BASE_URL}/tickets/{ticket_id}") # No headers
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Missing token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Missing Token leads to Unauthorized")

    def test_delete_tickets_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        ticket_id = 1
        headers = {"Authorization": "Bearer corrupted_token"}
        logger.info("Testing API request with corrupted token")
        response = requests.delete(
            f"{self.BASE_URL}/tickets/{ticket_id}",
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_delete_tickets_missing_org_id_in_token(self):
        """Test API request where the token does not have an org_id."""
        ticket_id=1
        token = create_token_without_org_id(org_role=self.ORG_ROLE)  # No org_id
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("Testing API request with missing org_id in token")
        response = requests.delete(
            f"{self.BASE_URL}/tickets/{ticket_id}",
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Missing org_id should result in 400 Bad Request")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_delete_tickets_missing_org_role_in_token(self):
        """Test API request where the token does not have an org_role."""
        ticket_id=1
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        logger.info("Testing API request with missing org_role in token")
        response = requests.delete(
            f"{self.BASE_URL}/tickets/{ticket_id}",
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN, "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_delete_tickets_unauthorized_org_role(self):
        headers={}
        ticket_id=1
        # Assuming an endpoint `/addcustomer` to create a new customer
        data = add_customer("test_org")
        org_id = data.get("org_id")

        # Create Test Token for member (not allowed)
        token = create_test_token(org_id=org_id, org_role="org:random_org_role")
        headers['Authorization'] = f'Bearer {token}'
        response = requests.delete(
            f"{self.BASE_URL}/tickets/{ticket_id}",
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_delete_tickets_invalid_org_id_no_mapped_customer_guid(self):
        """Test API request with an org_id that has no mapped customer_guid."""
        ticket_id=1
        invalid_token = create_test_token(org_id="unmapped_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        logger.info("Testing API request with org_id that has no mapped customer_guid")
        response = requests.delete(
            f"{self.BASE_URL}/tickets/{ticket_id}",
            headers=headers
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Unmapped org_id should result in 400 Bad Request")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")

    def tearDown(self):
        """Clean up resources if necessary."""
        logger.info(f"Finished test: {self._testMethodName}")
        logger.info("=== Test teardown complete ===")


if __name__ == "__main__":
    unittest.main()

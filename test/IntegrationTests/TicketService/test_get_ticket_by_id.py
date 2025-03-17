import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer, create_test_token, create_token_without_org_id, create_token_without_org_role

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestGetTicketEndpoint(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"
    allowed_custom_field_sql_types = ["VARCHAR(255)", "INT", "BOOLEAN", "DATETIME", "MEDIUMTEXT", "FLOAT", "TEXT"]

    ORG_ROLE = 'org:admin'
    def setUp(self):
        """Set up test environment: create customer, chat, and mock ticket."""
        logger.info("=== Setting up test environment ===")

        self.headers = {}

        # Assuming an endpoint `/addcustomer` to create a new customer
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
            "chat_id": self.valid_chat_id,  # Use valid chat_id if needed or mock it
            "title": "Test Ticket",
            "description": "This is a test ticket.",
            "priority": "high",
            "reported_by": "support_agent_1",
            "assigned": "support_agent_1",
            "custom_fields": {}  # Include custom fields if required
        }
        response = requests.post(ticket_url, json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a ticket")
        self.valid_ticket_id = response.json().get("ticket_id")

        logger.info(f"Test setup complete: customer_guid={self.valid_customer_guid}, ticket_id={self.valid_ticket_id}")
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_get_ticket_success(self):
        """Test retrieving a ticket by ID."""
        response = requests.get(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            headers=self.headers
        )
        response_json = response.json()

        # Check if the response is as expected
        self.assertEqual(response.status_code, HTTPStatus.OK, "Expected 200 OK for valid ticket.")
        self.assertEqual(response.json(), {
            "ticket_id":  int(self.valid_ticket_id),
            "chat_id": self.valid_chat_id,
            "title": "Test Ticket",
            "description": "This is a test ticket.",
            "priority": "High",
            "status": "open",
            "reported_by": "support_agent_1",
            "assigned": "support_agent_1",
            "created_at":response_json["created_at"],
            "updated_at":response_json["updated_at"],
            "custom_fields": {}
        })

    def test_get_ticket_not_found(self):
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

    def test_get_ticket_with_invalid_org_id_or_customer_guid(self):
        """Test retrieving a ticket by ID with an invalid GUID."""
        #invalid customer_guid
        invalid_token = create_test_token(org_id="invalid_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = requests.get(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            headers=headers
        )

        # Check for 404 error with the appropriate detail message
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 NOT FOUND for invalid GUID.")
        self.assertEqual(response.json(), {
            "detail": f"Database customer_None does not exist"
        })

    def test_create_and_get_ticket_with_custom_fields(self):
        """Test creating a ticket with custom fields and retrieving it by ID."""
        logger.info("=== Creating custom fields ===")

        # Create custom fields
        self.custom_fields = {}
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

        # Prepare custom fields data with appropriate types
        custom_fields_data = {
            "field_varchar": "Some string value",
            "field_int": 123,
            "field_boolean": True,
            "field_datetime": "2025-01-03 12:00:00",  # Adjusting the format
            "field_mediumtext": "This is a medium text field",
            "field_float": 10.5,
            "field_text": "This is a long text field"
        }

        # Create a ticket with custom fields
        logger.info("=== Creating ticket with custom fields ===")
        ticket_url = f"{self.BASE_URL}/tickets"
        ticket_data = {
            "chat_id": self.valid_chat_id,
            "title": "Test Ticket with Custom Fields",
            "description": "This is a test ticket with custom fields.",
            "priority": "High",
            "reported_by": "support_agent_1",
            "assigned": "support_agent_1",
            "custom_fields": custom_fields_data
        }
        response = requests.post(ticket_url, json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a ticket with custom fields")
        valid_ticket_id = response.json().get("ticket_id")

        # Now retrieve the created ticket by ID
        logger.info("=== Retrieving ticket by ID ===")
        response = requests.get(
            f"{self.BASE_URL}/tickets/{valid_ticket_id}",
            headers=self.headers
        )

        # Check if the response is as expected
        self.assertEqual(response.status_code, HTTPStatus.OK, "Expected 200 OK for valid ticket with custom fields.")

        # Normalize datetime format in the response
        response_json = response.json()
        response_json['custom_fields']['field_datetime'] = response_json['custom_fields']['field_datetime'].replace('T',
                                                                                                                    ' ')

        expected_response = {
            "ticket_id": int(valid_ticket_id),
            "chat_id": self.valid_chat_id,
            "title": "Test Ticket with Custom Fields",
            "description": "This is a test ticket with custom fields.",
            "priority": "High",
            "status": "open",
            "reported_by": "support_agent_1",
            "assigned": "support_agent_1",
            "created_at": response_json["created_at"],
            "updated_at": response_json["updated_at"],
            "custom_fields": {
                "field_varchar": "Some string value",
                "field_int": 123,
                "field_boolean": True,
                "field_datetime": "2025-01-03 12:00:00",  # Normalized format
                "field_mediumtext": "This is a medium text field",
                "field_float": 10.5,
                "field_text": "This is a long text field"
            }
        }

        self.assertEqual(response_json, expected_response)

    def test_ticket_timestamps(self):
        """Test that created_at and updated_at timestamps are set and updated correctly."""
        # Create a ticket
        ticket_url = f"{self.BASE_URL}/tickets"
        ticket_data = {
            "chat_id": self.valid_chat_id,
            "title": "Test Ticket",
            "description": "This is a test ticket.",
            "priority": "high",
            "reported_by": "support_agent_1",
            "assigned": "support_agent_1"
        }
        response = requests.post(ticket_url, json=ticket_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a ticket")
        ticket_id = response.json().get("ticket_id")

        # Get the created ticket
        response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the created ticket")
        ticket_data = response.json()
        created_at=ticket_data["created_at"]
        updated_at=ticket_data["updated_at"]
        self.assertIn("created_at", ticket_data, "created_at timestamp mismatch.")
        self.assertIn("updated_at", ticket_data, "updated_at timestamp mismatch.")

        import time
        time.sleep(1)

        # Update the ticket
        update_url = f"{self.BASE_URL}/tickets/{ticket_id}"
        update_data = {"description": "Updated description."}
        requests.put(update_url, json=update_data, headers=self.headers)
        response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update the ticket")
        updated_at_new = response.json().get("updated_at")

        # Validate timestamps after update
        self.assertEqual(created_at, response.json().get("created_at"), "created_at should not change on update.")
        self.assertNotEqual(updated_at, updated_at_new, "updated_at should change after an update.")

        # Get the updated ticket
        response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket")
        ticket_data = response.json()
        self.assertEqual(ticket_data["created_at"], created_at, "created_at timestamp mismatch after update.")
        self.assertEqual(ticket_data["updated_at"], updated_at_new, "updated_at timestamp mismatch after update.")

    def test_get_ticket_no_token(self):
        """Test API request without an authentication token."""

        url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        logger.info("Testing API request without token")
        response = requests.get(url)  # No headers
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Missing token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Missing Token leads to Unauthorized")

    def test_get_ticket_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        headers = {"Authorization": "Bearer corrupted_token"}
        logger.info("Testing API request with corrupted token")
        response = requests.get(url,  headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_get_ticket_missing_org_id_in_token(self):
        """Test API request where the token does not have an org_id."""
        url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        token = create_token_without_org_id(org_role=self.ORG_ROLE)  # No org_id
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("Testing API request with missing org_id in token")
        response = requests.get(url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Missing org_id should result in 400 Bad Request")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_get_ticket_missing_org_role_in_token(self):
        """Test API request where the token does not have an org_role."""
        url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        logger.info("Testing API request with missing org_role in token")
        response = requests.get(url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN, "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_get_ticket_unauthorized_org_role(self):
        headers={}
        # Assuming an endpoint `/addcustomer` to create a new customer
        data = add_customer("test_org")
        org_id = data.get("org_id")

        # Create Test Token for member (not allowed)
        token = create_test_token(org_id=org_id, org_role="org:random_org_role")
        headers['Authorization'] = f'Bearer {token}'

        url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        response = requests.get(url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_get_ticket_invalid_org_id_no_mapped_customer_guid(self):
        """Test API request with an org_id that has no mapped customer_guid."""
        url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}"
        invalid_token = create_test_token(org_id="unmapped_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        logger.info("Testing API request with org_id that has no mapped customer_guid")
        response = requests.get(url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Unmapped org_id should result in 400 Bad Request")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")

    def tearDown(self):
        """Clean up after tests."""
        logger.info(f"=== Test {self._testMethodName} completed and passed ===")
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

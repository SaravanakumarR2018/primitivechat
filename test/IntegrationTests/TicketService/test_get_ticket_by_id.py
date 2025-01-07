import unittest
import requests
from http import HTTPStatus
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestGetTicketEndpoint(unittest.TestCase):
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT')}"
    allowed_custom_field_sql_types = ["VARCHAR(255)", "INT", "BOOLEAN", "DATETIME", "MEDIUMTEXT", "FLOAT", "TEXT"]

    def setUp(self):
        """Set up test environment: create customer, chat, and mock ticket."""
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

        # Add a ticket
        ticket_url = f"{self.BASE_URL}/tickets"
        ticket_data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,  # Use valid chat_id if needed or mock it
            "title": "Test Ticket",
            "description": "This is a test ticket.",
            "priority": "high",
            "reported_by": "support_agent_1",
            "assigned": "support_agent_1",
            "custom_fields": {}  # Include custom fields if required
        }
        response = requests.post(ticket_url, json=ticket_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a ticket")
        self.valid_ticket_id = response.json().get("ticket_id")

        logger.info(f"Test setup complete: customer_guid={self.valid_customer_guid}, ticket_id={self.valid_ticket_id}")
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_get_ticket_success(self):
        """Test retrieving a ticket by ID."""
        response = requests.get(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            params={"customer_guid": self.valid_customer_guid}
        )
        response_json = response.json()

        # Check if the response is as expected
        self.assertEqual(response.status_code, HTTPStatus.OK, "Expected 200 OK for valid ticket.")
        self.assertEqual(response.json(), {
            "ticket_id": self.valid_ticket_id,
            "chat_id": self.valid_chat_id,
            "title": "Test Ticket",
            "description": "This is a test ticket.",
            "priority": "High",
            "status": "Open",
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
            params={"customer_guid": self.valid_customer_guid}
        )

        # Check if the response is as expected for invalid ticket ID
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected 404 NOT FOUND for invalid ticket ID.")
        self.assertEqual(response.json(), {
            "detail": f"Ticket with ticket_id {invalid_ticket_id} not found for customer {self.valid_customer_guid}"
        })

    def test_get_ticket_with_invalid_guid(self):
        """Test retrieving a ticket by ID with an invalid GUID."""
        invalid_customer_guid="34e67372-28aa-48e6-8646-54b2578b90a2" #invalid customer_guid
        response = requests.get(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}",
            params={"customer_guid": invalid_customer_guid}
        )

        # Check for 404 error with the appropriate detail message
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 NOT FOUND for invalid GUID.")
        self.assertEqual(response.json(), {
            "detail": f"Database customer_{invalid_customer_guid} does not exist"
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
                "customer_guid": self.valid_customer_guid,
                "field_name": field_name,
                "field_type": field_type,
                "required": False
            }
            response = requests.post(custom_fields_url, json=payload)
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
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "title": "Test Ticket with Custom Fields",
            "description": "This is a test ticket with custom fields.",
            "priority": "High",
            "reported_by": "support_agent_1",
            "assigned": "support_agent_1",
            "custom_fields": custom_fields_data
        }
        response = requests.post(ticket_url, json=ticket_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a ticket with custom fields")
        valid_ticket_id = response.json().get("ticket_id")

        # Now retrieve the created ticket by ID
        logger.info("=== Retrieving ticket by ID ===")
        response = requests.get(
            f"{self.BASE_URL}/tickets/{valid_ticket_id}",
            params={"customer_guid": self.valid_customer_guid}
        )

        # Check if the response is as expected
        self.assertEqual(response.status_code, HTTPStatus.OK, "Expected 200 OK for valid ticket with custom fields.")

        # Normalize datetime format in the response
        response_json = response.json()
        response_json['custom_fields']['field_datetime'] = response_json['custom_fields']['field_datetime'].replace('T',
                                                                                                                    ' ')

        expected_response = {
            "ticket_id": valid_ticket_id,
            "chat_id": self.valid_chat_id,
            "title": "Test Ticket with Custom Fields",
            "description": "This is a test ticket with custom fields.",
            "priority": "High",
            "status": "Open",
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
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "title": "Test Ticket",
            "description": "This is a test ticket.",
            "priority": "high",
            "reported_by": "support_agent_1",
            "assigned": "support_agent_1"
        }
        response = requests.post(ticket_url, json=ticket_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a ticket")
        ticket_id = response.json().get("ticket_id")

        # Get the created ticket
        response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                params={"customer_guid": self.valid_customer_guid})
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
        requests.put(update_url, json=update_data, params={"customer_guid": self.valid_customer_guid})
        response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                params={"customer_guid": self.valid_customer_guid})
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update the ticket")
        updated_at_new = response.json().get("updated_at")

        # Validate timestamps after update
        self.assertEqual(created_at, response.json().get("created_at"), "created_at should not change on update.")
        self.assertNotEqual(updated_at, updated_at_new, "updated_at should change after an update.")

        # Get the updated ticket
        response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                params={"customer_guid": self.valid_customer_guid})
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the updated ticket")
        ticket_data = response.json()
        self.assertEqual(ticket_data["created_at"], created_at, "created_at timestamp mismatch after update.")
        self.assertEqual(ticket_data["updated_at"], updated_at_new, "updated_at timestamp mismatch after update.")

    def tearDown(self):
        """Clean up after tests."""
        logger.info(f"=== Test {self._testMethodName} completed and passed ===")
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

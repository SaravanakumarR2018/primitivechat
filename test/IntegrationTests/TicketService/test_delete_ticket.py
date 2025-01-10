import unittest
from http import HTTPStatus
import requests
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestDeleteTicketAPI(unittest.TestCase):
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT')}"

    allowed_custom_field_sql_types = ["VARCHAR(255)", "INT", "BOOLEAN", "DATETIME", "MEDIUMTEXT", "FLOAT", "TEXT"]

    def setUp(self):
        """Setup function to initialize a valid customer GUID, chat, and ticket."""
        logger.info("=== Initializing test setup for Delete Ticket API ===")

        # Step 1: Create a new customer
        customer_url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(customer_url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create customer")
        self.valid_customer_guid = response.json().get("customer_guid")
        logger.info(f"Customer created with GUID: {self.valid_customer_guid}")

        self.custom_fields = {}

        # Step 2: Create a new chat for the customer
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "Initial question"
        }
        response = requests.post(chat_url, json=chat_data)
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
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "priority": "medium",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        response = requests.post(ticket_url, json=ticket_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create ticket")
        valid_ticket_id = response.json().get("ticket_id")
        logger.info(f"Ticket created with ID: {valid_ticket_id}")
        """Test deleting a valid ticket and verifying the response."""
        delete_url = f"{self.BASE_URL}/tickets/{valid_ticket_id}?customer_guid={self.valid_customer_guid}"
        logger.info(f"Deleting valid ticket with ID: {valid_ticket_id}")

        response = requests.delete(delete_url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete valid ticket")
        response_data = response.json()
        self.assertEqual(response_data["ticket_id"], valid_ticket_id)
        self.assertEqual(response_data["status"], "deleted")
        logger.info("Successfully deleted valid ticket.")

        response = requests.get(f"{self.BASE_URL}/tickets/{valid_ticket_id}",
                                params={"customer_guid": self.valid_customer_guid})
        logger.info(f"Get ticket {valid_ticket_id} response status: {response.status_code}")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,
                         f"Ticket {valid_ticket_id} should not exist but was found.")
        self.assertIn("not found", response.json().get("detail", "").lower(),
                      f"Unexpected error message for ticket {valid_ticket_id}: {response.json().get('detail')}")
        logger.info(f"Confirmed ticket {valid_ticket_id} does not exist.")

    def test_delete_non_existent_ticket(self):
        """Test deleting a non-existent ticket."""
        non_existent_ticket_id = "non_existent_ticket_12345"
        delete_url = f"{self.BASE_URL}/tickets/{non_existent_ticket_id}?customer_guid={self.valid_customer_guid}"
        logger.info(f"Deleting non-existent ticket with ID: {non_existent_ticket_id}")

        response = requests.delete(delete_url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete non_existent_ticket_12345 ticket")
        response_data = response.json()
        self.assertEqual(response_data["ticket_id"], non_existent_ticket_id)
        self.assertEqual(response_data["status"], "deleted")
        logger.info("Successfully deleted valid ticket.")

    def test_delete_ticket_invalid_customer_guid(self):
        """Test deleting a ticket with an invalid customer GUID."""
        ticket_url = f"{self.BASE_URL}/tickets"
        ticket_data = {
            "title": "Test Ticket",
            "description": "Test description",
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "priority": "medium",
            "reported_by": "user@example.com",
            "assigned": "agent@example.com"
        }
        response = requests.post(ticket_url, json=ticket_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create ticket")
        valid_ticket_id = response.json().get("ticket_id")
        logger.info(f"Ticket created with ID: {valid_ticket_id}")
        """Test deleting a valid ticket and verifying the response."""
        delete_url = f"{self.BASE_URL}/tickets/{valid_ticket_id}?customer_guid={self.valid_customer_guid}"
        logger.info(f"Deleting valid ticket with ID: {valid_ticket_id}")

        invalid_customer_guid = "invalid_guid_12345"
        delete_url = f"{self.BASE_URL}/tickets/{valid_ticket_id}?customer_guid={invalid_customer_guid}"
        logger.info(f"Deleting ticket with invalid customer GUID: {invalid_customer_guid}")

        response = requests.delete(delete_url)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 for invalid customer GUID")
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertEqual(response_data["detail"], f"Database customer_{invalid_customer_guid} does not exist")
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
                "customer_guid": self.valid_customer_guid,
                "field_name": field_name,
                "field_type": field_type,
                "required": False
            }

            response = requests.post(custom_fields_url, json=payload)
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
                "customer_guid": self.valid_customer_guid,
                "chat_id": self.valid_chat_id,
                "priority": "medium",
                "reported_by": "user@example.com",
                "assigned": "agent@example.com",
                "custom_fields": {
                    field_name: custom_field_value
                }
            }

            response = requests.post(ticket_url, json=ticket_data)
            if response.status_code != HTTPStatus.CREATED:
                logger.error(f"Failed to create ticket for '{field_name}': {response.text}")
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create ticket with '{field_name}'")

            ticket_id = response.json().get("ticket_id")
            self.tickets.append(ticket_id)
            logger.info(f"Created ticket '{ticket_id}' with custom field '{field_name}'")

        # Step 3: Delete Tickets Individually
        for ticket_id in self.tickets:
            delete_url = f"{ticket_url}/{ticket_id}?customer_guid={self.valid_customer_guid}"
            response = requests.delete(delete_url)
            if response.status_code != HTTPStatus.OK:
                logger.error(f"Failed to delete ticket '{ticket_id}': {response.text}")
            self.assertEqual(response.status_code, HTTPStatus.OK, f"Failed to delete ticket '{ticket_id}'")
            logger.info(f"Successfully deleted ticket '{ticket_id}'")

            logger.info(f"Verifying ticket {ticket_id} no longer exists.")
            response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                    params={"customer_guid": self.valid_customer_guid})
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
                "customer_guid": self.valid_customer_guid,
                "field_name": field_name,
                "field_type": field_type,
                "required": False
            }
            response = requests.post(custom_fields_url, json=payload)
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create custom field {field_name}")
            self.custom_fields[field_name] = field_type

        logger.info(f"Custom fields created: {self.custom_fields}")

        # Create 50 tickets with custom fields
        tickets = [
            {
                "customer_guid": self.valid_customer_guid,
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
            response = requests.post(f"{self.BASE_URL}/tickets", json=ticket)
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
                                       params={"customer_guid": self.valid_customer_guid})
            if response.status_code != HTTPStatus.OK:
                logger.error(f"Failed to delete ticket {ticket_id}. Server response: {response.text}")
            self.assertEqual(response.status_code, HTTPStatus.OK, f"Failed to delete ticket {ticket_id}")
            logger.info(f"Successfully deleted ticket {ticket_id}.")

        # Step 2: Verify the deleted tickets no longer exist
        for ticket_id in ticket_ids_to_delete:
            logger.info(f"Verifying ticket {ticket_id} no longer exists.")
            response = requests.get(f"{self.BASE_URL}/tickets/{ticket_id}",
                                    params={"customer_guid": self.valid_customer_guid})
            logger.info(f"Get ticket {ticket_id} response status: {response.status_code}")
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,
                             f"Ticket {ticket_id} should not exist but was found.")
            self.assertIn("not found", response.json().get("detail", "").lower(),
                          f"Unexpected error message for ticket {ticket_id}: {response.json().get('detail')}")
            logger.info(f"Confirmed ticket {ticket_id} does not exist.")

    def tearDown(self):
        """Clean up resources if necessary."""
        logger.info(f"Finished test: {self._testMethodName}")
        logger.info("=== Test teardown complete ===")


if __name__ == "__main__":
    unittest.main()

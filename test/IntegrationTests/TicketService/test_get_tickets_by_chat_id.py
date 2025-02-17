import sys
import time
import unittest
import logging
import requests
import uuid
from http import HTTPStatus
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.backend.utils.api_utils import add_customer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestGetTicketsByChatId(unittest.TestCase):

    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT')}"
    allowed_custom_field_sql_types = ["VARCHAR(255)", "INT", "BOOLEAN", "DATETIME", "MEDIUMTEXT", "FLOAT", "TEXT"]

    def setUp(self):
        """Set up a valid customer and chat for tests."""
        logger.info("=== Setting up test environment ===")
        # Create a valid customer
        self.valid_customer_guid = add_customer("_org_id_123").get("customer_guid")

        # Create a valid chat
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "How can I reset my password?"
        }
        response = requests.post(chat_url, json=chat_data)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create a chat")
        self.valid_chat_id = response.json().get("chat_id")
        self.custom_fields = {}
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_get_tickets_by_chat_id_success(self):
        """Test retrieving tickets by a valid chat ID."""

        # Create a ticket linked to the chat
        ticket_url = f"{self.BASE_URL}/tickets"
        ticket_data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "title": "Reset Password",
            "description": "Unable to reset password",
            "priority": "high",
            "reported_by": "user1",
            "assigned": "agent1"
        }
        response = requests.post(ticket_url, json=ticket_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a ticket")
        self.valid_ticket_id = response.json().get("ticket_id")

        # Retrieve tickets for a valid chat ID and customer GUID
        response = requests.get(
            f"{self.BASE_URL}/tickets",
            params={
                "customer_guid": self.valid_customer_guid,
                "chat_id": self.valid_chat_id,
                "page": 1,
                "page_size": 10
            }
        )
        # Validate the response status
        self.assertEqual(response.status_code, HTTPStatus.OK, "Expected 200 OK for valid chat ID")

        # Parse the response JSON
        tickets = response.json()

        # Validate the response format and content
        self.assertTrue(isinstance(tickets, list), "Expected a list of tickets")
        self.assertEqual(len(tickets), 1, "Expected at least one ticket")
        self.assertEqual(tickets[0]["ticket_id"], "1", "Ticket ID mismatch")
        self.assertEqual(tickets[0]["title"], "Reset Password", "Title mismatch")
        self.assertEqual(tickets[0]["status"], "open", "Status mismatch")
        self.assertIn("created_at", tickets[0], "created_at not found")

    def test_get_tickets_no_tickets_found_for_valid_chat_id(self):
        """Test retrieving tickets when no tickets exist for a valid chat ID and customer GUID."""
        # Create a valid chat without adding tickets
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "Can I change my subscription plan?"
        }
        response = requests.post(chat_url, json=chat_data)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create a chat")
        new_chat_id = response.json().get("chat_id")

        # Attempt to retrieve tickets for the new chat ID with no tickets
        response = requests.get(
            f"{self.BASE_URL}/tickets",
            params={
                "customer_guid": self.valid_customer_guid,
                "chat_id": new_chat_id,
                "page": 1,
                "page_size": 10
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,
                         "Expected 404 NOT FOUND for valid chat ID with no tickets")
        self.assertEqual(
            response.json().get("detail"),
            f"No tickets found for chat_id {new_chat_id}",
            "Mismatch in error detail for no tickets found"
        )

    def test_get_tickets_by_invalid_chat_id(self):
        """Test retrieving tickets with an invalid chat ID."""
        invalid_chat_id = str(uuid.uuid4())
        response = requests.get(
            f"{self.BASE_URL}/tickets/",
            params={
                "customer_guid": self.valid_customer_guid,
                "chat_id": invalid_chat_id,
                "page": 1,
                "page_size": 10
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 404 NOT FOUND for invalid chat ID")
        self.assertEqual(response.json(), {
            "detail": f"Invalid chat_id: {invalid_chat_id} does not exist."
        })

    def test_get_tickets_with_invalid_customer_guid(self):
        """Test retrieving tickets with an invalid customer GUID."""
        invalid_customer_guid = str(uuid.uuid4())
        response = requests.get(
            f"{self.BASE_URL}/tickets/",
            params={
                "customer_guid": invalid_customer_guid,
                "chat_id": self.valid_chat_id,
                "page": 1,
                "page_size": 10
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 BAD REQUEST for invalid customer GUID")
        self.assertEqual(response.json(), {
            "detail": f"Database customer_{invalid_customer_guid} does not exist"
        })

    def _add_50_tickets(self):
        """Add 50 tickets for a valid customer and chat."""
        logger.info("Adding 50 tickets for the customer and chat.")

        # Create 50 tickets with unique titles
        tickets = [
            {
                "customer_guid": self.valid_customer_guid,
                "chat_id": self.valid_chat_id,
                "title": f"Ticket {i}",
                "description": f"Description for ticket {i}",
                "priority": "high" if i % 2 == 0 else "low",
                "reported_by": f"user{i}",
                "assigned": f"agent{i}"
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
        logger.info("Successfully added 50 tickets.")

    def test_pagination_for_tickets_by_chat_id(self):
        """Test pagination for tickets retrieved by chat ID."""
        logger.info("Testing pagination for tickets with different page sizes.")

        # Add 50 tickets for testing pagination
        self._add_50_tickets()

        # Define different page sizes for pagination testing
        page_sizes = [10, 20, 50]

        for per_page in page_sizes:
            logger.info(f"Testing with per_page={per_page}")

            # Initialize a list to collect all tickets across pages
            all_tickets = []

            # Fetch tickets page by page
            page_num = 1
            while True:
                page_url = f"{self.BASE_URL}/tickets?customer_guid={self.valid_customer_guid}&chat_id={self.valid_chat_id}&page={page_num}&page_size={per_page}"
                response = requests.get(page_url)

                if response.status_code == HTTPStatus.NOT_FOUND:
                    logger.info(f"Reached the end of available pages for per_page={per_page}")
                    break

                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f"Failed to fetch page {page_num} for per_page={per_page}"
                )

                # Parse the response JSON
                page_data = response.json()
                all_tickets.extend(page_data)

                if len(page_data) < per_page:
                    break

                page_num += 1

            # Check that the tickets are sorted by created_at in descending order
            created_at_list = [ticket["created_at"] for ticket in all_tickets]
            self.assertTrue(
                all(created_at_list[i] >= created_at_list[i + 1] for i in range(len(created_at_list) - 1)),
                "Tickets are not sorted by created_at in descending order"
            )

            # Validate the total number of tickets retrieved
            self.assertEqual(
                len(all_tickets),
                50,
                f"Total tickets retrieved with per_page={per_page} should be 50"
            )

            # Validate ticket IDs are in reverse order
            expected_ticket_ids = [str(i) for i in range(50, 0, -1)]
            retrieved_ticket_ids = [ticket["ticket_id"] for ticket in all_tickets]

            self.assertEqual(
                expected_ticket_ids,
                retrieved_ticket_ids,
                "Mismatch in expected and retrieved ticket IDs"
            )

            # Test the 'status' field for expected values
            for ticket in all_tickets:
                self.assertEqual(
                    ticket["status"], "open",
                    f"Unexpected status value {ticket['status']} for ticket {ticket['ticket_id']}"
                )

            expected_ticket_titles = [f"Ticket {i}" for i in range(50, 0, -1)]
            retrieved_ticket_titles = [ticket["title"] for ticket in all_tickets]

            # Test the 'title' field for correct format
            self.assertEqual(
                expected_ticket_titles,
                retrieved_ticket_titles,
                "Mismatch in expected and retrieved ticket IDs"
            )

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

    def test_pagination_for_tickets_with_custom_fields(self):
        """Test pagination for tickets with custom fields retrieved by chat ID."""
        logger.info("Testing pagination for tickets with custom fields and different page sizes.")

        # Add 50 tickets with custom fields for testing pagination
        self._add_50_tickets_with_custom_fields()

        # Define different page sizes for pagination testing
        page_sizes = [10, 20, 50]

        for per_page in page_sizes:
            logger.info(f"Testing with per_page={per_page}")

            # Initialize a list to collect all tickets across pages
            all_tickets = []

            # Fetch tickets page by page
            page_num = 1
            while True:
                page_url = f"{self.BASE_URL}/tickets?customer_guid={self.valid_customer_guid}&chat_id={self.valid_chat_id}&page={page_num}&page_size={per_page}"
                response = requests.get(page_url)

                if response.status_code == HTTPStatus.NOT_FOUND:
                    logger.info(f"Reached the end of available pages for per_page={per_page}")
                    break

                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f"Failed to fetch page {page_num} for per_page={per_page}"
                )

                # Parse the response JSON
                page_data = response.json()
                all_tickets.extend(page_data)

                if len(page_data) < per_page:
                    break

                page_num += 1

            # Check that the tickets are sorted by created_at in descending order
            created_at_list = [ticket["created_at"] for ticket in all_tickets]
            self.assertTrue(
                all(created_at_list[i] >= created_at_list[i + 1] for i in range(len(created_at_list) - 1)),
                "Tickets are not sorted by created_at in descending order"
            )

            # Validate the total number of tickets retrieved
            self.assertEqual(
                len(all_tickets),
                50,
                f"Total tickets retrieved with per_page={per_page} should be 50"
            )

            # Validate ticket IDs are in reverse order
            expected_ticket_ids = [str(i) for i in range(50, 0, -1)]
            retrieved_ticket_ids = [ticket["ticket_id"] for ticket in all_tickets]

            self.assertEqual(
                expected_ticket_ids,
                retrieved_ticket_ids,
                "Mismatch in expected and retrieved ticket IDs"
            )

            # Test the 'status' field for expected values
            for ticket in all_tickets:
                self.assertEqual(
                    ticket["status"], "open",
                    f"Unexpected status value {ticket['status']} for ticket {ticket['ticket_id']}"
                )

            expected_ticket_titles = [f"Ticket {i}" for i in range(50, 0, -1)]
            retrieved_ticket_titles = [ticket["title"] for ticket in all_tickets]

            # Test the 'title' field for correct format
            self.assertEqual(
                expected_ticket_titles,
                retrieved_ticket_titles,
                "Mismatch in expected and retrieved ticket IDs"
            )

    def _delete_ticket(self, ticket_id):
        """Delete a specific ticket."""
        logger.info(f"Deleting ticket {ticket_id}.")
        response = requests.delete(f"{self.BASE_URL}/tickets/{ticket_id}",
                                   params={"customer_guid": self.valid_customer_guid})
        if response.status_code != HTTPStatus.OK:
            logger.error(f"Failed to delete ticket {ticket_id}. Server response: {response.text}")
        self.assertEqual(response.status_code, HTTPStatus.OK, f"Failed to delete ticket {ticket_id}")
        logger.info(f"Successfully deleted ticket {ticket_id}.")

    def test_pagination_and_deletion_for_tickets_by_chat_id(self):
        """Test pagination for tickets retrieved by chat ID, including ticket deletion."""
        logger.info("Testing pagination for tickets with different page sizes and deletion.")

        # Add 50 tickets for testing pagination
        self._add_50_tickets()

        # Define different page sizes for pagination testing
        page_sizes = [10, 20, 50]

        # List of ticket IDs to delete for the test
        ticket_ids_to_delete = [10, 20, 25, 35, 42]

        # Delete specific tickets
        for ticket_id in ticket_ids_to_delete:
            self._delete_ticket(ticket_id)

        for per_page in page_sizes:
            logger.info(f"Testing with per_page={per_page}")

            # Initialize a list to collect all tickets across pages
            all_tickets = []

            # Fetch tickets page by page
            page_num = 1
            while True:
                page_url = f"{self.BASE_URL}/tickets?customer_guid={self.valid_customer_guid}&chat_id={self.valid_chat_id}&page={page_num}&page_size={per_page}"
                response = requests.get(page_url)

                if response.status_code == HTTPStatus.NOT_FOUND:
                    logger.info(f"Reached the end of available pages for per_page={per_page}")
                    break

                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f"Failed to fetch page {page_num} for per_page={per_page}"
                )

                # Parse the response JSON
                page_data = response.json()
                all_tickets.extend(page_data)

                if len(page_data) < per_page:
                    break

                page_num += 1

            # Check that the tickets are sorted by created_at in descending order
            created_at_list = [ticket["created_at"] for ticket in all_tickets]
            self.assertTrue(
                all(created_at_list[i] >= created_at_list[i + 1] for i in range(len(created_at_list) - 1)),
                "Tickets are not sorted by created_at in descending order"
            )

            # Ensure deleted tickets are not included
            deleted_ticket_ids = set(ticket_ids_to_delete)
            retrieved_ticket_ids = {ticket["ticket_id"] for ticket in all_tickets}
            self.assertTrue(deleted_ticket_ids.isdisjoint(retrieved_ticket_ids),
                            "Deleted tickets should not be included in the retrieved tickets.")

            logger.info(f"All retrieved ticket IDs: {retrieved_ticket_ids}")

            # Validate the total number of tickets retrieved
            self.assertEqual(
                len(all_tickets),
                45,  # 50 - 5 deleted tickets
                f"Total tickets retrieved with per_page={per_page} should be 45"
            )

            # Validate ticket IDs are in reverse order (excluding deleted ones)
            expected_ticket_ids = [str(i) for i in range(50, 0, -1) if i not in ticket_ids_to_delete]
            retrieved_ticket_ids = [ticket["ticket_id"] for ticket in all_tickets]

            self.assertEqual(
                expected_ticket_ids,
                retrieved_ticket_ids,
                "Mismatch in expected and retrieved ticket IDs"
            )

            # Test the 'status' field for expected values
            for ticket in all_tickets:
                self.assertEqual(
                    ticket["status"], "open",
                    f"Unexpected status value {ticket['status']} for ticket {ticket['ticket_id']}"
                )

            expected_ticket_titles = [f"Ticket {i}" for i in range(50, 0, -1) if i not in ticket_ids_to_delete]
            retrieved_ticket_titles = [ticket["title"] for ticket in all_tickets]

            # Test the 'title' field for correct format
            self.assertEqual(
                expected_ticket_titles,
                retrieved_ticket_titles,
                "Mismatch in expected and retrieved ticket titles"
            )

            logger.info(f"Successfully verified tickets for per_page={per_page}.")

    def tearDown(self):
        """Clean up after tests."""
        logger.info(f"=== Test {self._testMethodName} completed and passed ===")
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

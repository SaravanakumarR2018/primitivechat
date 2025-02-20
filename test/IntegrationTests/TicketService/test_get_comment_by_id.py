import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestGetCommentByIdAPI(unittest.TestCase):

    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        """Set up test environment by creating a customer, ticket, and a comment."""
        logger.info("=== Setting up test environment ===")

        # Add customer
        self.valid_customer_guid = add_customer("test_org").get("customer_guid")

        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "Initial question"
        }
        response = requests.post(chat_url, json=chat_data)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create a chat")
        self.valid_chat_id = response.json().get("chat_id")

        # Add ticket
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
        self.valid_ticket_id = response.json().get("ticket_id")

        # Add comment
        comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }

        response = requests.post(comment_url, json=comment_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a comment")
        self.valid_comment_id = response.json().get("comment_id")
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_get_comment_by_id_success(self):
        """Test getting a comment by ID with valid ticket ID and customer GUID."""
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{self.valid_comment_id}"
        params = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the comment")

        comment_response = response.json()
        self.assertEqual(comment_response["comment_id"], str(self.valid_comment_id), "Incorrect comment_id")
        self.assertEqual(comment_response["ticket_id"], str(self.valid_ticket_id), "Incorrect ticket_id")
        self.assertEqual(comment_response["comment"], "This is a test comment", "Incorrect comment text")
        self.assertEqual(comment_response["posted_by"], "test_user", "Incorrect posted_by")
        self.assertIn("created_at", comment_response, "Missing 'created_at' timestamp")
        self.assertIn("updated_at", comment_response, "Missing 'updated_at' timestamp")

    def test_get_comment_wrong_comment_id(self):
        """Test getting a comment with an invalid comment ID."""
        invalid_comment_id = "invalid_comment_id" # Assuming 57 is an invalid comment ID for this ticket
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{invalid_comment_id}"
        params = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected 404 for invalid comment_id")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Comment with comment_id {invalid_comment_id} not found for ticket id {self.valid_ticket_id}",
                         "Unexpected error message for invalid comment_id")

    def test_get_comment_wrong_customer_guid(self):
        """Test getting a comment with an invalid customer GUID."""
        invalid_customer_guid = "a39a3076-f45f-4bb1-9945-700330b5e541"  # Invalid GUID
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{self.valid_comment_id}"
        params = {
            "customer_guid": invalid_customer_guid,
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 for invalid customer_guid")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Database customer_{invalid_customer_guid} does not exist",
                         "Unexpected error message for invalid customer_guid")

    def test_get_comment_invalid_ticket_id(self):
        """Test getting a comment with an invalid ticket ID."""
        invalid_ticket_id = 12  # Invalid ticket ID for this test
        comment_url = f"{self.BASE_URL}/tickets/{invalid_ticket_id}/comments/{self.valid_comment_id}"
        params = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": invalid_ticket_id
        }

        response = requests.get(comment_url, params=params)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 for invalid ticket_id")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Invalid ticket_id: {invalid_ticket_id} does not exist.",
                         "Unexpected error message for invalid ticket_id")

    def test_comment_timestamps(self):
        """Test that created_at and updated_at timestamps for comments are set and updated correctly."""

        # Create a comment
        comment_url = f"{self.BASE_URL}/add_comment"
        new_comment_data = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }

        response = requests.post(comment_url, json=new_comment_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a comment")
        comment_id = response.json().get("comment_id")

        # Get the created comment
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the comment")

        comment_data = response.json()
        created_at = comment_data["created_at"]
        updated_at = comment_data["updated_at"]

        self.assertIn("created_at", comment_data, "Missing 'created_at' timestamp for comment.")
        self.assertIn("updated_at", comment_data, "Missing 'updated_at' timestamp for comment.")

        import time
        time.sleep(1)

        # Update the comment
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id,
            "comment_id":comment_id
        }
        update_data = {
            "comment": "Updated test comment.",
            "posted_by": comment_data["posted_by"]
        }

        update_response = requests.put(update_comment_url, json=update_data, params=params)
        self.assertEqual(update_response.status_code, HTTPStatus.OK, "Failed to update the comment")

        # Get the updated comment
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the comment")

        updated_comment_data = response.json()
        updated_at_new = updated_comment_data["updated_at"]

        # Validate timestamps after update
        self.assertEqual(created_at, updated_comment_data["created_at"],
                         "created_at should not change on comment update.")
        self.assertNotEqual(updated_at, updated_at_new, "updated_at should change after comment update.")

        # Verify updated comment content
        self.assertEqual(updated_comment_data["comment"], "Updated test comment.",
                         "Comment text mismatch after update.")

    def tearDown(self):
        """Clean up after each test."""
        logger.info(f"=== Test Case {self._testMethodName} Completed ===")
        logger.info("Tear Down Completed")

if __name__ == "__main__":
    unittest.main()

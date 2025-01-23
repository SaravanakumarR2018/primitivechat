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

class TestDeleteCommentAPI(unittest.TestCase):
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        """Set up test environment by creating a customer, ticket, and a comment."""
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

    def delete_comment(self, ticket_id, comment_id, customer_guid):
        """Helper function to delete a comment."""
        url = f"{self.BASE_URL}/delete_comment"
        params = {
            "ticket_id": ticket_id,
            "comment_id": comment_id,
            "customer_guid": customer_guid
        }
        response = requests.delete(url, params=params)
        return response

    def test_delete_comment_success(self):
        """Test deleting a comment successfully."""
        response = self.delete_comment(self.valid_ticket_id, self.valid_comment_id, self.valid_customer_guid)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete the comment")
        self.assertEqual(response.json()["status"], "deleted", "Comment was not deleted successfully")

        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{self.valid_comment_id}"
        params = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected 404 for invalid comment_id")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Comment with comment_id {self.valid_comment_id} not found for ticket id {self.valid_ticket_id}",
                         "Unexpected error message for invalid comment_id")

    def test_delete_comment_not_found(self):
        """Test deleting a non-existent comment should return 404."""
        response = self.delete_comment(self.valid_ticket_id, self.valid_comment_id, self.valid_customer_guid)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete the comment")
        self.assertEqual(response.json()["status"], "deleted", "Comment was not deleted successfully")

    def test_delete_comment_invalid_customer_guid(self):
        """Test deleting a comment with an invalid customer GUID should fail."""
        response = self.delete_comment(self.valid_ticket_id, self.valid_comment_id, "invalid-guid")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected failure for invalid customer_guid")
        self.assertIn("detail", response.json(), "Expected error detail message")

    def test_delete_comment_invalid_ticket_id(self):
        """Test deleting a comment with an invalid ticket ID should return 404."""
        invalid_ticket_id = 999999  # Assuming this ticket ID does not exist
        response = self.delete_comment(invalid_ticket_id, self.valid_comment_id, self.valid_customer_guid)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected 404 for invalid ticket_id")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Invalid Ticket ID. {invalid_ticket_id} does not exist.",
                         "Unexpected error message for invalid ticket_id")

    def tearDown(self):
        """Clean up resources after tests."""
        logger.info(f"=== Test Case {self._testMethodName} Completed ===")

if __name__ == "__main__":
    unittest.main()

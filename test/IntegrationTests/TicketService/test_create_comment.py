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

class TestCreateCommentAPI(unittest.TestCase):

    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        """Set up test environment by creating a customer and ticket."""
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
        logger.info(f"Ticket created with ID: {self.valid_ticket_id}")
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_create_comment_success(self):
        """Test creating a comment for a valid ticket."""
        comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }

        response = requests.post(comment_url, json=comment_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a comment")

        comment_response = response.json()
        self.assertIn("comment_id", comment_response, "Response missing 'comment_id'")
        self.assertEqual(comment_response["ticket_id"], self.valid_ticket_id, "Incorrect ticket ID in response")
        self.assertEqual(comment_response["posted_by"], "test_user", "Incorrect 'posted_by' in response")
        self.assertEqual(comment_response["comment"], "This is a test comment", "Incorrect comment text in response")
        self.assertIn("created_at", comment_response, "created at not exist")
        self.assertIn("updated_at", comment_response, "updated at not exist")

    def test_create_comment_invalid_ticket(self):
        """Test creating a comment for an invalid ticket."""
        comment_url = f"{self.BASE_URL}/add_comment"
        invalid_ticket_id="invalid_ticket_id"
        comment_data = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": invalid_ticket_id,
            "posted_by": "test_user",
            "comment": "Invalid ticket test"
        }

        response = requests.post(comment_url, json=comment_data)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected failure for invalid ticket")

        error_detail = response.json().get("detail")
        expected_error_message = f"Invalid ticket_id: {invalid_ticket_id} does not exist."
        self.assertEqual(error_detail, expected_error_message, "Unexpected error message for invalid ticket")

    def test_create_comment_invalid_customer_guid(self):
        comment_url = f"{self.BASE_URL}/add_comment"
        invalid_customer_guid = "invalid_customer_guid"
        comment_data = {
            "customer_guid": invalid_customer_guid,
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "Invalid ticket test"
        }

        response_data = requests.post(comment_url, json=comment_data)
        self.assertEqual(response_data.status_code, HTTPStatus.BAD_REQUEST, "Expected failure for invalid ticket")

        # Parse the response data
        response_data = response_data.json()

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

    def test_create_comment_missing_fields(self):
        """Test creating a comment with missing fields and verify 422 response."""
        comment_url = f"{self.BASE_URL}/add_comment"

        # Missing 'comment' field
        incomplete_comment_data = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_chat_id,
            "posted_by": "test_user"
        }

        response = requests.post(comment_url, json=incomplete_comment_data)

        # Check status code for 422 Unprocessable Entity
        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY,
                         "Expected status code 422 for missing fields")

        # Check for error details indicating missing fields
        error_details = response.json().get("detail")
        self.assertIsInstance(error_details, list, "Error detail should be a list of validation errors")

        # Validate presence of specific missing field message
        missing_field_message = any("comment" in str(error) for error in error_details)
        self.assertTrue(missing_field_message, "Error message should indicate missing 'comment' field")

    def test_create_comment_missing_customer_guid(self):
        """Test creating a comment with missing customer_guid field."""
        comment_url = f"{self.BASE_URL}/add_comment"

        # Payload missing customer_guid
        incomplete_comment_data = {
            "ticket_id": "123",
            "posted_by": "user123",
            "comment": "Test comment"
        }

        response = requests.post(comment_url, json=incomplete_comment_data)

        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY,
                         "Expected status code 422 for missing customer_guid")
        self.assertIn("customer_guid", str(response.json()["detail"]),
                      "Error should indicate missing 'customer_guid' field")

    def test_create_comment_missing_ticket_id(self):
        """Test creating a comment with missing ticket_id field."""
        comment_url = f"{self.BASE_URL}/add_comment"

        # Payload missing ticket_id
        incomplete_comment_data = {
            "customer_guid": "cust-123",
            "posted_by": "user123",
            "comment": "Test comment"
        }

        response = requests.post(comment_url, json=incomplete_comment_data)

        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY,
                         "Expected status code 422 for missing ticket_id")
        self.assertIn("ticket_id", str(response.json()["detail"]),
                      "Error should indicate missing 'ticket_id' field")

    def test_create_comment_missing_posted_by(self):
        """Test creating a comment with missing posted_by field."""
        comment_url = f"{self.BASE_URL}/add_comment"

        # Payload missing posted_by
        incomplete_comment_data = {
            "customer_guid": "cust-123",
            "ticket_id": "123",
            "comment": "Test comment"
        }

        response = requests.post(comment_url, json=incomplete_comment_data)

        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY,
                         "Expected status code 422 for missing posted_by")
        self.assertIn("posted_by", str(response.json()["detail"]),
                      "Error should indicate missing 'posted_by' field")

    def tearDown(self):
        """Clean up after each test."""
        logger.info(f"=== Test Case {self._testMethodName} Completed ===")

if __name__ == "__main__":
    unittest.main()

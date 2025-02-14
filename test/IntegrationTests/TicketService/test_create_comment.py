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

        # Get the comment ID for verification
        comment_id = response.json().get("comment_id")

        # Step 2: Retrieve the comment using the valid ticket_id and customer_guid
        get_comment_url = (f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
                           f"?customer_guid={self.valid_customer_guid}&ticket_id={self.valid_ticket_id}")

        response_get = requests.get(get_comment_url)
        self.assertEqual(response_get.status_code, HTTPStatus.OK, "Failed to retrieve the comment")

        # Step 3: Validate the retrieved comment data
        retrieved_comment = response.json()
        self.assertEqual(retrieved_comment["comment_id"], comment_id, "Comment ID mismatch")
        self.assertEqual(retrieved_comment["ticket_id"], self.valid_ticket_id, "Ticket ID mismatch")
        self.assertEqual(retrieved_comment["posted_by"], "test_user", "Incorrect 'posted_by' field")
        self.assertEqual(retrieved_comment["comment"], "This is a test comment",
                         "Incorrect comment content")

        # Step 4: Check for timestamps in the response
        self.assertIn("created_at", retrieved_comment, "Missing 'created_at' timestamp")
        self.assertIn("updated_at", retrieved_comment, "Missing 'updated_at' timestamp")

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

    def _add_50_comments(self, number_of_comments=50):
        comment_url = f"{self.BASE_URL}/add_comment"

        for i in range(1, number_of_comments + 1):
            comment_data = {
                "customer_guid": self.valid_customer_guid,
                "ticket_id": self.valid_ticket_id,
                "posted_by": f"user_{i}",
                "comment": f"This is test comment number {i}"
            }

            response = requests.post(comment_url, json=comment_data)
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create comment #{i}")
            logger.info(f"Comment #{i} added successfully")

    def test_pagination_for_comments_by_ticket_id(self):
        """Test pagination for comments retrieved by ticket ID."""
        logger.info("Testing pagination for comments with different page sizes.")

        # Add 50 comments to the ticket for testing pagination
        self._add_50_comments()

        # Define different page sizes for pagination testing
        page_sizes = [10, 20, 50]

        for per_page in page_sizes:
            logger.info(f"Testing with per_page={per_page}")

            # Initialize a list to collect all comments across pages
            all_comments = []

            # Fetch comments page by page
            page_num = 1
            while True:
                page_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments?customer_guid={self.valid_customer_guid}&page={page_num}&page_size={per_page}"
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
                all_comments.extend(page_data)

                if len(page_data) < per_page:
                    break

                page_num += 1

            # Check that the comments are sorted by created_at in descending order
            created_at_list = [comment["created_at"] for comment in all_comments]
            self.assertTrue(
                all(created_at_list[i] >= created_at_list[i + 1] for i in range(len(created_at_list) - 1)),
                "Comments are not sorted by created_at in descending order"
            )

            # Validate the total number of comments retrieved
            self.assertEqual(
                len(all_comments),
                50,
                f"Total comments retrieved with per_page={per_page} should be 50"
            )

            # Validate comment IDs are in reverse order
            expected_comment_ids = [str(i) for i in range(50, 0, -1)]
            retrieved_comment_ids = [comment["comment_id"] for comment in all_comments]

            self.assertEqual(
                expected_comment_ids,
                retrieved_comment_ids,
                "Mismatch in expected and retrieved comment IDs"
            )

            # Test the 'posted_by' field for correct data
            expected_posted_by = [f"user_{i}" for i in range(50, 0, -1)]
            retrieved_posted_by = [comment["posted_by"] for comment in all_comments]
            self.assertEqual(expected_posted_by, retrieved_posted_by, "Mismatch in expected and retrieved comment posted_by")

            # Test the 'comment' field for expected content
            expected_comment_texts = [f"This is test comment number {i}" for i in range(50, 0, -1)]
            retrieved_comment_texts = [comment["comment"] for comment in all_comments]

            self.assertEqual(
                expected_comment_texts,
                retrieved_comment_texts,
                "Mismatch in expected and retrieved comment texts"
            )

    def tearDown(self):
        """Clean up after each test."""
        logger.info(f"=== Test Case {self._testMethodName} Completed ===")
        logger.info("Tear Down Completed")

if __name__ == "__main__":
    unittest.main()

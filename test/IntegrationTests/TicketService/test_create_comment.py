import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer, create_test_token, create_token_without_org_role, create_token_without_org_id
from src.backend.lib.logging_config import get_primitivechat_logger

# Configure logging
logger = get_primitivechat_logger(__name__)

class TestCreateCommentAPI(unittest.TestCase):

    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"
    ORG_ROLE = 'org:admin'
    def setUp(self):
        """Set up test environment by creating a customer and ticket."""
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

        # Add ticket
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
        self.valid_ticket_id = response.json().get("ticket_id")
        logger.info(f"Ticket created with ID: {self.valid_ticket_id}")
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_create_comment_success(self):
        """Test creating a comment for a valid ticket."""
        comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }

        response = requests.post(comment_url, json=comment_data, headers=self.headers)
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
                           f"?ticket_id={self.valid_ticket_id}")

        response_get = requests.get(get_comment_url, headers=self.headers)
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
            "ticket_id": invalid_ticket_id,
            "posted_by": "test_user",
            "comment": "Invalid ticket test"
        }

        response = requests.post(comment_url, json=comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected failure for invalid ticket")

        error_detail = response.json().get("detail")
        expected_error_message = f"Invalid ticket_id: {invalid_ticket_id} does not exist."
        self.assertEqual(error_detail, expected_error_message, "Unexpected error message for invalid ticket")

    def test_create_comment_invalid_org_id_or_customer_guid(self):
        comment_url = f"{self.BASE_URL}/add_comment"
        invalid_token = create_test_token(org_id="invalid_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "Invalid ticket test"
        }

        response_data = requests.post(comment_url, json=comment_data, headers=headers)
        self.assertEqual(response_data.status_code, HTTPStatus.BAD_REQUEST, "Expected failure for invalid ticket")

        # Parse the response data
        response_data = response_data.json()

        # Assert the error message contains the expected invalid customer_guid
        self.assertIn(
            "detail",
            response_data,
            "Response should contain 'detail' key."
        )
        expected_message = f"Database customer_None does not exist"
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
            "ticket_id": self.valid_chat_id,
            "posted_by": "test_user"
        }

        response = requests.post(comment_url, json=incomplete_comment_data, headers=self.headers)

        # Check status code for 422 Unprocessable Entity
        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY,
                         "Expected status code 422 for missing fields")

        # Check for error details indicating missing fields
        error_details = response.json().get("detail")
        self.assertIsInstance(error_details, list, "Error detail should be a list of validation errors")

        # Validate presence of specific missing field message
        missing_field_message = any("comment" in str(error) for error in error_details)
        self.assertTrue(missing_field_message, "Error message should indicate missing 'comment' field")

    def test_create_comment_missing_ticket_id(self):
        """Test creating a comment with missing ticket_id field."""
        comment_url = f"{self.BASE_URL}/add_comment"

        # Payload missing ticket_id
        incomplete_comment_data = {
            "posted_by": "user123",
            "comment": "Test comment"
        }

        response = requests.post(comment_url, json=incomplete_comment_data, headers=self.headers)

        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY,
                         "Expected status code 422 for missing ticket_id")
        self.assertIn("ticket_id", str(response.json()["detail"]),
                      "Error should indicate missing 'ticket_id' field")

    def test_create_comment_missing_posted_by(self):
        """Test creating a comment with missing posted_by field."""
        comment_url = f"{self.BASE_URL}/add_comment"

        # Payload missing posted_by
        incomplete_comment_data = {
            "ticket_id": "123",
            "comment": "Test comment"
        }

        response = requests.post(comment_url, json=incomplete_comment_data, headers=self.headers)

        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY,
                         "Expected status code 422 for missing posted_by")
        self.assertIn("posted_by", str(response.json()["detail"]),
                      "Error should indicate missing 'posted_by' field")

    def _add_50_comments(self, number_of_comments=50):
        comment_url = f"{self.BASE_URL}/add_comment"

        for i in range(1, number_of_comments + 1):
            comment_data = {
                "ticket_id": self.valid_ticket_id,
                "posted_by": f"user_{i}",
                "comment": f"This is test comment number {i}"
            }

            response = requests.post(comment_url, json=comment_data, headers=self.headers)
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
                page_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments?page={page_num}&page_size={per_page}"
                response = requests.get(page_url, headers=self.headers)

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
            retrieved_comment_ids = [str(comment["comment_id"]) for comment in all_comments]

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

    def test_create_comment_no_token(self):
        """Test API request without an authentication token."""
        url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": f"user",
            "comment": f"This is test comment"
        }

        response = requests.post(url, json=comment_data) # No headers
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Missing token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Missing Token leads to Unauthorized")

    def test_create_comment_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": f"user",
            "comment": f"This is test comment"
        }
        headers = {"Authorization": "Bearer corrupted_token"}
        response = requests.post(url, json=comment_data, headers=headers)
        logger.info("Testing API request with corrupted token")
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_create_comment_missing_org_id_in_token(self):
        """Test API request where the token does not have an org_id."""
        url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": f"user",
            "comment": f"This is test comment"
        }
        token = create_token_without_org_id(org_role=self.ORG_ROLE)  # No org_id
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("Testing API request with missing org_id in token")
        response = requests.post(url, json=comment_data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Missing org_id should result in 400 Bad Request")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_create_comment_missing_org_role_in_token(self):
        """Test API request where the token does not have an org_role."""
        url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": f"user",
            "comment": f"This is test comment"
        }
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        logger.info("Testing API request with missing org_role in token")
        response = requests.post(url, json=comment_data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN, "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_create_comment_unauthorized_org_role(self):
        headers={}
        # Assuming an endpoint `/addcustomer` to create a new customer
        data = add_customer("test_org")
        org_id = data.get("org_id")

        # Create Test Token for member (not allowed)
        token = create_test_token(org_id=org_id, org_role="org:random_org_role")
        headers['Authorization'] = f'Bearer {token}'

        url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": f"user",
            "comment": f"This is test comment"
        }
        response = requests.post(url, json=comment_data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_create_comment_invalid_org_id_no_mapped_customer_guid(self):
        """Test API request with an org_id that has no mapped customer_guid."""
        url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": f"user",
            "comment": f"This is test comment"
        }
        invalid_token = create_test_token(org_id="unmapped_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        logger.info("Testing API request with org_id that has no mapped customer_guid")
        response = requests.post(url, json=comment_data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Unmapped org_id should result in 400 Bad Request")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")

    def tearDown(self):
        """Clean up after each test."""
        logger.info(f"=== Test Case {self._testMethodName} Completed ===")
        logger.info("Tear Down Completed")

if __name__ == "__main__":
    unittest.main()

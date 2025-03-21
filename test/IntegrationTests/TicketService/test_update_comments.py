import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

from src.backend.lib.logging_config import log_format

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer, create_test_token, create_token_without_org_id, create_token_without_org_role

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=log_format
)
logger = logging.getLogger(__name__)

class TestUpdateCommentAPI(unittest.TestCase):

    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"
    ORG_ROLE = 'org:admin'
    def setUp(self):
        """Set up test environment by creating a customer, ticket, and comment."""
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

        # Add comment
        comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }

        response = requests.post(comment_url, json=comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a comment")
        self.valid_comment_id = response.json().get("comment_id")
        logger.info(f"Comment created with ID: {self.valid_comment_id}")
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_update_comment_success(self):
        """Test updating a comment successfully."""
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id
        }

        # Get the current comment details before the update
        get_comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{self.valid_comment_id}"
        comment_before_update_response = requests.get(get_comment_url, params=params, headers=self.headers)
        self.assertEqual(comment_before_update_response.status_code, HTTPStatus.OK,
                         "Failed to fetch comment before update")
        comment_before_update = comment_before_update_response.json()

        # Store initial values for comparison
        initial_created_at=comment_before_update.get("created_at")
        initial_updated_at = comment_before_update.get("updated_at")
        initial_is_edited = comment_before_update.get("is_edited")

        # Prepare the update data
        update_comment_data = {
            "comment": "This is an updated comment",
            "posted_by": "test_user"  # Ensure this matches the original posted_by
        }

        # Update the comment
        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to update the comment")

        # Get the updated comment
        updated_comment_response = requests.get(get_comment_url, params=params, headers=self.headers)
        self.assertEqual(updated_comment_response.status_code, HTTPStatus.OK, "Failed to fetch updated comment")
        updated_comment = updated_comment_response.json()

        # Check that the comment text has been updated
        self.assertEqual(updated_comment["comment"], "This is an updated comment", "Comment text was not updated")
        self.assertEqual(str(updated_comment["comment_id"]), str(self.valid_comment_id), "Comment ID mismatch")
        self.assertEqual(updated_comment["posted_by"], "test_user", "posted_by does not match")

        #Verify the 'created_at' remains same
        self.assertEqual(updated_comment['created_at'], initial_created_at, "The 'created_at' should not changed")

        # Verify the 'updated_at' has changed
        self.assertNotEqual(updated_comment["updated_at"], initial_updated_at,
                            "The 'updated_at' timestamp was not updated")

        # Verify the 'is_edited' field has been set to True (indicating the comment was edited)
        self.assertTrue(updated_comment["is_edited"], "The 'is_edited' field was not updated to True")

        # Ensure 'updated_at' timestamp is present in the response
        self.assertIn("updated_at", updated_comment, "'updated_at' timestamp not present")

    def test_update_comment_invalid_ticket_id(self):
        """Test updating a comment for an invalid ticket."""
        update_comment_url = f"{self.BASE_URL}/update_comment"
        invalid_ticket_id="9999"
        params = {
            "ticket_id": invalid_ticket_id,  # Invalid ticket_id
            "comment_id": self.valid_comment_id
        }
        update_comment_data = {
            "comment": "This comment update should fail",
            "posted_by": "test_user"  # Ensure posted_by is included
        }

        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected failure for invalid ticket ID")

        error_detail = response.json().get("detail")
        expected_error_message = f"Invalid Ticket ID. {invalid_ticket_id} does not exist."
        self.assertEqual(error_detail, expected_error_message, "Unexpected error message for invalid ticket ID")

    def test_update_comment_missing_fields(self):
        """Test updating a comment with missing required fields."""
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id,
        }

        # Payload missing the 'comment' and 'posted_by' fields
        incomplete_update_data = {}

        response = requests.put(update_comment_url, params=params, json=incomplete_update_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY, "Expected failure for missing fields")

        error_details = response.json().get("detail")
        self.assertIsInstance(error_details, list, "Error detail should be a list of validation errors")

        expected_errors = ["posted_by", "comment"]
        for field in expected_errors:
            self.assertTrue(
                any(field in str(error) for error in error_details),
                f"Error message should indicate missing '{field}' field"
            )

    def test_update_comment_invalid_org_id_or_customer_guid(self):
        """Test updating a comment with an invalid customer_guid."""
        invalid_token = create_test_token(org_id="invalid_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id,
        }
        update_comment_data = {
            "posted_by": "test_user",
            "comment": "This comment update should fail"
        }

        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected failure for invalid customer_guid")

        error_detail = response.json().get("detail")
        expected_error_message = "Database customer_None does not exist"
        self.assertEqual(error_detail, expected_error_message, "Unexpected error message for invalid customer_guid")

    def test_update_comment_invalid_comment_id(self):
        """Test updating a comment with an invalid comment_id."""
        update_comment_url = f"{self.BASE_URL}/update_comment"
        invalid_comment_id=90
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": invalid_comment_id,  # Invalid comment ID
        }
        update_comment_data = {
            "posted_by": "test_user",
            "comment": "This comment update should fail"
        }

        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected failure for invalid comment_id")

        error_detail = response.json().get("detail")
        expected_error_message = f"Comment ID {invalid_comment_id} not found for Ticket ID {self.valid_ticket_id}."
        self.assertEqual(error_detail, expected_error_message, "Unexpected error message for invalid comment_id")

    def test_update_comment_unauthorized_user(self):
        """Test updating a comment when posted_by does not match the original poster."""
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id,
        }
        update_comment_data = {
            "posted_by": "unauthorized_user",  # Different from the actual posted_by
            "comment": "This update should fail due to unauthorized access"
        }

        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                         "Expected failure for unauthorized comment update")

        error_detail = response.json().get("detail")
        expected_error_message = "You are not authorized to update this comment."
        self.assertEqual(error_detail, expected_error_message,
                         "Unexpected error message for unauthorized comment update")

    def test_update_comment_no_token(self):
        """Test API request without an authentication token."""
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id,
        }
        update_comment_data = {
            "posted_by": "user123",
            "comment": "This update should fail due to unauthorized access"
        }

        response = requests.put(update_comment_url, params=params, json=update_comment_data)  # No headers
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Missing token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Missing Token leads to Unauthorized")

    def test_update_comment_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        headers = {"Authorization": "Bearer corrupted_token"}
        logger.info("Testing API request with corrupted token")
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id,
        }
        update_comment_data = {
            "posted_by": "user1",  # Different from the actual posted_by
            "comment": "This update should fail due to unauthorized access"
        }

        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_update_comment_missing_org_id_in_token(self):
        """Test API request where the token does not have an org_id."""
        token = create_token_without_org_id(org_role=self.ORG_ROLE)  # No org_id
        headers = {"Authorization": f"Bearer {token}"}
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id,
        }
        update_comment_data = {
            "posted_by": "user1",  # Different from the actual posted_by
            "comment": "This update should fail due to unauthorized access"
        }

        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=headers)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Missing org_id should result in 400 Bad Request")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_update_comment_missing_org_role_in_token(self):
        """Test API request where the token does not have an org_role."""
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        logger.info("Testing API request with missing org_role in token")
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id,
        }
        update_comment_data = {
            "posted_by": "user1",  # Different from the actual posted_by
            "comment": "This update should fail due to unauthorized access"
        }
        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN, "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_update_comment_unauthorized_org_role(self):
        headers={}
        # Assuming an endpoint `/addcustomer` to create a new customer
        data = add_customer("test_org")
        org_id = data.get("org_id")

        # Create Test Token for member (not allowed)
        token = create_test_token(org_id=org_id, org_role="org:random_org_role")
        headers['Authorization'] = f'Bearer {token}'
        update_comment_url = f"{self.BASE_URL}/update_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id,
        }
        update_comment_data = {
            "posted_by": "user1",  # Different from the actual posted_by
            "comment": "This update should fail due to unauthorized access"
        }
        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_update_comment_invalid_org_id_no_mapped_customer_guid(self):
        """Test API request with an org_id that has no mapped customer_guid."""
        update_comment_url = f"{self.BASE_URL}/update_comment"
        invalid_token = create_test_token(org_id="unmapped_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": self.valid_comment_id,
        }
        update_comment_data = {
            "posted_by": "user1",  # Different from the actual posted_by
            "comment": "This update should fail due to unauthorized access"
        }
        response = requests.put(update_comment_url, params=params, json=update_comment_data, headers=headers)
        logger.info("Testing API request with org_id that has no mapped customer_guid")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Unmapped org_id should result in 400 Bad Request")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")

    def tearDown(self):
        """Clean up after each test."""
        logger.info(f"=== Test Case {self._testMethodName} Completed ===")
        logger.info("Tear Down Completed")

if __name__ == "__main__":
    unittest.main()

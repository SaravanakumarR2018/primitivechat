import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer, create_test_token, create_token_without_org_id, create_token_without_org_role
from src.backend.lib.logging_config import log_format

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=log_format
)
logger = logging.getLogger(__name__)

class TestGetCommentByIdAPI(unittest.TestCase):

    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"
    ORG_ROLE = 'org:admin'
    def setUp(self):
        """Set up test environment by creating a customer, ticket, and a comment."""
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
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_get_comment_by_id_success(self):
        """Test getting a comment by ID with valid ticket ID and customer GUID."""
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{self.valid_comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to retrieve the comment")

        comment_response = response.json()
        self.assertEqual(str(comment_response["comment_id"]), str(self.valid_comment_id), "Incorrect comment_id")
        self.assertEqual(str(comment_response["ticket_id"]), str(self.valid_ticket_id), "Incorrect ticket_id")
        self.assertEqual(comment_response["comment"], "This is a test comment", "Incorrect comment text")
        self.assertEqual(comment_response["posted_by"], "test_user", "Incorrect posted_by")
        self.assertIn("created_at", comment_response, "Missing 'created_at' timestamp")
        self.assertIn("updated_at", comment_response, "Missing 'updated_at' timestamp")

    def test_get_comment_wrong_comment_id(self):
        """Test getting a comment with an invalid comment ID."""
        invalid_comment_id = "invalid_comment_id" # Assuming 57 is an invalid comment ID for this ticket
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{invalid_comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected 404 for invalid comment_id")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Comment with comment_id {invalid_comment_id} not found for ticket id {self.valid_ticket_id}",
                         "Unexpected error message for invalid comment_id")

    def test_get_comment_wrong_org_id_or_customer_guid(self):
        """Test getting a comment with an invalid customer GUID."""
        invalid_token = create_test_token(org_id="invalid_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}  # Invalid GUID
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{self.valid_comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 for invalid customer_guid")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Database customer_None does not exist",
                         "Unexpected error message for invalid customer_guid")

    def test_get_comment_invalid_ticket_id(self):
        """Test getting a comment with an invalid ticket ID."""
        invalid_ticket_id = 12  # Invalid ticket ID for this test
        comment_url = f"{self.BASE_URL}/tickets/{invalid_ticket_id}/comments/{self.valid_comment_id}"
        params = {
            "ticket_id": invalid_ticket_id
        }

        response = requests.get(comment_url, params=params, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 for invalid ticket_id")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Invalid ticket_id: {invalid_ticket_id} does not exist.",
                         "Unexpected error message for invalid ticket_id")

    def test_comment_timestamps(self):
        """Test that created_at and updated_at timestamps for comments are set and updated correctly."""

        # Create a comment
        comment_url = f"{self.BASE_URL}/add_comment"
        new_comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }

        response = requests.post(comment_url, json=new_comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a comment")
        comment_id = response.json().get("comment_id")

        # Get the created comment
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params, headers=self.headers)
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
            "ticket_id": self.valid_ticket_id,
            "comment_id":comment_id
        }
        update_data = {
            "comment": "Updated test comment.",
            "posted_by": comment_data["posted_by"]
        }

        update_response = requests.put(update_comment_url, json=update_data, params=params, headers=self.headers)
        self.assertEqual(update_response.status_code, HTTPStatus.OK, "Failed to update the comment")

        # Get the updated comment
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params, headers=self.headers)
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

    def test_get_comment_no_token(self):
        """Test API request without an authentication token."""
        comment_id=1
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }

        response = requests.get(comment_url, params=params) # No headers
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Missing token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Missing Token leads to Unauthorized")

    def test_get_comment_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        comment_id = 1
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }

        headers = {"Authorization": "Bearer corrupted_token"}
        response = requests.get(comment_url, params=params, headers=headers)
        logger.info("Testing API request with corrupted token")
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_get_comment_missing_org_id_in_token(self):
        """Test API request where the token does not have an org_id."""
        comment_id = 1
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }
        token = create_token_without_org_id(org_role=self.ORG_ROLE)  # No org_id
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("Testing API request with missing org_id in token")
        response = requests.get(comment_url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Missing org_id should result in 400 Bad Request")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_get_comment_missing_org_role_in_token(self):
        """Test API request where the token does not have an org_role."""
        comment_id = 1
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        logger.info("Testing API request with missing org_role in token")
        response = requests.get(comment_url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN, "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_get_comment_unauthorized_org_role(self):
        headers={}
        # Assuming an endpoint `/addcustomer` to create a new customer
        data = add_customer("test_org")
        org_id = data.get("org_id")

        # Create Test Token for member (not allowed)
        token = create_test_token(org_id=org_id, org_role="org:random_org_role")
        headers['Authorization'] = f'Bearer {token}'

        comment_id = 1
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }
        response = requests.get(comment_url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_get_comment_invalid_org_id_no_mapped_customer_guid(self):
        """Test API request with an org_id that has no mapped customer_guid."""
        comment_id = 1
        comment_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments/{comment_id}"
        params = {
            "ticket_id": self.valid_ticket_id
        }
        invalid_token = create_test_token(org_id="unmapped_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        logger.info("Testing API request with org_id that has no mapped customer_guid")
        response = requests.get(comment_url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Unmapped org_id should result in 400 Bad Request")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")

    def tearDown(self):
        """Clean up after each test."""
        logger.info(f"=== Test Case {self._testMethodName} Completed ===")
        logger.info("Tear Down Completed")

if __name__ == "__main__":
    unittest.main()

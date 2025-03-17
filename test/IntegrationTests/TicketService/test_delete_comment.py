import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer, create_test_token, create_token_without_org_id, create_token_without_org_role

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestDeleteCommentAPI(unittest.TestCase):
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

        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def delete_comment(self, ticket_id, comment_id):
        """Helper function to delete a comment."""
        url = f"{self.BASE_URL}/delete_comment"
        params = {
            "ticket_id": ticket_id,
            "comment_id": comment_id,
        }
        response = requests.delete(url, params=params, headers=self.headers)
        return response

    def test_delete_comment_success(self):
        """Test deleting a comment successfully."""

        # Add comment
        comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }
        response = requests.post(comment_url, json=comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a comment")
        valid_comment_id = response.json().get("comment_id")

        response = self.delete_comment(self.valid_ticket_id, valid_comment_id)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete the comment")
        self.assertEqual(response.json()["status"], "deleted", "Comment was not deleted successfully")

        page_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments?page={1}&page_size={10}"
        response = requests.get(page_url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected 404 for invalid comment_id")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"No comments found for ticket_id {self.valid_ticket_id}",
                         "Unexpected error message for invalid comment_id")

    def test_delete_comment_not_found(self):
        """Test deleting a non-existent comment should return 404."""

        comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }
        response = requests.post(comment_url, json=comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a comment")
        valid_comment_id = response.json().get("comment_id")

        response = self.delete_comment(self.valid_ticket_id, valid_comment_id)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete the comment")
        self.assertEqual(response.json()["status"], "deleted", "Comment was not deleted successfully")

        response = self.delete_comment(self.valid_ticket_id, valid_comment_id)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete the comment")
        self.assertEqual(response.json()["status"], "deleted", "Comment was not deleted successfully")

    def test_delete_comment_invalid_customer_guid(self):
        """Test deleting a comment with an invalid customer GUID should fail."""
        invalid_token = create_test_token(org_id="invalid_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }
        response = requests.post(comment_url, json=comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a comment")
        valid_comment_id = response.json().get("comment_id")

        url = f"{self.BASE_URL}/delete_comment"
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": valid_comment_id,
        }
        response = requests.delete(url, params=params, headers=headers)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected failure for invalid customer_guid")
        self.assertIn("detail", response.json(), "Expected error detail message")

    def test_delete_comment_invalid_ticket_id(self):
        """Test deleting a comment with an invalid ticket ID should return 404."""
        comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "ticket_id": self.valid_ticket_id,
            "posted_by": "test_user",
            "comment": "This is a test comment"
        }
        response = requests.post(comment_url, json=comment_data, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a comment")
        valid_comment_id = response.json().get("comment_id")

        response = self.delete_comment(self.valid_ticket_id, valid_comment_id)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to delete the comment")
        self.assertEqual(response.json()["status"], "deleted", "Comment was not deleted successfully")

        invalid_ticket_id = 999999  # Assuming this ticket ID does not exist
        response = self.delete_comment(invalid_ticket_id, valid_comment_id)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected 404 for invalid ticket_id")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Invalid Ticket ID. {invalid_ticket_id} does not exist.",
                         "Unexpected error message for invalid ticket_id")

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

    def _delete_comment(self, ticket_id, comment_id):
        """Delete a specific comment for a ticket."""
        logger.info(f"Deleting comment {comment_id} for ticket {ticket_id}.")
        response = requests.delete(
            f"{self.BASE_URL}/delete_comment",
            params={"ticket_id": ticket_id, "comment_id": comment_id},
            headers=self.headers
        )
        if response.status_code != HTTPStatus.OK:
            logger.error(f"Failed to delete comment {comment_id} for ticket {ticket_id}. Server response: {response.text}")
        self.assertEqual(response.status_code, HTTPStatus.OK, f"Failed to delete comment {comment_id}")
        logger.info(f"Successfully deleted comment {comment_id} for ticket {ticket_id}.")

    def test_pagination_and_deletion_for_comments_by_ticket_id(self):
        """Test pagination for comments retrieved by ticket ID, including comment deletion."""
        logger.info("Testing pagination for comments with different page sizes and deletion.")

        # Add 50 comments to a ticket for testing pagination
        self._add_50_comments()

        # Define different page sizes for pagination testing
        page_sizes = [10, 20, 50]

        # List of comment IDs to delete for the test
        comment_ids_to_delete = [5, 10, 15, 25, 30]

        # Delete specific comments
        for comment_id in comment_ids_to_delete:
            self._delete_comment(self.valid_ticket_id, comment_id)

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

            # Ensure deleted comments are not included
            deleted_comment_ids = set(comment_ids_to_delete)
            retrieved_comment_ids = {comment["comment_id"] for comment in all_comments}
            self.assertTrue(deleted_comment_ids.isdisjoint(retrieved_comment_ids),
                            "Deleted comments should not be included in the retrieved comments.")

            logger.info(f"All retrieved comment IDs: {retrieved_comment_ids}")

            # Validate the total number of comments retrieved
            self.assertEqual(
                len(all_comments),
                45,  # 50 - 5 deleted comments
                f"Total comments retrieved with per_page={per_page} should be 45"
            )

            # Validate comment IDs are in reverse order (excluding deleted ones)
            expected_comment_ids = [str(i) for i in range(50, 0, -1) if i not in comment_ids_to_delete]
            retrieved_comment_ids = [str(comment["comment_id"]) for comment in all_comments]

            self.assertEqual(
                expected_comment_ids,
                retrieved_comment_ids,
                "Mismatch in expected and retrieved comment IDs"
            )

            # Test the 'posted_by' field for correct data
            expected_posted_by = [f"user_{i}" for i in range(50, 0, -1) if i not in comment_ids_to_delete]
            retrieved_posted_by = [comment["posted_by"] for comment in all_comments]
            self.assertEqual(expected_posted_by, retrieved_posted_by,
                             "Mismatch in expected and retrieved comment posted_by")

            # Test the 'comment' field for expected content
            expected_comment_texts = [f"This is test comment number {i}" for i in range(50, 0, -1) if i not in comment_ids_to_delete]
            retrieved_comment_texts = [comment["comment"] for comment in all_comments]

            self.assertEqual(
                expected_comment_texts,
                retrieved_comment_texts,
                "Mismatch in expected and retrieved comment texts"
            )

            logger.info(f"Successfully verified comments for per_page={per_page}.")

    def test_delete_comments_no_token(self):
        """Test API request without an authentication token."""
        logger.info("Testing API request without token")
        url = f"{self.BASE_URL}/delete_comment"
        comment_id=1
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": comment_id,
        }
        response = requests.delete(url, params=params) # No headers
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Missing token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Missing Token leads to Unauthorized")

    def test_delete_comments_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        headers = {"Authorization": "Bearer corrupted_token"}
        logger.info("Testing API request with corrupted token")
        url = f"{self.BASE_URL}/delete_comment"
        comment_id = 1
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": comment_id,
        }
        response = requests.delete(url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_delete_comments_missing_org_id_in_token(self):
        """Test API request where the token does not have an org_id."""
        token = create_token_without_org_id(org_role=self.ORG_ROLE)  # No org_id
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("Testing API request with missing org_id in token")
        url = f"{self.BASE_URL}/delete_comment"
        comment_id = 1
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": comment_id,
        }
        response = requests.delete(url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Missing org_id should result in 400 Bad Request")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_delete_comments_missing_org_role_in_token(self):
        """Test API request where the token does not have an org_role."""
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        logger.info("Testing API request with missing org_role in token")
        url = f"{self.BASE_URL}/delete_comment"
        comment_id = 1
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": comment_id,
        }
        response = requests.delete(url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN, "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_delete_comments_unauthorized_org_role(self):
        headers={}
        # Assuming an endpoint `/addcustomer` to create a new customer
        data = add_customer("test_org")
        org_id = data.get("org_id")

        # Create Test Token for member (not allowed)
        token = create_test_token(org_id=org_id, org_role="org:random_org_role")
        headers['Authorization'] = f'Bearer {token}'
        url = f"{self.BASE_URL}/delete_comment"
        comment_id = 1
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": comment_id,
        }
        response = requests.delete(url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_delete_comments_invalid_org_id_no_mapped_customer_guid(self):
        """Test API request with an org_id that has no mapped customer_guid."""
        invalid_token = create_test_token(org_id="unmapped_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        logger.info("Testing API request with org_id that has no mapped customer_guid")
        url = f"{self.BASE_URL}/delete_comment"
        comment_id = 1
        params = {
            "ticket_id": self.valid_ticket_id,
            "comment_id": comment_id,
        }
        response = requests.delete(url, params=params, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Unmapped org_id should result in 400 Bad Request")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")

    def tearDown(self):
        """Clean up resources after tests."""
        logger.info(f"=== Test Case {self._testMethodName} Completed ===")

if __name__ == "__main__":
    unittest.main()

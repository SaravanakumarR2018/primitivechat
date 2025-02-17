import os
import sys

import requests
import logging
from http import HTTPStatus
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.backend.utils.api_utils import add_customer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestGetCommentsByTicketId(unittest.TestCase):
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        """Setup before each test."""
        logger.info("=== Setting up test environment ===")

        # Create a valid customer
        self.valid_customer_guid = add_customer("test_org_123").get("customer_guid")

        # Create a valid chat
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "How can I reset my password?"
        }
        response = requests.post(chat_url, json=chat_data)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create a chat")
        self.valid_chat_id = response.json().get("chat_id")

        # Create a valid ticket
        ticket_url = f"{self.BASE_URL}/tickets"
        ticket_data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "title":"This is title",
            "description": "Issue with login",
            "priority": "High",
            "reported_by":"user@email.com",
            "assigned":"user@email.com"
        }
        response = requests.post(ticket_url, json=ticket_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Failed to create a ticket")
        self.valid_ticket_id = response.json().get("ticket_id")

        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def test_get_paginated_comments_for_invalid_ticket_id(self):
        """Test retrieving paginated comments with an invalid ticket ID."""
        add_comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = {
            "customer_guid": self.valid_customer_guid,
            "ticket_id": self.valid_ticket_id,
            "posted_by": "user@email.com",
            "comment": "This is a test comment."
        }
        response = requests.post(add_comment_url, json=comment_data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Expected 201 Created for valid comment")
        response_data = response.json()
        self.assertEqual(response_data["ticket_id"], self.valid_ticket_id, "Ticket ID mismatch")
        self.assertEqual(response_data["posted_by"], "user@email.com", "Posted by mismatch")
        self.assertEqual(response_data["comment"], "This is a test comment.", "Comment content mismatch")

        invalid_ticket_id = "invalid_ticket_id"
        response = requests.get(
            f"{self.BASE_URL}/tickets/{invalid_ticket_id}/comments",
            params={
                "customer_guid": self.valid_customer_guid,
                "page": 1,
                "page_size": 10
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Expected 400 BAD REQUEST for invalid ticket ID")
        self.assertEqual(response.json(), {
            "detail": f"No comments found for ticket_id {invalid_ticket_id}"
        })

    def test_get_paginated_comments_by_ticket_id_success(self):
        """Test retrieving paginated comments by valid ticket ID."""
        # Create some comments for the ticket
        comment_url = f"{self.BASE_URL}/add_comment"
        comment_data = [
            {
                "customer_guid": self.valid_customer_guid,
                "ticket_id": self.valid_ticket_id,
                "posted_by": "user@email.com",
                "comment": "This is a test comment.1"
            },
            {
                "customer_guid": self.valid_customer_guid,
                "ticket_id": self.valid_ticket_id,
                "posted_by": "user@email.com",
                "comment": "This is a test comment.2"
            },
            {
                "customer_guid": self.valid_customer_guid,
                "ticket_id": self.valid_ticket_id,
                "posted_by": "user@email.com",
                "comment": "This is a test comment.3"
            },
            {
                "customer_guid": self.valid_customer_guid,
                "ticket_id": self.valid_ticket_id,
                "posted_by": "user@email.com",
                "comment": "This is a test comment.4"
            },
        ]
        # Post the comments
        for data in comment_data:
            response = requests.post(comment_url, json=data)
            self.assertEqual(response.status_code, HTTPStatus.CREATED, f"Failed to create comment: {data['comment']}")

        # Retrieve paginated comments for the ticket
        response = requests.get(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments",
            params={
                "customer_guid": self.valid_customer_guid,
                "page": 1,
                "page_size": 2  # Set page size to 2 for pagination
            }
        )

        # Validate the response status
        self.assertEqual(response.status_code, HTTPStatus.OK,
                         "Expected 200 OK for valid ticket ID and paginated comments")

        # Parse the response JSON
        comments = response.json()

        # Validate the response format and content
        self.assertTrue(isinstance(comments, list), "Expected a list of comments")
        self.assertEqual(len(comments), 2, "Expected 2 comments on page 1")

        # Check each comment, adjusting for reverse chronological order
        for i, comment_response in enumerate(comments):
            # Compare against the correct comment text from the comment_data based on reverse order
            expected_comment = comment_data[3 - i]["comment"]  # Reverse order of the original comment data
            self.assertEqual(comment_response["ticket_id"], str(self.valid_ticket_id), "Incorrect ticket_id")
            self.assertEqual(comment_response["comment"], expected_comment,
                             f"Incorrect comment text for comment {i + 1}")
            self.assertEqual(comment_response["posted_by"], "user@email.com",
                             f"Incorrect posted_by for comment {i + 1}")
            self.assertIn("created_at", comment_response, f"Missing 'created_at' timestamp for comment {i + 1}")
            self.assertIn("updated_at", comment_response, f"Missing 'updated_at' timestamp for comment {i + 1}")
            self.assertIn("comment_id", comment_response, f"Missing 'comment_id' for comment {i + 1}")

    def test_get_comment_wrong_customer_guid(self):
        """Test getting a comment with an invalid customer GUID."""
        invalid_customer_guid = "a39a3076-f45f-4bb1-9945-700330b5e541"  # Invalid GUID
        response = requests.get(
            f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments",
            params={
                "customer_guid": invalid_customer_guid,
                "page": 1,
                "page_size": 2  # Set page size to 2 for pagination
            }
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Expected 400 for invalid customer_guid")

        error_detail = response.json().get("detail")
        self.assertEqual(error_detail, f"Database customer_{invalid_customer_guid} does not exist",
                         "Unexpected error message for invalid customer_guid")

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
            self.assertEqual(expected_posted_by, retrieved_posted_by,
                             "Mismatch in expected and retrieved comment posted_by")

            # Test the 'comment' field for expected content
            expected_comment_texts = [f"This is test comment number {i}" for i in range(50, 0, -1)]
            retrieved_comment_texts = [comment["comment"] for comment in all_comments]

            self.assertEqual(
                expected_comment_texts,
                retrieved_comment_texts,
                "Mismatch in expected and retrieved comment texts"
            )

    def test_pagination_for_comments_with_large_page_size(self):
        """Test pagination when page size exceeds the number of available comments."""
        logger.info("Testing pagination for comments with page size greater than the total number of comments.")

        # Add 50 comments to the ticket for testing pagination
        self._add_50_comments()

        # Set a page size greater than the total number of comments
        large_page_size = 100  # A page size larger than the total number of comments

        # Fetch the first page of comments
        page_num = 1
        page_url = f"{self.BASE_URL}/tickets/{self.valid_ticket_id}/comments?customer_guid={self.valid_customer_guid}&page={page_num}&page_size={large_page_size}"
        response = requests.get(page_url)

        # Validate the response status
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            f"Failed to fetch page {page_num} with page_size={large_page_size}"
        )

        # Parse the response JSON
        page_data = response.json()

        # Validate the total number of comments retrieved
        self.assertEqual(
            len(page_data),
            50,  # Since we only have 50 comments, the page should contain exactly 50 comments
            f"Total comments retrieved should be 50 when page_size={large_page_size}"
        )

        # Check that all comments are retrieved in the correct order
        created_at_list = [comment["created_at"] for comment in page_data]
        self.assertTrue(
            all(created_at_list[i] >= created_at_list[i + 1] for i in range(len(created_at_list) - 1)),
            "Comments are not sorted by created_at in descending order"
        )

        # Validate that comment IDs are in reverse order
        expected_comment_ids = [str(i) for i in range(50, 0, -1)]
        retrieved_comment_ids = [comment["comment_id"] for comment in page_data]
        self.assertEqual(
            expected_comment_ids,
            retrieved_comment_ids,
            "Mismatch in expected and retrieved comment IDs"
        )

        # Test the 'posted_by' field for correct data
        expected_posted_by = [f"user_{i}" for i in range(50, 0, -1)]
        retrieved_posted_by = [comment["posted_by"] for comment in page_data]
        self.assertEqual(expected_posted_by, retrieved_posted_by,
                         "Mismatch in expected and retrieved comment posted_by")

        # Test the 'comment' field for expected content
        expected_comment_texts = [f"This is test comment number {i}" for i in range(50, 0, -1)]
        retrieved_comment_texts = [comment["comment"] for comment in page_data]

        self.assertEqual(
            expected_comment_texts,
            retrieved_comment_texts,
            "Mismatch in expected and retrieved comment texts"
        )

        logger.info(f"Test passed for page_size={large_page_size}, with only 50 comments returned as expected.")

    def _delete_comment(self, ticket_id, comment_id):
        """Delete a specific comment for a ticket."""
        logger.info(f"Deleting comment {comment_id} for ticket {ticket_id}.")
        response = requests.delete(
            f"{self.BASE_URL}/delete_comment",
            params={"ticket_id": ticket_id, "comment_id": comment_id, "customer_guid": self.valid_customer_guid}
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
            retrieved_comment_ids = [comment["comment_id"] for comment in all_comments]

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

    def tearDown(self):
        """Cleanup after each test."""
        logger.info(f"=== Test {self._testMethodName} completed and passed ===")
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

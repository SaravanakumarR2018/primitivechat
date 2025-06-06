import logging
import os
import unittest

import requests

from src.backend.lib.logging_config import get_primitivechat_logger
from utils.api_utils import add_customer,create_test_token, create_token_without_org_role, create_token_without_org_id

# Set up logging configuration
logger = get_primitivechat_logger(__name__)

# Constants
TEST_ORG = "test_org"
ORG_ADMIN_ROLE = "org:admin"

class TestDeleteChatAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"  # Update this to your actual API base URL

    def setUp(self):
        """Setup function to create valid customer_guid"""
        logger.info("=== Starting setUp process ===")

        # Get valid customer_guid
        customer_data = add_customer("test_org")
        self.valid_customer_guid = customer_data["customer_guid"]
        self.org_id = customer_data.get("org_id")
        logger.info(f"OUTPUT: Received valid customer_guid: {self.valid_customer_guid}")

        # Create a test token for authentication
        self.token = create_test_token(org_id=self.org_id, org_role=ORG_ADMIN_ROLE)
        self.headers = {'Authorization': f'Bearer {self.token}'}
        logger.info(f"=== Test Case {self._testMethodName} Started ===")

    def create_chat(self):
        """Helper method to create a new chat and return the chat_id"""
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "question": "who is modi?"
        }
        logger.info(f"INPUT: Creating initial chat with data: {str(chat_data)}")

        chat_response = requests.post(chat_url, json=chat_data, headers=self.headers)
        logger.info(f"OUTPUT: Chat creation response status: {chat_response.status_code}")

        self.assertEqual(chat_response.status_code, 200)
        chat_data = chat_response.json()
        local_chat_id = chat_data["chat_id"]
        logger.info(f"OUTPUT: Received valid chat_id: {local_chat_id}")
        return local_chat_id  # Return the chat_id for use in tests

    def test_valid_customer_guid_and_valid_chat_id(self):
        """Test case 1: Valid customer_guid and valid chat_id"""
        logger.info("=== Starting Test Case 1: Valid customer_guid and valid chat_id ===")

        # Create a new chat for this test case
        local_chat_id = self.create_chat()

        # Step 2: Add some chat messages
        add_chat_url = f"{self.BASE_URL}/chat"
        messages_to_add = [
            "Message 1: Can you provide an update?",
            "Message 2: How do I contact support?",
            "Message 3: Can I change my order?"
        ]

        logger.info(f"Adding messages to chat_id: {local_chat_id}")
        for idx, message in enumerate(messages_to_add, start=1):
            message_data = {
                "chat_id": local_chat_id,
                "question": message
            }
            response = requests.post(add_chat_url, json=message_data, headers=self.headers)
            logger.info(f"Add Message #{idx}: Response: {response.status_code}, {response.text}")
            self.assertEqual(response.status_code, 200, f"Failed to add message #{idx}")

        logger.info("=== All messages added successfully ===")

        # Step 3: Retrieve chats using GET request
        get_chats_url = f"{self.BASE_URL}/getallchats"  # Define the URL here
        url = f"{get_chats_url}?chat_id={local_chat_id}&page=1&page_size=10"
        logger.info(f"INPUT: Sending request to: {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")
        self.assertEqual(response.status_code, 200, "Failed to retrieve chats using GET.")

        messages_get = response.json().get("messages", [])
        self.assertGreater(len(messages_get), 0, "Expected to find messages in the chat using GET.")

        # Step 4: Delete the chat
        delete_chat_url = f"{self.BASE_URL}/deletechat"
        delete_data = {
            "chat_id": local_chat_id
        }
        logger.info(f"Deleting chat with data: {delete_data}")
        response = requests.post(delete_chat_url, json=delete_data, headers=self.headers)
        logger.info(f"Delete Chat Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 200, "Failed to delete the chat.")

        # Verify that the response body contains the expected success message
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertEqual(response_data["message"], "Chat deleted successfully", "Unexpected message in response.")

        # Step 5: Verify that the chat has been deleted
        logger.info("Verifying that the chat has been deleted.")
        # Use the same URL for retrieving chats after deletion
        response = requests.get(url, headers=self.headers)  # Use the same URL constructed earlier
        logger.info(f"Retrieving chats after deletion: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 404, "Failed to retrieve chats after deletion.")

        messages_after_deletion = response.json().get("messages", [])
        self.assertEqual(len(messages_after_deletion), 0, "Expected no messages in the chat after deletion.")

        logger.info("=== Test Case 1 Completed ===\n")

    def test_valid_customer_guid_and_empty_chat_id(self):
        """Test case 2: Valid customer_guid and empty chat_id"""
        logger.info("=== Starting Test Case 2: Valid customer_guid and empty chat_id ===")

        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": ""
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=self.headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Verify that the response status code is 200
        self.assertEqual(response.status_code, 200)  # Expecting 200 based on API behavior

        # Verify that the response body contains the expected success message
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertEqual(response_data["message"], "Chat deleted successfully", "Unexpected message in response.")

        logger.info("=== Test Case 2 Completed ===\n")

    def test_customer_guid_value_missing_and_correct_chat_id(self):
        """Test case 3: customer_guid value missing and correct chat_id"""
        logger.info("=== Starting Test Case 3: customer_guid value missing and correct chat_id ===")

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": local_chat_id
        }
        logger.info(f"INPUT : Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 401)
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Authentication required")
        logger.info("=== Test Case 3 Completed ===\n")

    def test_correct_customer_guid_and_missing_chat_id(self):
        """Test case 4: correct customer_guid and missing chat_id"""
        logger.info("=== Starting Test Case 4: correct customer_guid and missing chat_id ===")

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
        }
        logger.info(f"INPUT : Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=self.headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 422)
        self.assertIn("field required", response.text.lower())
        logger.info("=== Test Case 4 Completed ===\n")

    def test_empty_customer_guid_and_empty_chat_id(self):
        """Test case 5: Empty customer_guid and empty chat_id"""
        logger.info("=== Starting Test Case 5: Empty customer_guid and empty chat_id ===")

        url = f"{self.BASE_URL}/deletechat"
        data = {}
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=self.headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 422)  # Expecting 422 for missing fields
        self.assertIn("field required",
                      response.text.lower())  # Check that the response indicates required fields are missing

        logger.info("=== Test Case 5 Completed ===\n")

    def test_duplicate_deletion(self):
        """Test case 6: Duplicate Deletion with valid customer_guid and valid chat_id"""
        logger.info("=== Starting Test Case 6: Duplicate Deletion ===")

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": local_chat_id
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        # First deletion
        response = requests.post(url, json=data, headers=self.headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 200)  # Expecting 200 based on API behavior

        # Second deletion attempt
        response = requests.post(url, json=data, headers=self.headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 200)  # Expecting 200 based on API behavior
        logger.info("=== Test Case 6 Completed ===\n")

    def test_wrong_customer_guid_and_wrong_chat_id(self):
        """Test case 7: Invalid customer_guid and chat_id"""
        logger.info("=== Starting Test Case 7: Wrong customer_guid and wrong chat_id ===")

        # Simulate a token with an invalid or missing customer_guid
        invalid_token = create_test_token(org_id="invalid_org_id", org_role="org:admin")
        headers = {'Authorization': f'Bearer {invalid_token}'}

        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": "invalid_chat_id"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 404)
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Invalid customer_guid provided")

        logger.info("=== Test Case 7 Completed ===\n")

    def test_correct_customer_guid_wrong_chat_id(self):
        """Test case 8: Valid customer_guid but invalid chat_id"""
        logger.info("=== Starting Test Case 8: Correct customer_guid and wrong chat_id ===")

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": "invalid_chat_id"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=self.headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("chat deleted successfully", response.text.lower())
        logger.info("=== Test Case 8 Completed ===\n")

    def test_wrong_customer_guid_correct_chat_id(self):
        """Test case 9: InValid customer_guid but valid chat_id"""
        logger.info("=== Starting Test Case 9: Correct customer_guid and wrong chat_id ===")

        # Simulate a token with an invalid or missing customer_guid
        invalid_token = create_test_token(org_id="invalid_org_id", org_role="org:admin")
        headers = {'Authorization': f'Bearer {invalid_token}'}

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": local_chat_id
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 404)
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Invalid customer_guid provided")
        logger.info("=== Test Case 9 Completed ===\n")
        
    def test_delete_chat_without_token(self):
        logger.info("Executing delete_chat_without_token: Testing error handling for missing token")

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": local_chat_id
        }
        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 401)
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Authentication required")
        logger.info("=== Test Case 10 Completed ===\n")

    def test_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        headers = {"Authorization": "Bearer corrupted_token"}
        local_chat_id = self.create_chat()
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": local_chat_id
        }
        response = requests.post(url, json=data, headers=headers)
        self.assertEqual(response.status_code, 401, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")
        logger.info("=== Test Case 11 Completed ===\n")

    def test_delete_chat_token_without_org_role(self):
        logger.info("Testing deletechat API with a token missing org_role")

        headers = {'Authorization': f'Bearer {create_token_without_org_role(self.org_id)}'}
        local_chat_id = self.create_chat()
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": local_chat_id
        }
        response = requests.post(url, json=data, headers=headers)

        self.assertEqual(response.status_code, 403, "Expected status code 403 for missing org_role")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

        logger.info("=== Test Case 12 Completed ===\n")

    def test_delete_chat_token_without_org_id(self):
        logger.info("Testing deletechat API with a token missing org_id")

        headers = {'Authorization': f'Bearer {create_token_without_org_id(ORG_ADMIN_ROLE)}'}
        local_chat_id = self.create_chat()
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": local_chat_id
        }
        response = requests.post(url, json=data, headers=headers)

        # Expect 400 Bad Request
        self.assertEqual(response.status_code, 400, "Expected status code 400 for missing org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

        logger.info("=== Test Case 13 Completed ===\n")

    def test_delete_chat_no_mapping_customer_guid(self):
        logger.info("Testing chat API with no mapping between org_id and customer_guid")

        # Create a new org_id without mapping it to a customer_guid
        org_id = "unmapped_org_id"
        token = create_test_token(org_id=org_id, org_role=ORG_ADMIN_ROLE)
        headers = {'Authorization': f'Bearer {token}'}
        local_chat_id = self.create_chat()

        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": local_chat_id
        }
        response = requests.post(url, json=data, headers=headers)

        self.assertEqual(response.status_code, 404, "Expected status code 404 for unmapped org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided", "Unexpected error message")

        logger.info("=== Test Case 14 Completed ===\n")

if __name__ == "__main__":
    unittest.main()

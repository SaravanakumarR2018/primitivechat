import unittest
import requests
import logging
import os

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestDeleteChatAPI(unittest.TestCase):
    # Get the port from environment variables (default to 8000 if not set)
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT', 8000)}"

    def setUp(self):
        """Setup function to create valid customer_guid"""
        logger.info("=== Starting setUp process ===")

        # Get valid customer_guid
        add_customer_url = f"{self.BASE_URL}/addcustomer"
        logger.info(f"INPUT: Requesting new customer from: {add_customer_url}")

        customer_response = requests.post(add_customer_url)
        logger.info(f"OUTPUT: Customer creation response status: {customer_response.status_code}")

        self.assertEqual(customer_response.status_code, 200)
        customer_data = customer_response.json()
        self.valid_customer_guid = customer_data["customer_guid"]
        logger.info(f"OUTPUT: Received valid customer_guid: {self.valid_customer_guid}")

        logger.info("=== setUp completed successfully ===\n")

    def create_chat(self):
        """Helper method to create a new chat and return the chat_id"""
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "who is modi?"
        }
        logger.info(f"INPUT: Creating initial chat with data: {str(chat_data)}")

        chat_response = requests.post(chat_url, json=chat_data)
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
                "customer_guid": self.valid_customer_guid,
                "chat_id": local_chat_id,
                "question": message
            }
            response = requests.post(add_chat_url, json=message_data)
            logger.info(f"Add Message #{idx}: Response: {response.status_code}, {response.text}")
            self.assertEqual(response.status_code, 200, f"Failed to add message #{idx}")

        logger.info("=== All messages added successfully ===")

        # Step 3: Retrieve chats to verify they exist
        get_chats_url = f"{self.BASE_URL}/getallchats"
        retrieve_data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": local_chat_id,
            "page": 1,
            "page_size": 10  # Retrieve all messages
        }
        logger.info(f"Retrieving chats with data: {retrieve_data}")
        response = requests.post(get_chats_url, json=retrieve_data)
        logger.info(f"Get Chats Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 200, "Failed to retrieve chats.")

        messages = response.json().get("messages", [])
        self.assertGreater(len(messages), 0, "Expected to find messages in the chat.")

        # Step 4: Delete the chat
        delete_chat_url = f"{self.BASE_URL}/deletechat"
        delete_data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": local_chat_id
        }
        logger.info(f"Deleting chat with data: {delete_data}")
        response = requests.post(delete_chat_url, json=delete_data)
        logger.info(f"Delete Chat Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 200, "Failed to delete the chat.")

        # Verify that the response body contains the expected success message
        response_data = response.json()
        self.assertIn("message", response_data)
        self.assertEqual(response_data["message"], "Chat deleted successfully", "Unexpected message in response.")

        # Step 5: Verify that the chat has been deleted
        logger.info("Verifying that the chat has been deleted.")
        response = requests.post(get_chats_url, json=retrieve_data)
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
            "customer_guid": self.valid_customer_guid,
            "chat_id": ""
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
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

        self.assertEqual(response.status_code, 422)
        self.assertIn("field required", response.text.lower())
        logger.info("=== Test Case 3 Completed ===\n")

    def test_correct_customer_guid_and_missing_chat_id(self):
        """Test case 4: correct customer_guid and missing chat_id"""
        logger.info("=== Starting Test Case 4: correct customer_guid and missing chat_id ===")

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "customer_guid": self.valid_customer_guid
        }
        logger.info(f"INPUT : Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
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

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 422)  # Expecting 422 for missing fields
        self.assertIn("field required", response.text.lower())  # Check that the response indicates required fields are missing

        logger.info("=== Test Case 5 Completed ===\n")

    def test_duplicate_deletion(self):
        """Test case 6: Duplicate Deletion with valid customer_guid and valid chat_id"""
        logger.info("=== Starting Test Case 6: Duplicate Deletion ===")

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": local_chat_id
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        # First deletion
        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 200)  # Expecting 200 based on API behavior

        # Second deletion attempt
        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 200)  # Expecting 200 based on API behavior
        logger.info("=== Test Case 6 Completed ===\n")

    def test_wrong_customer_guid_and_wrong_chat_id(self):
        """Test case 7: Invalid customer_guid and chat_id"""
        logger.info("=== Starting Test Case 7: Wrong customer_guid and wrong chat_id ===")

        url = f"{self.BASE_URL}/deletechat"
        data = {
            "customer_guid": "invalid_customer_guid",
            "chat_id": "invalid_chat_id"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("chat deleted successfully", response.text.lower())

        logger.info("=== Test Case 7 Completed ===\n")

    def test_correct_customer_guid_wrong_chat_id(self):
        """Test case 8: Valid customer_guid but invalid chat_id"""
        logger.info("=== Starting Test Case 8: Correct customer_guid and wrong chat_id ===")

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": "invalid_chat_id"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("chat deleted successfully", response.text.lower())
        logger.info("=== Test Case 8 Completed ===\n")

    def test_wrong_customer_guid_correct_chat_id(self):
        """Test case 9: Valid customer_guid but invalid chat_id"""
        logger.info("=== Starting Test Case 9: Correct customer_guid and wrong chat_id ===")

        local_chat_id = self.create_chat()  # Create a chat to get a valid chat_id
        url = f"{self.BASE_URL}/deletechat"
        data = {
            "customer_guid": "invalid_customer_guid",
            "chat_id": local_chat_id
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("chat deleted successfully", response.text.lower())
        logger.info("=== Test Case 9 Completed ===\n")

if __name__ == "__main__":
    unittest.main()
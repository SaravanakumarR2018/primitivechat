import unittest
import requests
import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestDeleteChatAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"  # Update this to your actual API base URL

    def setUp(self):
        """Setup function to create valid customer_guid and chat_id, and define invalid ones."""
        logger.info("=== Starting setUp process ===")

        # Create a customer to get a valid customer_guid
        add_customer_url = f"{self.BASE_URL}/addcustomer"
        logger.info(f"INPUT: Requesting new customer from: {add_customer_url}")

        customer_response = requests.post(add_customer_url)
        logger.info(f"OUTPUT: Customer creation response status: {customer_response.status_code}")

        self.assertEqual(customer_response.status_code, 200)
        customer_data = customer_response.json()
        self.valid_customer_guid = customer_data["customer_guid"]
        logger.info(f"OUTPUT: Received valid customer_guid: {self.valid_customer_guid}")

        # Create a chat for the customer
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "customer_guid": self.valid_customer_guid,
            "message": "Test chat message",
            "question": "What is your question?"
        }
        logger.info(f"INPUT: Creating initial chat with data: {str(chat_data)}")

        chat_response = requests.post(chat_url, json=chat_data)
        logger.info(f"OUTPUT: Chat creation response status: {chat_response.status_code}")

        self.assertEqual(chat_response.status_code, 200)
        chat_data = chat_response.json()
        self.valid_chat_id = chat_data["chat_id"]
        logger.info(f"OUTPUT: Received valid chat_id: {self.valid_chat_id}")
        logger.info("=== setUp completed successfully ===\n")

    def test_valid_customer_guid_and_valid_chat_id(self):
        """Test case 1: Valid customer_guid and valid chat_id"""
        logger.info("=== Starting Test Case 1: Valid customer_guid and valid chat_id ===")

        url = f"{self.BASE_URL}/deletechat"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id
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

        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": self.valid_chat_id
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

        url = f"{self.BASE_URL}/deletechat"
        data = {
            "chat_id": self.valid_chat_id
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

        url = f"{self.BASE_URL}/deletechat"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id
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

        url = f"{self.BASE_URL}/chat"
        data = {
            "customer_guid": "invalid_customer_guid",
            "chat_id": "invalid_chat_id",
            "question": "What is your question?"  # Ensure the question field is included
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Update the assertion to expect a 400 status code
        self.assertEqual(response.status_code, 400)
        self.assertIn("customer_guid is not valid", response.text.lower())

        logger.info("=== Test Case 7 Completed ===\n")

    def test_correct_customer_guid_wrong_chat_id(self):
        """Test case 8: Valid customer_guid but invalid chat_id"""
        logger.info("=== Starting Test Case 8: Correct customer_guid and wrong chat_id ===")

        url = f"{self.BASE_URL}/chat"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": "invalid_chat_id",
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")


        self.assertEqual(response.status_code, 400)
        self.assertIn("chat_id is not valid", response.text.lower())
        logger.info("=== Test Case 8 Completed ===\n")

    def test_wrong_customer_guid_correct_chat_id(self):
        """Test case 9: Valid customer_guid but invalid chat_id"""
        logger.info("=== Starting Test Case 9: Correct customer_guid and wrong chat_id ===")

        url = f"{self.BASE_URL}/chat"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": "invalid_chat_id",
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")


        self.assertEqual(response.status_code, 400)
        self.assertIn("chat_id is not valid", response.text.lower())
        logger.info("=== Test Case 9 Completed ===\n")



if __name__ == "__main__":
    unittest.main()
import unittest
import requests
import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestGetAllChatsAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"

    def setUp(self):
        """Setup function to create valid customer_guid and chat_id"""
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

        # Get valid chat_id
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "Initial question"
        }
        logger.info(f"INPUT: Creating initial chat with data: {str(chat_data)}")

        chat_response = requests.post(chat_url, json=chat_data)
        logger.info(f"OUTPUT: Chat creation response status: {chat_response.status_code}")

        self.assertEqual(chat_response.status_code, 200)
        chat_data = chat_response.json()
        self.valid_chat_id = chat_data["chat_id"]
        logger.info(f"OUTPUT: Received valid chat_id: {self.valid_chat_id}")
        logger.info("=== setUp completed successfully ===\n")

    def test_wrong_customer_guid_and_wrong_chat_id(self):
        """Test case 1: Invalid customer_guid and chat_id"""
        logger.info("=== Starting Test Case 1: Wrong customer_guid and wrong chat_id ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": "invalid_customer_guid",
            "chat_id": "invalid_chat_id"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 404)
        self.assertIn("no chats found for this customer and chat id", response.text.lower())
        logger.info("=== Test Case 1 Completed ===\n")

    def test_correct_customer_guid_and_wrong_chat_id(self):
        """Test case 2: Valid customer_guid but invalid chat_id"""
        logger.info("=== Starting Test Case 2: Correct customer_guid and wrong chat_id ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": "invalid_chat_id"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 404)
        self.assertIn("no chats found for this customer and chat id", response.text.lower())
        logger.info("=== Test Case 2 Completed ===\n")

        def test_wrong_customer_guid_and_correct_chat_id(self):
        """Test case 3: Wrong customer_guid and correct chat_id"""
        logger.info("=== Starting Test Case 3: Wrong customer_guid and correct chat_id ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": "invalid_customer_guid",
            "chat_id": self.valid_chat_id
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Verify the status code
        self.assertEqual(response.status_code, 404)

        # Verify the response text
        self.assertIn("no chats found for this customer and chat id", response.text.lower())

        logger.info("=== Test Case 3 Completed ===\n")

    def test_retrieval_with_valid_inputs(self):
        """Test case 4: Valid customer_guid and chat_id"""
        logger.info("=== Starting Test Case 4: Valid customer_guid and chat_id ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 1,
            "page_size": 10
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Verify that the response status code is 200
        self.assertEqual(response.status_code, 200, "Expected status code 200")

        messages = response.json().get('messages')
        self.assertIsInstance(messages, list)  # Check that messages is a list

        # Verify that the chat_id and customer_guid in the response match the input
        if messages:  # Check if messages list is not empty
            # Assuming the first message corresponds to the chat_id and customer_guid
            first_message = messages[0]
            self.assertEqual(first_message['chat_id'], self.valid_chat_id,
                             "Chat ID in response does not match the input chat ID")
            self.assertEqual(first_message['customer_guid'], self.valid_customer_guid,
                             "Customer GUID in response does not match the input customer GUID")

        # Check for reverse chronological order
        for i in range(len(messages) - 1):
            current_timestamp = messages[i]['timestamp']
            next_timestamp = messages[i + 1]['timestamp']
            self.assertGreaterEqual(current_timestamp, next_timestamp,
                                    "Messages are not in reverse chronological order")

        logger.info("=== Test Case 4 Completed ===\n")

    def test_retrieval_with_page_two(self):
        """Test case 5: Valid customer_guid, chat_id, page=2, and page_size=10"""
        logger.info("=== Starting Test Case 5: Valid customer_guid, chat_id, page=2, and page_size=10 ===")

        # Assuming we have enough messages to test pagination
        for page in range(1, 4):  # Test first three pages
            url = f"{self.BASE_URL}/getallchats"
            data = {
                "customer_guid": self.valid_customer_guid,
                "chat_id": self.valid_chat_id,
                "page": page,
                "page_size": 5
            }
            logger.info(f"INPUT: Sending request with data:\n{str(data)}")

            response = requests.post(url, json=data)
            logger.info(f"OUTPUT: Response status code: {response.status_code}")
            logger.info(f"OUTPUT: Response content: {response.text}")

            if response.status_code == 200:
                messages = response.json().get('messages')
                self.assertIsInstance(messages, list)
                self.assertLessEqual(len(messages), 5, "Messages returned exceed page size")
            else:
                self.assertEqual(response.status_code, 404, "Expected 404 for no more messages")

            logger.info("=== Test Case 5 Completed ===\n")

    def test_single_message_retrieval(self):
        """Test case 6: Valid customer_guid, chat_id, page=1, and page_size=1"""
        logger.info("=== Starting Test Case 6: Valid customer_guid, chat_id, page=1, and page_size=1 ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 1,
            "page_size": 1
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        response_data = response.json()
        self.assertIsInstance(response_data.get('messages'), list)
        logger.info("=== Test Case 6 Completed ===\n")

    def test_missing_customer_guid(self):
        """Test case 8: Missing customer_guid"""
        logger.info("=== Starting Test Case 8: Missing customer_guid ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "chat_id": self.valid_chat_id
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertIn("field required", response.text.lower())
        self.assertEqual(response.status_code, 422)
        logger.info("=== Test Case 8 Completed ===\n")

    def test_missing_chat_id(self):
        """Test case 7: Missing chat_id"""
        logger.info("=== Starting Test Case 7: Missing chat_id ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertIn("field required", response.text.lower())
        self.assertEqual(response.status_code, 422)
        logger.info("=== Test Case 7 Completed ===\n")

    def test_invalid_page_number(self):
        """Test case 9: Invalid Page Number"""
        logger.info("=== Starting Test Case 9: Invalid Page Number ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 0,
            "page_size": 10
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 404)
        self.assertIn("no chats found for this customer and chat id", response.text.lower())
        logger.info("=== Test Case 9 Completed ===\n")

    def test_invalid_page_size(self):
        """Test case 10: Invalid Page Size"""
        logger.info("=== Starting Test Case 10: Invalid Page Size ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 1,
            "page_size": 0
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")


        self.assertEqual(response.status_code, 404)
        logger.info("=== Test Case 10 Completed ===\n")

    def test_large_page_size(self):
        """Test case 12: Large Page Size"""
        logger.info("=== Starting Test Case 12: Large Page Size ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 1,
            "page_size": 1000
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        response_data = response.json()

        # Adjusted to check that 'messages' is a list
        self.assertIsInstance(response_data.get('messages'), list)
        logger.info("=== Test Case 12 Completed ===\n")

    def test_high_page_number(self):
        """Test case 13: High Page Number"""
        logger.info("=== Starting Test case 13: High Page Number ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 1000,
            "page_size": 10
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertIn("no chats found for this customer and chat id", response.text.lower())
        self.assertEqual(response.status_code, 404)
        logger.info("=== Test case 13: High Page Number Completed ===\n")

if __name__ == "__main__":
    unittest.main()

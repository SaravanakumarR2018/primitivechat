import unittest
import requests
import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestChatAPI(unittest.TestCase):
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

        url = f"{self.BASE_URL}/chat"
        data = {
            "customer_guid": "invalid_customer_guid",
            "chat_id": "invalid_chat_id",
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")


        self.assertEqual(response.status_code, 400)
        self.assertIn("customer_guid is not valid", response.text.lower())
        logger.info("=== Test Case 1 Completed ===\n")

    def test_correct_customer_guid_wrong_chat_id(self):
        """Test case 2: Valid customer_guid but invalid chat_id"""
        logger.info("=== Starting Test Case 2: Correct customer_guid and wrong chat_id ===")

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
        logger.info("=== Test Case 2 Completed ===\n")

    def test_correct_customer_guid_without_chat_id(self):
        """Test case 3: Valid customer_guid without chat_id"""
        logger.info("=== Starting Test Case 3: Correct customer_guid without chat_id ===")

        url = f"{self.BASE_URL}/chat"
        data = {
            "customer_guid": self.valid_customer_guid,
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Verify the response status code
        self.assertEqual(response.status_code, 200)

        # Parse the response JSON
        response_data = response.json()

        # Verify that the response contains a chat_id field with a value
        self.assertIn("chat_id", response_data)
        self.assertIsNotNone(response_data["chat_id"])
        self.assertNotEqual(response_data["chat_id"], "")  # Ensure chat_id is not an empty string

        # Verify that the customer_guid in the response matches the one sent in the request
        self.assertEqual(response_data["customer_guid"], self.valid_customer_guid)

        # Verify that the response contains an answer field with a value
        self.assertIn("answer", response_data)
        self.assertIsNotNone(response_data["answer"])
        self.assertNotEqual(response_data["answer"], "")  # Ensure answer is not an empty string

        logger.info("=== Test Case 3 Completed ===\n")

    def test_correct_customer_guid_and_chat_id(self):
        """Test case 4: Valid customer_guid and chat_id"""
        logger.info("=== Starting Test Case 4: Correct customer_guid and chat_id ===")

        url = f"{self.BASE_URL}/chat"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Verify the response status code
        self.assertEqual(response.status_code, 200)

        # Parse the response JSON
        response_data = response.json()

        # Verify that the chat_id in response matches the input chat_id
        self.assertEqual(response_data["chat_id"], self.valid_chat_id,
                         "Chat ID in response should match the input chat_id")

        # Verify that the customer_guid in response matches the input customer_guid
        self.assertEqual(response_data["customer_guid"], self.valid_customer_guid,
                         "Customer GUID in response should match the input customer_guid")

        # Verify that the response contains an answer field with a string value
        self.assertIn("answer", response_data, "Response should contain an answer field")
        self.assertIsInstance(response_data["answer"], str, "Answer should be a string")
        self.assertNotEqual(response_data["answer"], "", "Answer should not be empty")

        logger.info("=== Test Case 4 Completed ===\n")

    def test_correct_ids_without_question(self):
        """Test case 5: Valid IDs but missing question"""
        logger.info("=== Starting Test Case 5: Correct IDs without question ===")

        url = f"{self.BASE_URL}/chat"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 422)
        # Changed assertion to match actual response
        self.assertIn("field required", response.text.lower())
        logger.info("=== Test Case 5 Completed ===\n")

    def test_missing_all_input(self):
        """Test case 6: No input data"""
        logger.info("=== Starting Test Case 6: Missing all input ===")

        url = f"{self.BASE_URL}/chat"
        data = {}
        logger.info("INPUT: Sending empty request")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")


        self.assertEqual(response.status_code, 422)
        self.assertIn("field required", response.text.lower())
        logger.info("=== Test Case 6 Completed ===\n")

    def test_missing_customer_guid(self):
        """Test case 7: Missing customer_guid"""
        logger.info("=== Starting Test Case 7: Missing customer_guid ===")

        url = f"{self.BASE_URL}/chat"
        data = {
            "chat_id": self.valid_chat_id,
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")


        self.assertEqual(response.status_code, 422)
        self.assertIn("field required", response.text.lower())
        logger.info("=== Test Case 7 Completed ===\n")


if __name__ == "__main__":
    unittest.main()
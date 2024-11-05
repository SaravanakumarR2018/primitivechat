import unittest
import requests
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestChatAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"  # Adjust to the correct URL

    def test_chat_api_success(self):
        """Positive test case: Valid chat creation."""
        logger.info("Executing test_chat_api_success: Valid chat message handling.")
        
        payload = {
            "customer_guid": "1234",
            "chat_id": "100",
            "question": "What movies are recommended?"
        }
        response = requests.post(f"{self.BASE_URL}/chat", json=payload)
        logger.info(f"Response status code: {response.status_code}")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("chat_id", data)
        self.assertEqual(data["customer_guid"], payload["customer_guid"])
        logger.info("test_chat_api_success completed successfully.")

    def test_chat_api_existing_customer_id(self):
        """Positive test case: Existing customer ID."""
        logger.info("Executing test_chat_api_existing_customer_id: Handling for existing customer ID.")

        payload = {
            "customer_guid": "1234",
            "chat_id": "101",
            "question": "What TV shows are trending?"
        }
        response = requests.post(f"{self.BASE_URL}/chat", json=payload)
        logger.info(f"Response status code: {response.status_code}")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("chat_id", data)
        self.assertEqual(data["customer_guid"], payload["customer_guid"])
        logger.info("test_chat_api_existing_customer_id completed successfully.")

    def test_chat_api_non_existent_customer_id(self):
        """Negative test case: Non-existent customer ID."""
        logger.info("Executing test_chat_api_non_existent_customer_id: Handling for non-existent customer ID.")
        
        payload = {
            "customer_guid": "non_existent_id",
            "chat_id": "102",
            "question": "What are some good movies?"
        }
        response = requests.post(f"{self.BASE_URL}/chat", json=payload)
        logger.info(f"Response status code: {response.status_code}")

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["detail"], "Chat ID not found or invalid")
        logger.info("test_chat_api_non_existent_customer_id completed successfully.")

    def test_chat_api_no_chat_id(self):
        """Negative test case: Missing chat ID."""
        logger.info("Executing test_chat_api_no_chat_id: Handling when chat ID is not provided.")

        payload = {
            "customer_guid": "1234",
            "question": "What are the latest shows?"
        }
        response = requests.post(f"{self.BASE_URL}/chat", json=payload)
        logger.info(f"Response status code: {response.status_code}")

        self.assertEqual(response.status_code, 422)
        logger.info("test_chat_api_no_chat_id completed successfully.")

    def test_chat_api_empty_customer_id(self):
        """Negative test case: Empty customer ID."""
        logger.info("Executing test_chat_api_empty_customer_id: Handling empty customer ID.")
        
        payload = {
            "customer_guid": "",
            "chat_id": "103",
            "question": "What movies are recommended?"
        }
        response = requests.post(f"{self.BASE_URL}/chat", json=payload)
        logger.info(f"Response status code: {response.status_code}")

        self.assertEqual(response.status_code, 422)
        logger.info("test_chat_api_empty_customer_id completed successfully.")

    def test_chat_api_empty_chat_id(self):
        """Negative test case: Empty chat ID."""
        logger.info("Executing test_chat_api_empty_chat_id: Handling empty chat ID.")
        
        payload = {
            "customer_guid": "1234",
            "chat_id": "",
            "question": "What movies are recommended?"
        }
        response = requests.post(f"{self.BASE_URL}/chat", json=payload)
        logger.info(f"Response status code: {response.status_code}")

        self.assertEqual(response.status_code, 422)
        logger.info("test_chat_api_empty_chat_id completed successfully.")

    def test_chat_api_empty_question(self):
        """Negative test case: Empty question."""
        logger.info("Executing test_chat_api_empty_question: Handling empty question.")
        
        payload = {
            "customer_guid": "1234",
            "chat_id": "104",
            "question": ""
        }
        response = requests.post(f"{self.BASE_URL}/chat", json=payload)
        logger.info(f"Response status code: {response.status_code}")

        self.assertEqual(response.status_code, 422)
        logger.info("test_chat_api_empty_question completed successfully.")

    def test_chat_api_no_question(self):
        """Negative test case: Missing question."""
        logger.info("Executing test_chat_api_no_question: Handling missing question field.")
        
        payload = {
            "customer_guid": "1234",
            "chat_id": "105"
        }
        response = requests.post(f"{self.BASE_URL}/chat", json=payload)
        logger.info(f"Response status code: {response.status_code}")

        self.assertEqual(response.status_code, 422)
        logger.info("test_chat_api_no_question completed successfully.")

    def test_chat_api_no_data(self):
        """Negative test case: No data provided."""
        logger.info("Executing test_chat_api_no_data: Handling no data provided.")
        
        response = requests.post(f"{self.BASE_URL}/chat")
        logger.info(f"Response status code: {response.status_code}")

        self.assertEqual(response.status_code, 422)
        logger.info("test_chat_api_no_data completed successfully.")

if __name__ == "__main__":
    unittest.main()
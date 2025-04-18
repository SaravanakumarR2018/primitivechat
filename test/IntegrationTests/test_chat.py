import logging
import os
import unittest
import json

import requests

from src.backend.lib.logging_config import log_format
from utils.api_utils import add_customer,create_test_token, create_token_without_org_id,create_token_without_org_role
from src.backend.lib.default_ai_response import DEFAULTAIRESPONSE

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format=log_format
)
logger = logging.getLogger(__name__)

# Constants
TEST_ORG = "test_org"
ORG_ADMIN_ROLE = "org:admin"
INVALID_GUID = "invalid-guid"

class TestChatAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    @staticmethod
    def use_llm_response(flag: bool):
        url = f"{TestChatAPI.BASE_URL}/llm_service/use_llm_response"
        res = requests.post(url, json={"use_llm": flag})
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_llm_response_mode():
        url = f"{TestChatAPI.BASE_URL}/llm_service/get_llm_response_mode"
        res = requests.get(url)
        res.raise_for_status()
        return res.json().get("llm_response_mode")

    def setUp(self):
        """Setup function to create valid customer_guid and chat_id"""
        logger.info("=== Starting setUp process ===")

        # Get valid customer_guid
        customer_data = add_customer("test_org")
        self.valid_customer_guid = customer_data["customer_guid"]
        self.org_id = customer_data.get("org_id")
        logger.info(f"OUTPUT: Received valid customer_guid: {self.valid_customer_guid}")

        # Create a test token for authentication
        self.token = create_test_token(org_id=self.org_id, org_role=ORG_ADMIN_ROLE)
        self.headers = {'Authorization': f'Bearer {self.token}'}

        # Get valid chat_id
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {
            "question": "Initial question"
        }
        logger.info(f"INPUT: Creating initial chat with data: {str(chat_data)}")

        chat_response = requests.post(chat_url, json=chat_data, headers=self.headers)
        logger.info(f"OUTPUT: Chat creation response status: {chat_response.status_code}")

        self.assertEqual(chat_response.status_code, 200)
        chat_data = chat_response.json()
        self.valid_chat_id = chat_data["chat_id"]
        self.user_id = chat_data["user_id"]
        logger.info(f"OUTPUT: Received valid chat_id: {self.valid_chat_id}")
        logger.info("=== setUp completed successfully ===\n")

        # Disable LLM by default
        TestChatAPI.use_llm_response(False)
        self.assertEqual(TestChatAPI.get_llm_response_mode(), "NONLLM")

        # Create a base chat_id
        res = requests.post(f"{self.BASE_URL}/chat", json={"question": "Initial?"}, headers=self.headers)
        self.valid_chat_id = res.json()["chat_id"]

    def tearDown(self):
        TestChatAPI.use_llm_response(False)

    def _parse_stream_response(self, response):
        """Utility: Convert SSE stream response to full string answer"""
        content = ""
        for line in response.iter_lines():
            if line and line.decode().startswith("data:"):
                raw = line.decode().replace("data: ", "")
                if raw != "[DONE]":
                    try:
                        data = json.loads(raw)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content += delta.get("content", "")
                    except Exception:
                        continue
        return content.strip()

    def test_streaming_response_llm_disabled(self):
        TestChatAPI.use_llm_response(False)
        self.assertEqual(TestChatAPI.get_llm_response_mode(), "NONLLM")

        url = f"{self.BASE_URL}/chat"
        payload = {
            "chat_id": self.valid_chat_id,
            "question": "Who is Modi in a sentence?",
            "stream": True
        }

        response = requests.post(url, headers=self.headers, json=payload, stream=True)
        self.assertEqual(response.status_code, 200)
        full_answer = ""

        for line in response.iter_lines():
            if line and line.decode().startswith("data:"):
                raw = line.decode().replace("data: ", "")
                if raw != "[DONE]":
                    data = json.loads(raw)
                    # Verify fields in each stream
                    self.assertEqual(data["chat_id"], self.valid_chat_id)
                    self.assertEqual(data["customer_guid"], self.valid_customer_guid)
                    self.assertEqual(data["user_id"], self.user_id)
                    self.assertEqual(data["object"], "chat.completion")
                    self.assertIn("choices", data)
                    for choice in data["choices"]:
                        self.assertIn("delta", choice)
                        self.assertIn("index", choice)
                        self.assertIn("finish_reason", choice)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    full_answer += delta.get("content", "")

        self.assertEqual(full_answer, DEFAULTAIRESPONSE)

    def test_streaming_response_llm_enabled(self):
        TestChatAPI.use_llm_response(True)
        self.assertEqual(TestChatAPI.get_llm_response_mode(), "LLM")

        url = f"{self.BASE_URL}/chat"
        payload = {
            "chat_id": self.valid_chat_id,
            "question": "What is a car in a sentence?",
            "stream": True
        }

        response = requests.post(url, headers=self.headers, json=payload, stream=True)
        self.assertEqual(response.status_code, 200)
        full_answer = ""

        for line in response.iter_lines():
            if line and line.decode().startswith("data:"):
                raw = line.decode().replace("data: ", "")
                if raw != "[DONE]":
                    data = json.loads(raw)
                    # Verify fields in each stream
                    self.assertEqual(data["chat_id"], self.valid_chat_id)
                    self.assertEqual(data["customer_guid"], self.valid_customer_guid)
                    self.assertEqual(data["user_id"], self.user_id)
                    self.assertEqual(data["object"], "chat.completion")
                    self.assertIn("choices", data)
                    for choice in data["choices"]:
                        self.assertIn("delta", choice)
                        self.assertIn("index", choice)
                        self.assertIn("finish_reason", choice)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    full_answer += delta.get("content", "")

        self.assertNotEqual(full_answer, DEFAULTAIRESPONSE)
        self.assertTrue(len(full_answer) > 0)

    def test_non_stream_response_llm_disabled(self):
        TestChatAPI.use_llm_response(False)
        self.assertEqual(TestChatAPI.get_llm_response_mode(), "NONLLM")

        url = f"{self.BASE_URL}/chat"
        payload = {
            "chat_id": self.valid_chat_id,
            "question": "Who is Modi in a sentence?",
            "stream": False
        }

        response = requests.post(url, headers=self.headers, json=payload)
        self.assertEqual(response.status_code, 200)
        answer = response.json().get("answer")

        self.assertEqual(answer, DEFAULTAIRESPONSE)
        # Verify other output fields for LLM disabled
        response_data = response.json()
        self.assertEqual(response_data["chat_id"], self.valid_chat_id)
        self.assertEqual(response_data["customer_guid"], self.valid_customer_guid)
        self.assertEqual(response_data["user_id"], self.user_id)

    def test_non_stream_response_llm_enabled(self):
        TestChatAPI.use_llm_response(True)
        self.assertEqual(TestChatAPI.get_llm_response_mode(), "LLM")

        url = f"{self.BASE_URL}/chat"
        payload = {
            "chat_id": self.valid_chat_id,
            "question": "What is a car in a sentence?",
            "stream": False
        }

        response = requests.post(url, headers=self.headers, json=payload)
        self.assertEqual(response.status_code, 200)
        answer = response.json().get("answer")

        self.assertNotEqual(answer, DEFAULTAIRESPONSE)
        self.assertTrue(len(answer) > 0)
        # Verify other output fields for LLM enabled
        response_data = response.json()
        self.assertEqual(response_data["chat_id"], self.valid_chat_id)
        self.assertEqual(response_data["customer_guid"], self.valid_customer_guid)
        self.assertEqual(response_data["user_id"], self.user_id)

    def test_clear_histories_api(self):
        url = f"{self.BASE_URL}/llm_service/clear_histories"
        response = requests.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("message"), "All conversation histories have been cleared.")

    def test_wrong_customer_guid_and_wrong_chat_id(self):
        """Test case 1: Invalid customer_guid and wrong chat_id"""
        logger.info("=== Starting Test Case 1: Wrong customer_guid and wrong chat_id ===")

        # Simulate a token with an invalid or missing customer_guid
        invalid_token = create_test_token(org_id="invalid_ord_id", org_role="org:admin")
        headers = {'Authorization': f'Bearer {invalid_token}'}

        url = f"{self.BASE_URL}/chat"
        data = {
            "chat_id": "invalid_chat_id",
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=headers)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Invalid customer_guid provided")
        logger.info("=== Test Case 1 Completed ===\n")

    def test_correct_customer_guid_wrong_chat_id(self):
        """Test case 2: Valid customer_guid but invalid chat_id"""
        logger.info("=== Starting Test Case 2: Correct customer_guid and wrong chat_id ===")

        url = f"{self.BASE_URL}/chat"
        data = {
            "chat_id": "invalid_chat_id",
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=self.headers)
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
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=self.headers)
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
            "chat_id": self.valid_chat_id,
            "question": "Test question"
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=self.headers)
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
            "chat_id": self.valid_chat_id
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data, headers=self.headers)
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

        response = requests.post(url, json=data, headers=self.headers)
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

        self.assertEqual(response.status_code, 401)
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Authentication required")

        logger.info("=== Test Case 7 Completed ===\n")
        
    def test_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        headers = {"Authorization": "Bearer corrupted_token"}
        url = f"{self.BASE_URL}/chat"
        data = {
            "chat_id": self.valid_chat_id,
            "question": "Test question"
        }

        logger.info("Testing API request with corrupted token")
        response = requests.post(url, json=data, headers=headers)
        self.assertEqual(response.status_code, 401, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")
        logger.info("=== Test Case 8 Completed ===\n")

    def test_chat_token_without_org_role(self):
        logger.info("Testing chat API with a token missing org_role")

        headers = {'Authorization': f'Bearer {create_token_without_org_role(self.org_id)}'}
        url = f"{self.BASE_URL}/chat"
        data = {
            "chat_id": self.valid_chat_id,
            "question": "Test question"
        }
        response = requests.post(url, json=data, headers=headers)

        self.assertEqual(response.status_code, 403, "Expected status code 403 for missing org_role")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

        logger.info("=== Test Case 9 Completed ===\n")

    def test_chat_token_without_org_id(self):
        logger.info("Testing chat API with a token missing org_id")

        url = f"{self.BASE_URL}/chat"
        headers = {'Authorization': f'Bearer {create_token_without_org_id(ORG_ADMIN_ROLE)}'}
        data = {
            "chat_id": self.valid_chat_id,
            "question": "Test question"
        }
        response = requests.post(url, json=data, headers=headers)

        # Expect 400 Bad Request
        self.assertEqual(response.status_code, 400, "Expected status code 400 for missing org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

        logger.info("=== Test Case 10 Completed ===\n")

    def test_chat_no_mapping_customer_guid(self):
        logger.info("Testing chat API with no mapping between org_id and customer_guid")

        # Create a new org_id without mapping it to a customer_guid
        org_id = "unmapped_org_id"
        token = create_test_token(org_id=org_id, org_role=ORG_ADMIN_ROLE)
        headers = {'Authorization': f'Bearer {token}'}

        url = f"{self.BASE_URL}/chat"
        data = {
            "chat_id": self.valid_chat_id,
            "question": "Test question"
        }
        response = requests.post(url, json=data, headers=headers)

        self.assertEqual(response.status_code, 404, "Expected status code 404 for unmapped org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided", "Unexpected error message")

        logger.info("=== Test Case 11 Completed ===\n")    

    def test_correct_customer_guid_and_correct_user_id(self):
        """Test case 4: Valid customer_guid and valid user_id"""
        logger.info("=== Starting Test Case 12: Correct customer_guid and correct user_id ===")

        # Step 1: Create a chat first to get a valid chat_id
        chat_request_payload = {"question": "Test message"}
        response_chat = requests.post(f"{self.BASE_URL}/chat", headers=self.headers, json=chat_request_payload)
        self.assertEqual(response_chat.status_code, 200, "Failed to create chat.")
        chat_id = response_chat.json().get("chat_id")

        # Step 2: Call /getallchats with the valid chat_id
        url = f"{self.BASE_URL}/getallchats?chat_id={chat_id}"
        logger.info(f"INPUT: Sending request to: {url}")

        response = requests.get(url, headers=self.headers)

        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Step 3: Validate the response
        self.assertEqual(response.status_code, 200, "Expected status code 200 for valid customer_guid and user_id.")

        logger.info("=== Test Case 12 Completed ===\n")

    def test_correct_user_id_and_wrong_customer_guid(self):
        """Test case 5: Valid user_id but invalid customer_guid"""
        logger.info("=== Starting Test Case 13: Correct user_id and wrong customer_guid ===")

        # Step 1: Create a chat first to get a valid chat_id
        chat_request_payload = {"question": "Test message"}
        response_chat = requests.post(f"{self.BASE_URL}/chat", headers=self.headers, json=chat_request_payload)
        self.assertEqual(response_chat.status_code, 200, "Failed to create chat.")
        chat_id = response_chat.json().get("chat_id")

        # Step 2: Generate an invalid token (wrong customer_guid)
        invalid_token = create_test_token(org_id="invalid_org_id", org_role=ORG_ADMIN_ROLE)
        invalid_headers = {'Authorization': f'Bearer {invalid_token}'}

        # Step 3: Call /getallchats with wrong customer_guid
        url = f"{self.BASE_URL}/getallchats?chat_id={chat_id}"
        logger.info(f"INPUT: Sending request to: {url}")

        response = requests.get(url, headers=invalid_headers)

        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Step 4: Validate response for invalid customer_guid
        self.assertEqual(response.status_code, 404, "Expected status code 404 for wrong customer_guid.")

        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Invalid customer_guid provided")

        logger.info("=== Test Case 13 Completed ===\n")

if __name__ == "__main__":
    unittest.main()

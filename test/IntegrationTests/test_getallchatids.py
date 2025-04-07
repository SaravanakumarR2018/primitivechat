import os
import logging
import unittest
import requests
from src.backend.lib.logging_config import log_format
from utils.api_utils import (
    add_customer,
    create_test_token,
    create_token_without_org_role,
    create_token_without_org_id,
)

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

ORG_ADMIN_ROLE = "org:admin"


# [Your imports remain unchanged above]

class TestGetAllChatIDsAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        logger.info("=== [setUp] Starting setup for test case ===")
        customer_data = add_customer("test_org")
        self.valid_customer_guid = customer_data["customer_guid"]
        self.org_id = customer_data.get("org_id")
        self.token = create_test_token(org_id=self.org_id, org_role=ORG_ADMIN_ROLE)
        self.headers = {'Authorization': f'Bearer {self.token}'}
        logger.info(f"[setUp] org_id: {self.org_id}, customer_guid: {self.valid_customer_guid}")
        logger.info("[setUp] Token created and setup completed.\n")

    def create_chat(self, question="Who is the Prime Minister of India?"):
        chat_url = f"{self.BASE_URL}/chat"
        chat_data = {"question": question}
        logger.info(f"[create_chat] Sending POST to {chat_url} with: {chat_data}")
        response = requests.post(chat_url, json=chat_data, headers=self.headers)
        logger.info(f"[create_chat] Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 200, "[create_chat] Expected 200 OK for chat creation")
        return response.json()["chat_id"]

    def test_valid_request_fetch_chat_ids(self):
        logger.info("=== Test Case 1: Valid request with existing chat history ===")
        chat_id = self.create_chat()
        url = f"{self.BASE_URL}/getallchatids"
        logger.info(f"[test] Sending GET to {url}")
        response = requests.get(url, headers=self.headers)
        logger.info(f"[test] Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(chat_id, response.json()["chat_ids"])
        logger.info("=== Test Case 1 Completed ===\n")

    def test_valid_request_no_chat_history(self):
        logger.info("=== Test Case 2: Valid request with no chat history ===")
        url = f"{self.BASE_URL}/getallchatids"
        response = requests.get(url, headers=self.headers)
        logger.info(f"[test] Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["chat_ids"], [])
        logger.info("=== Test Case 2 Completed ===\n")

    def test_invalid_customer_guid(self):
        logger.info("=== Test Case 3: Invalid customer GUID ===")
        invalid_token = create_test_token(org_id="invalid_org_id", org_role=ORG_ADMIN_ROLE)
        response = requests.get(f"{self.BASE_URL}/getallchatids", headers={'Authorization': f'Bearer {invalid_token}'})
        logger.info(f"[test] Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided")
        logger.info("=== Test Case 3 Completed ===\n")

    def test_invalid_user_id(self):
        logger.info("=== Test Case 4: Invalid User ID ===")

        # Create a token with an invalid user ID (None or fake ID)
        invalid_user_token = create_test_token(org_id=self.org_id, org_role=ORG_ADMIN_ROLE,
                                               sub=None)  # Ensure invalidity
        invalid_headers = {'Authorization': f'Bearer {invalid_user_token}'}

        # Send request to get chat IDs
        response = requests.get(f"{self.BASE_URL}/getallchatids", headers=invalid_headers)

        # Log response details
        logger.info(f"[test] Response: {response.status_code}, {response.text}")

        # Assertions
        self.assertEqual(response.status_code, 401, "[test] Expected 401 Unauthorized for invalid user ID")
        self.assertEqual(response.json()["detail"], "Authentication required",
                         "[test] Expected 'Invalid user_id provided' error message")

        logger.info("=== Test Case 4 Completed ===\n")

    def test_getallchatids_without_token(self):
        logger.info("=== Test Case 5: Missing token ===")
        response = requests.get(f"{self.BASE_URL}/getallchatids")
        logger.info(f"[test] Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication required")
        logger.info("=== Test Case 5 Completed ===\n")

    def test_getallchatids_with_corrupted_token(self):
        logger.info("=== Test Case 6: Corrupted token ===")
        response = requests.get(f"{self.BASE_URL}/getallchatids", headers={"Authorization": "Bearer corrupted_token"})
        logger.info(f"[test] Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication required")
        logger.info("=== Test Case 6 Completed ===\n")

    def test_getallchatids_without_org_role(self):
        logger.info("=== Test Case 7: Token without org role ===")
        token = create_token_without_org_role(self.org_id)
        response = requests.get(f"{self.BASE_URL}/getallchatids", headers={'Authorization': f'Bearer {token}'})
        logger.info(f"[test] Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 403)
        logger.info("=== Test Case 7 Completed ===\n")

    def test_getallchatids_with_no_mapping_customer_guid(self):
        logger.info("=== Test Case 8: Unmapped customer_guid ===")
        token = create_test_token(org_id="unmapped_org_id", org_role=ORG_ADMIN_ROLE)
        response = requests.get(f"{self.BASE_URL}/getallchatids", headers={'Authorization': f'Bearer {token}'})
        logger.info(f"[test] Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided")
        logger.info("=== Test Case 8 Completed ===\n")

    def test_getallchatids_without_org_id(self):
        logger.info("=== Test Case 9: Token without org ID ===")
        token = create_token_without_org_id(ORG_ADMIN_ROLE)
        response = requests.get(f"{self.BASE_URL}/getallchatids", headers={'Authorization': f'Bearer {token}'})
        logger.info(f"[test] Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Org ID not found in token")
        logger.info("=== Test Case 9 Completed ===\n")

    def test_large_number_of_chat_ids(self):
        logger.info("=== Test Case 10: Large number of chat IDs ===")
        messages = [
            "Hello!", "How are you today?", "Tell me a joke.", "What's the weather like?",
            "Who won the last World Cup?", "Explain quantum mechanics.", "Give me a fun fact.",
            "How does blockchain work?", "What's the capital of Japan?", "Tell me about Python programming."
        ]

        created_chat_ids = []
        for message in messages:
            logger.info(f"[Creating Chat] Message: {message}")
            response = requests.post(f"{self.BASE_URL}/chat", json={"question": message}, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            chat_id = response.json().get("chat_id")
            self.assertIsNotNone(chat_id)
            created_chat_ids.append(chat_id)

        response = requests.get(f"{self.BASE_URL}/getallchatids", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        returned_chat_ids = response.json().get("chat_ids", [])

        for chat_id in created_chat_ids:
            self.assertIn(chat_id, returned_chat_ids)

        logger.info("=== Test Case 10 Completed ===\n")

    def test_retrieval_with_specific_pagination(self):
        logger.info("=== Test Case 11: Retrieval with specific pagination parameters ===")

        # Ensure at least 10 chats exist before testing pagination
        messages = [
            "Hello!", "How are you?", "Tell me a joke.", "What's the weather?",
            "Who won the World Cup?", "Explain AI.", "Give me a fun fact.",
            "How does blockchain work?", "Capital of Japan?", "Tell me about Python."
        ]

        created_chat_ids = []
        for message in messages:
            logger.info(f"[Creating Chat] Message: {message}")
            response = requests.post(f"{self.BASE_URL}/chat", json={"question": message}, headers=self.headers)
            self.assertEqual(response.status_code, 200, "[test] Expected 200 OK for chat creation")
            chat_id = response.json().get("chat_id")
            self.assertIsNotNone(chat_id, "[test] chat_id should not be None")
            created_chat_ids.append(chat_id)

        url = f"{self.BASE_URL}/getallchatids?page=2&page_size=5"
        logger.info(f"[test] Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"[test] Response: {response.status_code}, {response.text}")

        self.assertEqual(response.status_code, 200, "[test] Expected 200 OK response")

        data = response.json()
        self.assertIsInstance(data, dict, "[test] Response is not a dictionary")
        self.assertIn("chat_ids", data, "[test] Missing 'chat_ids' key in response")
        self.assertIsInstance(data["chat_ids"], list, "[test] 'chat_ids' is not a list")

        # Check if the response contains at most 5 chat IDs for pagination
        self.assertLessEqual(len(data["chat_ids"]), 5, "[test] Expected at most 5 chat IDs in response")

        logger.info("=== Test Case 11 Completed ===\n")

    def test_retrieve_with_large_page_size(self):
        logger.info("=== Test Case 12: Retrieval with large but valid page_size ===")

        # Ensure at least 100 chats exist before testing large page size
        messages = [f"Chat message {i + 1}" for i in range(100)]

        created_chat_ids = []
        for message in messages:
            logger.info(f"[Creating Chat] Message: {message}")
            response = requests.post(f"{self.BASE_URL}/chat", json={"question": message}, headers=self.headers)
            self.assertEqual(response.status_code, 200, "[test] Expected 200 OK for chat creation")
            chat_id = response.json().get("chat_id")
            self.assertIsNotNone(chat_id, "[test] chat_id should not be None")
            created_chat_ids.append(chat_id)

        url = f"{self.BASE_URL}/getallchatids?page=1&page_size=100"
        logger.info(f"[test] Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"[test] Response: {response.status_code}, {response.text}")

        self.assertEqual(response.status_code, 200, "[test] Expected 200 OK response")

        data = response.json()
        self.assertIsInstance(data, dict, "[test] Response is not a dictionary")
        self.assertIn("chat_ids", data, "[test] Missing 'chat_ids' key in response")
        self.assertIsInstance(data["chat_ids"], list, "[test] 'chat_ids' is not a list")

        # Check if response contains at most 100 chat IDs
        self.assertLessEqual(len(data["chat_ids"]), 100, "[test] Expected at most 100 chat IDs in response")

        logger.info("=== Test Case 12 Completed ===\n")

    def test_chat_ids_are_unique(self):
        logger.info("=== Test Case 13: Chat IDs are unique ===")

        # Create two separate chats
        chat_id_1 = self.create_chat("What's AI?")
        chat_id_2 = self.create_chat("What's ML?")

        logger.info(f"[test] Created chat_id_1: {chat_id_1}")
        logger.info(f"[test] Created chat_id_2: {chat_id_2}")

        # Verify chat IDs are different
        self.assertNotEqual(chat_id_1, chat_id_2, "[test] Chat IDs should be unique")

        # Fetch all chat IDs from the API
        response = requests.get(f"{self.BASE_URL}/getallchatids", headers=self.headers)

        logger.info(f"[test] API Response: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 200, "[test] Expected 200 OK when fetching chat IDs")

        # Extract chat IDs from response
        all_chat_ids = response.json().get("chat_ids", [])

        # Validate both chat IDs are in the response
        self.assertIn(chat_id_1, all_chat_ids, "[test] chat_id_1 should be in response")
        self.assertIn(chat_id_2, all_chat_ids, "[test] chat_id_2 should be in response")

        logger.info("=== Test Case 13 Completed ===\n")

    def test_extreme_large_page_number(self):
        logger.info("=== Test Case 14: Requesting chat IDs with a very large page number ===")

        url = f"{self.BASE_URL}/getallchatids?page=999999&page_size=5"
        response = requests.get(url, headers=self.headers)

        logger.info(f"[test] Actual Response: {response.status_code}, {response.text}")

        # Expecting either a 400 if API restricts large page numbers or 200 if it handles it gracefully
        self.assertIn(response.status_code, [200, 400], f"[test] Unexpected status code {response.status_code}")

        # If the API returns 400, expect an error message
        if response.status_code == 400:
            self.assertIn("Invalid page number", response.text, "[test] Expected 'Invalid page number' in response")

        logger.info("=== Test Case 14 Completed ===\n")

    def test_positive_page_number(self):
        logger.info("=== Test Case 15: Requesting chat IDs with a valid positive page number ===")

        url = f"{self.BASE_URL}/getallchatids?page=2&page_size=5"
        response = requests.get(url, headers=self.headers)

        logger.info(f"[test] Actual Response: {response.status_code}, {response.text}")

        # Expecting a 200 OK for valid page numbers
        self.assertEqual(response.status_code, 200, f"[test] Expected 200, but got {response.status_code}")

        # Ensure the response contains valid chat IDs (adjust as per actual API response)
        response_json = response.json()
        self.assertIn("chat_ids", response_json, "[test] Expected 'chat_ids' key in response")
        self.assertIsInstance(response_json["chat_ids"], list, "[test] Expected 'chat_ids' to be a list")

        logger.info("=== Test Case 15 Completed ===\n")

    def tearDown(self):
        logger.info(f"=== [tearDown] Completed test: {self._testMethodName} ===\n")

if __name__ == "__main__":
    unittest.main()

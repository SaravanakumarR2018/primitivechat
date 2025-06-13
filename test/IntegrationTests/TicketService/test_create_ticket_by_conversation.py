import os
import sys
import unittest
import requests
import json # Added for json.dumps
from http import HTTPStatus

# Ensure the utils directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))) # Adjust path to root of test utils
from utils.api_utils import add_customer, create_test_token, create_token_without_org_id, create_token_without_org_role

from src.backend.lib.logging_config import get_primitivechat_logger # Path to actual logger
logger = get_primitivechat_logger(__name__)


class TestCreateTicketByConversationAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}" # Provide defaults
    ORG_ROLE = 'org:admin' 

    @staticmethod
    def use_llm_response(use_llm: bool, llmprovider: str = None, model: str = None):
        url = f"{TestCreateTicketByConversationAPI.BASE_URL}/llm_service/use_llm_response"
        payload = {"use_llm": use_llm}
        if llmprovider:
            payload["llmprovider"] = llmprovider
        if model:
            payload["model"] = model
        res = requests.post(url, json=payload)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_llm_response_mode():
        url = f"{TestCreateTicketByConversationAPI.BASE_URL}/llm_service/get_llm_response_mode"
        res = requests.get(url)
        res.raise_for_status()
        return res.json()

    def setUp(self):
        logger.info(f"=== Setting up test environment for {self._testMethodName} ===")
        self.headers = {}

        # 1. Add customer
        org_name = "test_org"
        customer_data = add_customer(org_name)
        self.customer_guid = customer_data.get("customer_guid")
        self.org_id = customer_data.get("org_id")
        self.assertIsNotNone(self.customer_guid, "Failed to get customer_guid")
        self.assertIsNotNone(self.org_id, "Failed to get org_id")

        # 2. Create token
        self.token = create_test_token(org_id=self.org_id, org_role=self.ORG_ROLE)
        self.headers['Authorization'] = f'Bearer {self.token}'
        TestCreateTicketByConversationAPI.use_llm_response(use_llm=False)
        self.assertEqual(TestCreateTicketByConversationAPI.get_llm_response_mode().get("llm_response_mode"), "NONLLM")
        # 4. Create a chat and add messages to establish context
        chat_url = f"{self.BASE_URL}/chat"
        # First message to create the chat
        chat_create_payload = {"question": "My laptop is broken.", "stream": False}
        response = requests.post(chat_url, json=chat_create_payload, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK, f"Failed to create chat. Response: {response.text}")
        response_json = response.json()
        self.chat_id = response_json.get("chat_id")
        self.assertIsNotNone(self.chat_id, "Failed to get chat_id")

    def _add_chat_messages(self, chat_url, chat_id, headers):
        """Helper to add a set of predefined messages to a chat for context."""
        messages_to_add = [
            {"question": "It's a Dell XPS.", "chat_id": chat_id, "stream": False},
            {"question": "The screen is flickering badly.", "chat_id": chat_id, "stream": False},
            {"question": "I've tried restarting it, but the problem persists.", "chat_id": chat_id, "stream": False},
            {"question": "The issue started after a Windows update.", "chat_id": chat_id, "stream": False},
            {"question": "No, I haven't dropped the laptop.", "chat_id": chat_id, "stream": False},
            {"question": "The flickering happens even in Safe Mode.", "chat_id": chat_id, "stream": False},
            {"question": "I see horizontal lines on the display.", "chat_id": chat_id, "stream": False},
        ]
        for msg_payload in messages_to_add:
            response = requests.post(chat_url, json=msg_payload, headers=headers)
            self.assertEqual(response.status_code, HTTPStatus.OK, 
                             f"Failed to add message to chat {chat_id}. Response: {response.text}")

    def test_create_ticket_by_conversation_without_custom_field(self):
        # Step 1: Create ticket
        chat_url = f"{self.BASE_URL}/chat"
        self._add_chat_messages(chat_url, self.chat_id, self.headers)
        TestCreateTicketByConversationAPI.use_llm_response(use_llm=True, llmprovider="GEMINI", model="gemini-1.5-flash")
        self.assertEqual(TestCreateTicketByConversationAPI.get_llm_response_mode().get("llm_response_mode"), "LLM")
        url = f"{self.BASE_URL}/create_ticket_by_conversation?message_count=20"
        payload = {
            "chat_id": self.chat_id,
            "reported_by": "test_user"  # Use the first 3 messages added in setUp
        }
        response = requests.post(url, json=payload, headers=self.headers)
        TestCreateTicketByConversationAPI.use_llm_response(use_llm=False, llmprovider="GEMINI", model="gemini-1.5-flash")
        self.assertEqual(TestCreateTicketByConversationAPI.get_llm_response_mode().get("llm_response_mode"), "NONLLM")
        self.assertEqual(response.status_code, HTTPStatus.OK, f"API call failed: {response.text}")
        response_data = response.json()
        self.assertIn("ticket_id", response_data, "Response should contain 'ticket_id'")
        ticket_id = response_data["ticket_id"]
        self.assertIsInstance(ticket_id, int, "ticket_id should be an integer")
        logger.info(f"Ticket created with ID: {ticket_id}")

        # Step 2: Fetch ticket details
        ticket_url = f"{self.BASE_URL}/tickets/{ticket_id}"
        ticket_response = requests.get(ticket_url, headers=self.headers)
        self.assertEqual(ticket_response.status_code, HTTPStatus.OK, f"Failed to fetch ticket: {ticket_response.text}")
        ticket_data = ticket_response.json()
        logger.info(f"Fetched ticket data: {ticket_response}")
        # Step 3: Assert required fields and their types/validity
        expected_fields = [
            "ticket_id", "chat_id", "title", "description", "priority",
            "status", "reported_by", "assigned", "created_at", "updated_at"
        ]

        for field in expected_fields:
            self.assertIn(field, ticket_data, f"Missing field in response: {field}")
            if field == "assigned":
                # assigned can be None or a string
                self.assertIn(type(ticket_data[field]), [str, type(None)], f"Field '{field}' should be a string or None")
            else:
                self.assertIsNotNone(ticket_data[field], f"Field '{field}' should not be None")

        # Optional: Add type/value assertions for specific fields
        self.assertEqual(ticket_data["ticket_id"], ticket_id)
        self.assertEqual(ticket_data["chat_id"], self.chat_id)
        self.assertIsInstance(ticket_data["title"], str)
        self.assertIsInstance(ticket_data["description"], str)
        self.assertIn(ticket_data["priority"], ["Low", "Medium", "High"])
        self.assertEqual(ticket_data["status"], "open")
        self.assertEqual(ticket_data["reported_by"], "test_user")
        self.assertIsInstance(ticket_data["assigned"], (str, type(None)))  # can be None or a string
        self.assertIn("created_at", ticket_data)
        self.assertIn("updated_at", ticket_data)

    def test_create_ticket_invalid_chat_id(self):
        payload = {
                "chat_id": "non_existent_chat_id_12345",
                "reported_by": "test_user"
        }
        response = requests.post(f"{self.BASE_URL}/create_ticket_by_conversation?message_count=2", json=payload, headers=self.headers)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,
                            f"API call should have failed with 404 for invalid chat_id: {response.text}")
        self.assertIn("No messages found for chat_id non_existent_chat_id_12345", response.json().get("detail", ""))   
    
    def test_create_ticket_without_required_fields(self):
        # Try to create a ticket without required fields (chat_id and reported_by)
        url = f"{self.BASE_URL}/create_ticket_by_conversation?message_count=20"
        # Missing both 'chat_id' and 'reported_by'
        payload = {}
        response = requests.post(url, json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422, f"Expected 422 Unprocessable Entity for missing required fields, got {response.status_code}. Response: {response.text}")
        # Optionally, check that the error message mentions the missing fields
        error_detail = response.json().get("detail", "")
        self.assertTrue(any("chat_id" in str(item) for item in error_detail), "Error should mention missing 'chat_id'")
        self.assertTrue(any("reported_by" in str(item) for item in error_detail), "Error should mention missing 'reported_by'")

    def test_create_ticket_with_no_token(self):
        """Test API request without an authentication token for create_ticket_by_conversation."""
        url = f"{self.BASE_URL}/create_ticket_by_conversation?message_count=3"
        data = {
            "chat_id": self.chat_id,
            "reported_by": "user@example.com"
        }
        logger.info("Testing API request without token (by conversation)")
        response = requests.post(url, json=data)  # No headers
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Missing token should result in 401 Unauthorized")
        self.assertIn("detail", response.json())
        self.assertEqual(response.json()["detail"], "Authentication required", "Missing Token leads to Unauthorized")

    def test_create_ticket_with_corrupted_token(self):
        """Test API request with a corrupted authentication token for create_ticket_by_conversation."""
        url = f"{self.BASE_URL}/create_ticket_by_conversation?message_count=3"
        data = {
            "chat_id": self.chat_id,
            "reported_by": "user@example.com"
        }
        headers = {"Authorization": "Bearer corrupted_token"}
        logger.info("Testing API request with corrupted token (by conversation)")
        response = requests.post(url, json=data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Corrupted token should result in 401 Unauthorized")
        self.assertIn("detail", response.json())
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_create_ticket_with_missing_org_id_in_token(self):
        """Test API request where the token does not have an org_id for create_ticket_by_conversation."""
        url = f"{self.BASE_URL}/create_ticket_by_conversation?message_count=3"
        data = {
            "chat_id": self.chat_id,
            "reported_by": "user@example.com"
        }
        token = create_token_without_org_id(org_role=self.ORG_ROLE)  # No org_id
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("Testing API request with missing org_id in token (by conversation)")
        response = requests.post(url, json=data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Missing org_id should result in 400 Bad Request")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_create_ticket_with_missing_org_role_in_token(self):
        """Test API request where the token does not have an org_role for create_ticket_by_conversation."""
        url = f"{self.BASE_URL}/create_ticket_by_conversation?message_count=3"
        data = {
            "chat_id": self.chat_id,
            "reported_by": "user@example.com"
        }
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        logger.info("Testing API request with missing org_role in token (by conversation)")
        response = requests.post(url, json=data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN, "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_create_ticket_with_unauthorized_org_role(self):
        # Create Test Token for member (not allowed)
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role="org:random_org_role")
        headers = {'Authorization': f'Bearer {token}'}
        url = f"{self.BASE_URL}/create_ticket_by_conversation?message_count=3"
        data = {
            "chat_id": self.chat_id,
            "reported_by": "user@example.com"
        }
        response = requests.post(url, json=data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_create_ticket_with_invalid_org_id_no_mapped_customer_guid(self):
        """Test API request with an org_id that has no mapped customer_guid for create_ticket_by_conversation."""
        url = f"{self.BASE_URL}/create_ticket_by_conversation?message_count=3"
        data = {
            "chat_id": self.chat_id,
            "reported_by": "user@example.com"
        }
        invalid_token = create_test_token(org_id="unmapped_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        logger.info("Testing API request with org_id that has no mapped customer_guid (by conversation)")
        response = requests.post(url, json=data, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "Unmapped org_id should result in 400 Bad Request")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")
    
    def tearDown(self):
        logger.info(f"=== Test {self._testMethodName} completed and passed ===")
        TestCreateTicketByConversationAPI.use_llm_response(use_llm=False, llmprovider="GEMINI", model="gemini-1.5-flash")
        self.assertEqual(TestCreateTicketByConversationAPI.get_llm_response_mode().get("llm_response_mode"), "NONLLM")
        # Reset LLM mode to disabled after each test
        logger.info("=== Test teardown complete ===")

if __name__ == '__main__':
    unittest.main()

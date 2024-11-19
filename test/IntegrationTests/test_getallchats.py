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
            "question": "You will get the correct answer once AI is integrated."
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
            "customer_guid": "invalid_customer_guid",  # Invalid customer GUID
            "chat_id": "invalid_chat_id"  # Invalid chat ID
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Check that the status code is 404
        self.assertEqual(response.status_code, 404, "Expected status code 404 for invalid customer_guid and chat_id.")

        # Verify that the response text contains the expected error message
        self.assertIn("no chats found for this customer and chat id", response.text.lower(),
                      "Expected error message not found in the response.")

        logger.info("=== Test Case 1 Completed ===\n")

    def test_correct_customer_guid_and_wrong_chat_id(self):
        """Test case 2: Valid customer_guid but invalid chat_id"""
        logger.info("=== Starting Test Case 2: Correct customer_guid and wrong chat_id ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,  # Valid customer GUID
            "chat_id": "invalid_chat_id"  # Invalid chat ID
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Check that the status code is 404
        self.assertEqual(response.status_code, 404,
                         "Expected status code 404 for valid customer_guid and invalid chat_id.")

        # Verify that the response text contains the expected error message
        self.assertIn("no chats found for this customer and chat id", response.text.lower(),
                      "Expected error message not found in the response.")

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

        # Check that the status code is 404
        self.assertEqual(response.status_code, 404, "Expected status code 404 for invalid customer_guid.")

        # Verify that the response text contains the expected error message
        self.assertIn("no chats found for this customer and chat id", response.text.lower(),
                      "Expected error message not found in the response.")

        logger.info("=== Test Case 3 Completed ===\n")

    def test_retrieval_with_valid_inputs(self):
        """Test case 4: Valid customer_guid and chat_id"""
        logger.info("=== Starting Test Case 4: Valid customer_guid and chat_id ===")

        # Add multiple chat messages to the chat
        chat_url = f"{self.BASE_URL}/chat"
        messages_to_add = [
            "What are the store hours?"
        ]

        # Variable to hold the chat_id from the first message creation
        local_chat_id = None

        for index, message in enumerate(messages_to_add):
            message_data = {
                "customer_guid": self.valid_customer_guid,
                "question": message  # Using 'question' to represent the message
            }
            logger.info(f"INPUT: Creating message with data: {str(message_data)}")
            message_response = requests.post(chat_url, json=message_data)
            logger.info(f"OUTPUT: Message creation response status: {message_response.status_code}")
            self.assertEqual(message_response.status_code, 200, "Failed to create test message.")

            # Store the chat_id from the first message
            if index == 0:
                local_chat_id = message_response.json().get('chat_id')
                logger.info(f"Stored chat_id from the first message: {local_chat_id}")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": local_chat_id,  # Use the chat_id from the first message
            "page": 1,
            "page_size": 10
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Verify that the response status code is 200
        self.assertEqual(response.status_code, 200, "Expected status code 200, but got: " + str(response.status_code))

        messages = response.json().get('messages')
        self.assertIsInstance(messages, list, "Expected messages to be a list, but got: " + str(type(messages)))

        if messages:  # Check if messages list is not empty
            # Create a set of expected messages to compare
            expected_messages = set(messages_to_add)

            # Create a set of actual messages returned by the API
            actual_messages = set()
            system_messages = set()  # To hold any system messages

            for first_message in messages:
                self.assertEqual(first_message['chat_id'], local_chat_id,
                                 "Chat ID in response does not match the input chat ID")
                self.assertEqual(first_message['customer_guid'], self.valid_customer_guid,
                                 "Customer GUID in response does not match the input customer GUID")

                # Log the first_message to inspect its structure
                logger.info(f"Inspect ing message: {first_message}")

                # Check if the returned message matches the input question
                self.assertIn('message', first_message, "Message does not contain 'message'")  # Corrected line

                # Collect messages based on sender type
                if first_message['sender_type'] == 'system':
                    system_messages.add(first_message['message'])
                else:
                    actual_messages.add(first_message['message'])

                # Verify who sent the message
                self.assertIn('sender_type', first_message, "Message does not contain 'sender_type'")  # Corrected line
                self.assertIn(first_message['sender_type'], ['user', 'system', 'customer'],
                              "Sender should be either 'user', 'system', or 'customer'")

            # Log actual messages for debugging
            logger.info(f"Actual messages received: {actual_messages}")

            # Compare the sets of expected and actual messages
            self.assertSetEqual(expected_messages, actual_messages,
                                "The expected messages do not match the actual messages returned. Expected: {}, Actual: {}".format(
                                    expected_messages, actual_messages))

            # Optionally, check for the presence of system messages if needed
            if system_messages:
                logger.info(f"System messages received: {system_messages}")

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

        # Step 1: Create an initial chat and get the chat_id
        initial_chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "You will get the correct answer once AI is integrated."
        }
        chat_url = f"{self.BASE_URL}/chat"
        chat_response = requests.post(chat_url, json=initial_chat_data)
        self.assertEqual(chat_response.status_code, 200, "Failed to create initial chat.")
        self.valid_chat_id = chat_response.json().get("chat_id")
        logger.info(f"Created initial chat with chat_id: {self.valid_chat_id}")

        # Step 2: Add a chat message to the chat
        message_to_add = "You will get the correct answer once AI is integrated."
        message_data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,  # Use the chat_id from the initial chat creation
            "question": message_to_add  # Ensure this key matches what the API expects
        }
        logger.info(f"INPUT: Creating message with data: {str(message_data)}")
        message_response = requests.post(chat_url, json=message_data)
        logger.info(f"OUTPUT: Message creation response status: {message_response.status_code}")
        self.assertEqual(message_response.status_code, 200, "Failed to create test message.")

        # Step 3: Now retrieve the chat messages using the correct chat_id
        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,  # Use the chat_id from the initial chat creation
            "page": 1,
            "page_size": 1
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Step 4: Check for successful response
        self.assertEqual(response.status_code, 200, "Failed to retrieve chats.")

        response_data = response.json()
        messages = response_data.get('messages')
        self.assertIsInstance(messages, list, "Expected 'messages' to be a list.")
        self.assertEqual(len(messages), 1, "Expected exactly one message to be retrieved.")

        # Verify that the retrieved message matches the one that was added
        retrieved_message = messages[0].get('message')  # Adjust the key if necessary
        self.assertEqual(retrieved_message, message_to_add,
                         "The retrieved message does not match the expected message.")

        logger.info("=== Test Case 6 Completed ===\n")

    def test_missing_customer_guid(self):
        """Test case 7: Missing customer_guid"""
        logger.info("=== Starting Test Case 7: Missing customer_guid ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "chat_id": self.valid_chat_id  # Valid chat ID, but missing customer_guid
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Check that the status code is 422 (Unprocessable Entity)
        self.assertEqual(response.status_code, 422, "Expected status code 422 for missing customer_guid.")

        # Verify that the response text contains the expected error message for missing field
        self.assertIn("field required", response.text.lower(),
                      "Expected error message for missing customer_guid not found in the response.")

        logger.info("=== Test Case 7 Completed ===\n")

    def test_missing_chat_id(self):
        """Test case 8: Missing chat_id"""
        logger.info("=== Starting Test Case 8: Missing chat_id ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid  # Valid customer GUID, but missing chat_id
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")
        # Check that the status code is 422 (Unprocessable Entity)
        self.assertEqual(response.status_code, 422, "Expected status code 422 for missing chat_id.")

        # Verify that the response text contains the expected error message for missing field
        self.assertIn("field required", response.text.lower(),
                      "Expected error message for missing chat_id not found in the response.")

        logger.info("=== Test Case 8 Completed ===\n")

    def test_invalid_page_number(self):
        """Test case 9: Invalid Page Number"""
        logger.info("=== Starting Test Case 9: Invalid Page Number ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,  # Valid customer GUID
            "chat_id": self.valid_chat_id,  # Valid chat ID
            "page": 0,  # Invalid page number
            "page_size": 10  # Valid page size
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Check that the status code is 404
        self.assertEqual(response.status_code, 404, "Expected status code 404 for invalid page number.")

        # Verify that the response text contains the expected error message
        self.assertIn("no chats found for this customer and chat id", response.text.lower(),
                      "Expected error message not found in the response.")

        logger.info("=== Test Case 9 Completed ===\n")

    def test_invalid_page_size(self):
        """Test case 10: Invalid Page Size"""
        logger.info("=== Starting Test Case 10: Invalid Page Size ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 1,
            "page_size": 0  # Invalid page size
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Check that the status code is 404
        self.assertEqual(response.status_code, 404, "Expected status code 404 for invalid page size.")

        # Verify that the response text contains the expected error message
        self.assertIn("no chats found for this customer and chat id", response.text.lower(),
                      "Expected error message not found in the response.")

        logger.info("=== Test Case 10 Completed ===\n")

    def test_large_page_size(self):
        """Test case 11: Large Page Size"""
        logger.info("=== Starting Test Case 11: Large Page Size ===")

        # Create an initial chat and get the chat_id
        initial_chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": "You will get the correct answer once AI is integrated."
        }
        chat_url = f"{self.BASE_URL}/chat"
        chat_response = requests.post(chat_url, json=initial_chat_data)
        self.assertEqual(chat_response.status_code, 200, "Failed to create initial chat.")
        self.valid_chat_id = chat_response.json().get("chat_id")
        logger.info(f"Created initial chat with chat_id: {self.valid_chat_id}")

        # Add multiple chat messages to the chat
        messages_to_add = [
            "Message 1: You will get the correct answer once AI is integrated.",
            "Message 2: You will get the correct answer once AI is integrated.",
            "Message 3: You will get the correct answer once AI is integrated.",
            "Message 4: You will get the correct answer once AI is integrated.",
            "Message 5: You will get the correct answer once AI is integrated.",
        ]

        for message in messages_to_add:
            message_data = {
                "customer_guid": self.valid_customer_guid,
                "chat_id": self.valid_chat_id,  # Include the chat_id here
                "question": message  # Ensure this key matches what the API expects
            }
            logger.info(f"INPUT: Creating message with data: {str(message_data)}")
            message_response = requests.post(chat_url, json=message_data)
            logger.info(f"OUTPUT: Message creation response status: {message_response.status_code}")
            self.assertEqual(message_response.status_code, 200, "Failed to create test message.")

        # Now retrieve all chats using the correct chat_id
        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,  # Use the chat_id from the initial chat creation
            "page": 1,
            "page_size": 1000
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Check for successful response
        self.assertEqual(response.status_code, 200, "Failed to retrieve chats.")

        response_data = response.json()

        # Check that 'messages' is a list
        messages = response_data.get('messages')
        self.assertIsInstance(messages, list, "Expected 'messages' to be a list.")

        # Verify that all added messages are in the response
        for expected_message in messages_to_add:
            self.assertTrue(any(msg.get('message') == expected_message for msg in messages),
                            f"Expected message '{expected_message}' not found in the response.")

        logger.info("=== Test Case 11 Completed ===\n")

    def test_high_page_number(self):
        """Test case 12: High Page Number"""
        logger.info("=== Starting Test case 12: High Page Number ===")

        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,  # Valid customer GUID
            "chat_id": self.valid_chat_id,  # Valid chat ID
            "page": 1000,  # High page number
            "page_size": 10  # Valid page size
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Check that the status code is 404
        self.assertEqual(response.status_code, 404, "Expected status code 404 for high page number.")

        # Verify that the response text contains the expected error message
        self.assertIn("no chats found for this customer and chat id", response.text.lower(),
                      "Expected error message not found in the response.")
        logger.info("=== Test case 12: High Page Number Completed ===\n")

    def test_retrieve_with_large_page_size(self):
        """Test case 13: Retrieve 20 chats when only 5 exist"""
        logger.info("=== Test Case 13 : Retrieve 20 chats when only 5 exist ===")

        # Add 5 chat messages to the chat
        chat_url = f"{self.BASE_URL}/chat"
        messages_to_add = [
            "Message 1: You will get the correct answer once AI is integrated.",
            "Message 2: You will get the correct answer once AI is integrated.",
            "Message 3: You will get the correct answer once AI is integrated.",
            "Message 4: You will get the correct answer once AI is integrated.",
            "Message 5: You will get the correct answer once AI is integrated.",
        ]

        for message in messages_to_add:
            message_data = {
                "customer_guid": self.valid_customer_guid,
                "chat_id": self.valid_chat_id,
                "question": message
            }
            logger.info(f"INPUT: Creating message with data: {str(message_data)}")
            message_response = requests.post(chat_url, json=message_data)
            logger.info(f"OUTPUT: Message creation response status: {message_response.status_code}")
            assert message_response.status_code == 200, "Failed to create test message."

        # Retrieve chats with a request for 20 chats
        url = f"{self.BASE_URL}/getallchats"
        data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 1,
            "page_size": 20  # Requesting more chats than exist
        }
        logger.info(f"INPUT: Sending request with data:\n{str(data)}")

        response = requests.post(url, json=data)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        # Check for successful response
        assert response.status_code == 200, "Failed to retrieve chats."

        response_data = response.json()
        messages = response_data.get('messages')
        assert isinstance(messages, list), "Expected 'messages' to be a list."

        # Check for the total number of user messages, excluding the initial question
        user_messages = [msg for msg in messages if
                         msg['sender_type'] == 'customer' and msg['message'] not in ["Initial question",
                                                                                     "You will get the correct answer once AI is integrated."]]

        assert len(user_messages) == len(messages_to_add), (
            f"Expected {len(messages_to_add)} user messages, but got {len(user_messages)}. "
            f"Retrieved messages: {user_messages}"
        )

        # Verify that all added messages are in the response
        for expected_message in messages_to_add:
            assert any(msg.get('message') == expected_message for msg in user_messages), (
                f"Expected message '{expected_message}' not found in the response."
            )

        logger.info("=== Test Case 13: Retrieve 20 chats when only 5 exist Completed ===\n")

    def test_retrieval_with_specific_pagination(self):
        """Test case: Add 5 chats, retrieve 2 chats on the first page, 2 on the second, and 1 on the third."""
        logger.info("=== Test Case 14: Specific Pagination Retrieval ===")

        # Step 2: Create a new chat to ensure valid chat_id
        create_chat_url = f"{self.BASE_URL}/chat"
        initial_question = "initial_question"
        create_chat_data = {
            "customer_guid": self.valid_customer_guid,
            "question": initial_question
        }
        response = requests.post(create_chat_url, json=create_chat_data)
        logger.info(f"Chat creation response status: {response.status_code}, {response.text}")
        self.assertEqual(response.status_code, 200, "Failed to create a new chat.")

        # Get the new chat_id
        self.valid_chat_id = response.json().get("chat_id")
        logger.info(f"Received valid chat_id: {self.valid_chat_id}")

        # Step 3: Add 5 chat messages with unique content
        add_chat_url = f"{self.BASE_URL}/chat"
        messages_to_add = [
            "You will get the correct answer once AI is integrated.",
            "You will get the correct answer once AI is integrated.",
            "You will get the correct answer once AI is integrated.",
            "You will get the correct answer once AI is integrated.",
            "You will get the correct answer once AI is integrated."
        ]

        logger.info(f"Adding 5 messages to chat_id: {self.valid_chat_id}")
        for idx, message in enumerate(messages_to_add, start=1):
            message_data = {
                "customer_guid": self.valid_customer_guid,
                "chat_id": self.valid_chat_id,
                "question": message
            }
            response = requests.post(add_chat_url, json=message_data)
            logger.info(f"Add Message #{idx}: Response: {response.status_code}, {response.text}")
            self.assertEqual(response.status_code, 200, f"Failed to add message #{idx}")

        logger.info("=== All 5 messages added successfully ===")

        # Step 4: Retrieve 2 chats on the first page
        get_chats_url = f"{self.BASE_URL}/getallchats"

        # Page 1
        page_1_data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 1,
            "page_size": 2
        }
        logger.info(f"Retrieving page 1 with data: {page_1_data}")
        response_page_1 = requests.post(get_chats_url, json=page_1_data)
        logger.info(f"Get Chats Response Page 1: {response_page_1.status_code}, {response_page_1.text}")
        self.assertEqual(response_page_1.status_code, 200, "Failed to retrieve chats for page 1")

        messages_page_1 = response_page_1.json().get("messages", [])
        self.assertEqual(len(messages_page_1), 2, "Expected 2 messages on page 1")

        # Page 2
        page_2_data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 2,
            "page_size": 2
        }
        logger.info(f"Retrieving page 2 with data: {page_2_data}")
        response_page_2 = requests.post(get_chats_url, json=page_2_data)
        logger.info(f"Get Chats Response Page 2: {response_page_2.status_code}, {response_page_2.text}")
        self.assertEqual(response_page_2.status_code, 200, "Failed to retrieve chats for page 2")

        messages_page_2 = response_page_2.json().get("messages", [])
        self.assertEqual(len(messages_page_2), 2, "Expected 2 messages on page 2")

        # Page 3
        page_3_data = {
            "customer_guid": self.valid_customer_guid,
            "chat_id": self.valid_chat_id,
            "page": 3,
            "page_size": 1
        }
        logger.info(f"Retrieving page 3 with data: {page_3_data}")
        response_page_3 = requests.post(get_chats_url, json=page_3_data)
        logger.info(f"Get Chats Response Page 3: {response_page_3.status_code}, {response_page_3.text}")
        self.assertEqual(response_page_3.status_code, 200, "Failed to retrieve chats for page 3")

        messages_page_3 = response_page_3.json().get("messages", [])
        self.assertEqual(len(messages_page_3), 1, "Expected 1 message on page 3")

        # Step 5: Verify the messages retrieved
        expected_messages = [
            messages_to_add[0],  # First message
            messages_to_add[1],  # Second message
            messages_to_add[2],  # Third message
            messages_to_add[3],  # Fourth message
            messages_to_add[4]  # Fifth message
        ]

        # Check messages from page 1
        for idx, expected_message in enumerate(expected_messages[:2]):
            self.assertEqual(messages_page_1[idx]['message'], expected_message,
                             f"Message on page 1 at index {idx} does not match expected message.")

        # Check messages from page 2
        for idx, expected_message in enumerate(expected_messages[2:4]):
            self.assertEqual(messages_page_2[idx]['message'], expected_message,
                             f"Message on page 2 at index {idx} does not match expected message.")

        # Check message from page 3
        self.assertEqual(messages_page_3[0]['message'], expected_messages[4],
                         "Message on page 3 does not match expected message.")

        logger.info("=== Test Case 14: Specific Pagination Retrieval Completed ===")


if __name__ == "__main__":
    unittest.main()
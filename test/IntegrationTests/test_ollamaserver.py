import unittest
import requests
import logging
import os
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAPI(unittest.TestCase):
    def setUp(self):
        """Set up reusable test configurations."""
        logger.info("=== Setting up test case ===")
        self.BASE_URL = f"http://{os.getenv('OLLAMA_SERVICE_HOST')}:{os.getenv('OLLAMA_PORT')}"  # Example URL, adjust as needed
        self.generate_endpoint = "/api/generate"
        self.valid_model = "llama3.2:3b"
        self.valid_prompt = "What is the capital of France?"

        # Verify the server is running
        try:
            logger.info(f"Checking if server is reachable at {self.BASE_URL}")
            response = requests.get(f"{self.BASE_URL}")
            if response.status_code == 200:
                logger.info("Ollama is running")
            else:
                self.fail(f"Ollama server is reachable but returned unexpected status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.fail(f"Failed to connect to the server: {str(e)}")

    def send_post_request(self, endpoint, payload):
        """Helper function to send a POST request and handle JSON response."""
        url = f"{self.BASE_URL}{endpoint}"
        logger.info(f"Sending POST request to {url} with payload: {payload}")
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)
            try:
                response_data = response.json()
                logger.info(f"Received response: {response.status_code}, {response_data}")
                return response
            except ValueError:
                logger.error(f"Invalid JSON received: {response.text}")
                self.fail(f"Expected JSON response but received: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            self.fail(f"Request to {url} failed with error: {str(e)}")

    # Positive Test Cases
    def test_generate_valid_prompt(self):
        """Test generating a response with a valid prompt."""
        logger.info("=== Starting Positive Test Case 1: Generate Valid Prompt ===")
        payload = {
            "model": self.valid_model,
            "prompt": self.valid_prompt,
            "stream": False
        }
        response = self.send_post_request(self.generate_endpoint, payload)

        self.assertEqual(response.status_code, 200, "Expected status code 200.")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key.")

        # Check if the response contains the word 'Paris'
        if "Paris" in response_json["response"]:
            logger.info("The response contains 'Paris' as expected.")
        else:
            # If 'Paris' is not found, ensure the model still generated some text
            self.assertTrue(
                len(response_json["response"]) > 0,
                "The response should contain some text even if 'Paris' is not present."
            )
            logger.warning("The response does not contain 'Paris', but valid text was generated.")

        logger.info("Test Case Passed 1: Valid prompt generated a response.\n")


    # Edge Test Cases
    @unittest.skip("Skipping this test temporarily.")
    def test_generate_long_prompt(self):
        """Test generating a response with a very long prompt."""
        logger.info("=== Starting Edge Test Case 2: Generate Long Prompt ===")
        long_prompt = "Explain the theory of Electricity. " * 500  # Creating a long prompt
        payload = {"model": "llama3.2:3b", "prompt": long_prompt, "stream": False}
        response = self.send_post_request(self.generate_endpoint, payload)

        self.assertEqual(response.status_code, 200, "Expected status code 200.")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key.")
        self.assertTrue(len(response_json["response"]) > 0, "Response should not be empty.")
        logger.info("Test Case Passed 2: Long prompt generated a valid response.\n")

    def test_generate_special_characters(self):
        """Test generating a response with special characters in the prompt."""
        logger.info("=== Starting Edge Test Case 3: Generate Special Characters ===")
        payload = {
            "model": "llama3.2:3b",
            "prompt": "!@#$%^&*() What is this?",
            "stream": False
        }
        response = self.send_post_request(self.generate_endpoint, payload)

        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key")
        logger.info("Test Case Passed 3: Prompt with special characters generated a valid response.\n")

    def test_generate_numeric_prompt(self):
        """Test generating a response with a numeric-only prompt."""
        logger.info("=== Starting Edge Test Case 4: Generate Numeric Prompt ===")
        payload = {
            "model": "llama3.2:3b",
            "prompt": "1234567890",
            "stream": False
        }
        response = self.send_post_request(self.generate_endpoint, payload)

        # Test for allowing numeric prompts
        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key.")
        self.assertTrue(len(response_json["response"]) > 0, "Response should not be empty.")
        logger.info("Test Case Passed 4: Numeric-only prompt generated a valid response.\n")


if __name__ == "__main__":
    unittest.main()

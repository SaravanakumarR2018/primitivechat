import unittest
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAPI(unittest.TestCase):
    def setUp(self):
        """Set up reusable test configurations."""
        logger.info("=== Setting up test case ===")
        self.BASE_URL = "http://localhost:11434"  # Example URL, adjust as needed
        self.pull_endpoint = "/api/pull"
        self.generate_endpoint = "/api/generate"
        self.valid_model = "llama3.2:3b"
        self.valid_prompt = "What is the capital of France?"
        self.streaming_prompt = "Explain the theory of relativity in detail."

        # Verify the server is running
        try:
            logger.info(f"Checking if server is reachable at {self.BASE_URL}")
            response = requests.get(f"{self.BASE_URL}")
            if response.status_code == 200:
                logger.info("Ollama server is up and running.")
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
    def test_model_pull_valid(self):
        """Test pulling a valid model."""
        logger.info("=== Starting Positive Test Case: Pull Valid Model ===")
        payload = {"name": self.valid_model}
        response = self.send_post_request(self.pull_endpoint, payload)

        self.assertEqual(response.status_code, 200, "Expected status code 200.")
        response_json = response.json()
        self.assertIn("status", response_json, "Response JSON should contain 'status' key.")
        self.assertEqual(response_json["status"], "success", "Expected pull status to be 'success'.")
        logger.info("Test Case Passed: Model pull request succeeded.\n")

    def test_generate_valid_prompt(self):
        """Test generating a response with a valid prompt."""
        logger.info("=== Starting Positive Test Case: Generate Valid Prompt ===")
        payload = {
            "model": self.valid_model,
            "prompt": self.valid_prompt,
            "stream": False
        }
        response = self.send_post_request(self.generate_endpoint, payload)

        self.assertEqual(response.status_code, 200, "Expected status code 200.")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key.")
        self.assertIn("Paris", response_json["response"], "Expected response to contain 'Paris'.")
        logger.info("Test Case Passed: Valid prompt generated a correct response.\n")

    def test_generate_with_streaming(self):
        """Test generating a response with streaming enabled."""
        logger.info("=== Starting Edge Test Case: Generate with Streaming ===")
        payload = {
            "model": self.valid_model,
            "prompt": self.streaming_prompt,
            "stream": True
        }
        response = self.send_post_request(self.generate_endpoint, payload)

        self.assertEqual(response.status_code, 200, "Expected status code 200.")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key.")
        self.assertTrue(len(response_json["response"]) > 0, "Response should not be empty.")
        logger.info("Test Case Passed: Streaming response generated successfully.\n")


if __name__ == "__main__":
    unittest.main()

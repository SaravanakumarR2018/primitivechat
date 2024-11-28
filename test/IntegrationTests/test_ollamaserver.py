import unittest
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestOllamaServer(unittest.TestCase):
    BASE_URL = "http://localhost:11434"

    def send_post_request(self, endpoint, payload):
        """Helper function to send a POST request and return the response."""
        url = f"{self.BASE_URL}{endpoint}"
        logger.info(f"Sending POST request to {url} with payload: {payload}")
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Raises an error for bad responses (4xx and 5xx)
            logger.info(f"Received response: {response.status_code}, {response.json()}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if 'response' in locals() and response is not None:
                logger.error(f"Response content: {response.text}")
            raise

    # Positive Test Cases

    def test_model_pull_valid(self):
        """Test pulling a valid model."""
        logger.info("=== Starting Positive Test Case 1: Pull Valid Model ===")
        payload = {"name": "llama3.2:3b"}
        response = self.send_post_request("/api/pull", payload)

        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("status", response_json, "Response JSON should contain 'status' key")
        self.assertEqual(response_json["status"], "success", "Expected status to be 'success'")
        logger.info("Test Case Passed: Model pull request succeeded with status code 200.\n")

    def test_generate_valid_prompt(self):
        """Test generating a response with a valid prompt."""
        logger.info("=== Starting Positive Test Case 2: Generate Valid Prompt ===")
        payload = {
            "model": "llama3.2:3b",
            "prompt": "What is the capital of France?",
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key")
        self.assertIn("Paris", response_json["response"], "Expected response to contain 'Paris'")
        logger.info("Test Case Passed: Valid prompt generated a correct response.\n")

    def test_generate_streaming(self):
        """Test generating a response with streaming enabled."""
        logger.info("=== Starting Positive Test Case 3: Generate with Streaming ===")
        payload = {
            "model": "llama3.2:3b",
            "prompt": "Explain the theory of relativity in detail.",
            "stream": True
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key")
        self.assertTrue(len(response_json["response"]) > 0, "Response should not be empty")
        logger.info("Test Case Passed: Streaming response generated successfully.\n")

    # Negative Test Cases

    def test_model_pull_invalid(self):
        """Test pulling a model with an invalid name."""
        logger.info("=== Starting Negative Test Case 4: Pull Invalid Model ===")
        payload = {"name": "nonexistent_model"}
        response = self.send_post_request("/api/pull", payload)

        self.assertEqual(response.status_code, 400, f"Expected status code 400 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("error", response_json, "Response JSON should contain 'error' key")
        self.assertEqual(response_json["error"], "Model not found", "Expected error message to be 'Model not found'")
        logger.info("Test Case Passed: Invalid model pull request returned expected error.\n")

    def test_generate_invalid_model(self):
        """Test generating a response with an invalid model."""
        logger.info("=== Starting Negative Test Case 5: Generate with Invalid Model ===")
        payload = {
            "model": "nonexistent_model",
            "prompt": "What is the capital of France?",
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 400, f"Expected status code 400 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("error", response_json, "Response JSON should contain 'error' key")
        self.assertEqual(response_json["error"], "Model not found", "Expected error message to be 'Model not found'")
        logger.info("Test Case Passed: Invalid model name generated the expected error.\n")

    def test_generate_missing_prompt(self):
        """Test generating a response with a missing prompt."""
        logger.info("=== Starting Negative Test Case 6: Generate Missing Prompt ===")
        payload = {
            "model": "llama3.2:3b",
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 400, f"Expected status code 400 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("error", response_json, "Response JSON should contain 'error' key")
        self.assertEqual(response_json["error"], "Missing prompt", "Expected error message to be 'Missing prompt'")
        logger.info("Test Case Passed: Missing prompt generated the expected error.\n")

    # Edge Test Cases

    def test_generate_long_prompt(self):
        """Test generating a response with a very long prompt."""
        logger.info("=== Starting Edge Test Case 7: Generate Long Prompt ===")
        long_prompt = "Explain the theory of relativity. " * 500  # Very long prompt
        payload = {
            "model": "llama3.2:3b",
            "prompt": long_prompt,
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key")
        self.assertTrue(len(response_json["response"]) > 0, "Response should not be empty")
        logger.info("Test Case Passed: Long prompt generated a valid response.\n")

    def test_generate_special_characters(self):
        """Test generating a response with special characters in the prompt."""
        logger.info("=== Starting Edge Test Case 8: Generate Special Characters ===")
        payload = {
            "model": "llama3.2:3b",
            "prompt": "!@#$%^&*() What is this?",
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("response", response_json, "Response JSON should contain 'response' key")
        logger.info("Test Case Passed: Prompt with special characters generated a valid response.\n")

    def test_generate_numeric_prompt(self):
        """Test generating a response with a numeric-only prompt."""
        logger.info("=== Starting Edge Test Case 9: Generate Numeric Prompt ===")
        payload = {
            "model": "llama3.2:3b",
            "prompt": "1234567890",
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 400, f"Expected status code 400 but got {response.status_code}")
        response_json = response.json()
        self.assertIn("error", response_json, "Response JSON should contain 'error' key")
        self.assertEqual(response_json["error"], "Invalid prompt", "Expected error message to be 'Invalid prompt'")
        logger.info("Test Case Passed: Numeric-only prompt generated the expected error.\n")


if __name__ == "__main__":
    unittest.main()

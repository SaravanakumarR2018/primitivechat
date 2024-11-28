import unittest
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestOllamaServer(unittest.TestCase):
    BASE_URL = "http://localhost:11434"  # Change to your local server URL and port

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
            if 'response' in locals():
                logger.error(f"Response content: {response.text}")  # Log raw response
            raise

    # Positive Test Cases
    def test_pull_model(self):
        """Test pulling a valid model."""
        logger.info("=== Starting Test Case: Pull Model ===")

        payload = {"name": "llama3.2:3b"}
        response = self.send_post_request("/api/pull", payload)

        self.assertEqual(response.status_code, 200, "Expected status code 200 for pulling model")
        self.assertIn("message", response.json(), "Response JSON does not contain 'message' key")
        self.assertEqual(response.json().get("message"), "Model pulled successfully.", "Expected success message.")

        logger.info("=== Test Case Completed ===\n")

    def test_generate_response(self):
        """Test generating a response from the model."""
        logger.info("=== Starting Test Case: Generate Response ===")

        payload = {
            "model": "llama3.2:3b",
            "prompt": "Is the sky blue? Give one word as an answer. Answer as either True or False.",
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 200, "Expected status code 200 for generating response")
        self.assertIn("response", response.json(), "Response JSON does not contain 'response' key")

        logger.info("=== Test Case Completed ===\n")

    # Negative Test Cases
    def test_pull_invalid_model(self):
        """Test pulling an invalid model."""
        logger.info("=== Starting Test Case: Pull Invalid Model ===")

        payload = {"name": "invalid_model_name"}
        response = self.send_post_request("/api/pull", payload)

        self.assertEqual(response.status_code, 404, "Expected status code 404 for pulling invalid model")
        self.assertIn("error", response.json(), "Response JSON does not contain 'error' key")

        logger.info("=== Test Case Completed ===\n")

    def test_generate_response_invalid_model(self):
        """Test generating a response from an invalid model."""
        logger.info("=== Starting Test Case: Generate Response Invalid Model ===")

        payload = {
            "model": "invalid_model_name",
            "prompt": "Is the sky blue?",
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 400, "Expected status code 400 for generating response with invalid model")
        self.assertIn("error", response.json(), "Response JSON does not contain 'error' key")

        logger.info("=== Test Case Completed ===\n")

    def test_generate_response_missing_prompt(self):
        """Test generating a response with a missing prompt."""
        logger.info("=== Starting Test Case: Generate Response Missing Prompt ===")

        payload = {
            "model": "llama3.2:3b",
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 400, "Expected status code 400 for missing prompt")
        self.assertIn("error", response.json(), "Response JSON does not contain 'error' key")

        logger.info("=== Test Case Completed ===\n")

    # Edge Test Cases
    def test_pull_model_empty_name(self):
        """Test pulling a model with an empty name."""
        logger.info("=== Starting Test Case: Pull Model Empty Name ===")

        payload = {"name": ""}
        response = self.send_post_request("/api/pull", payload)

        self.assertEqual(response.status_code, 400, " Expected status code 400 for pulling model with empty name")
        self.assertIn("error", response.json(), "Response JSON does not contain 'error' key")

        logger.info("=== Test Case Completed ===\n")

    def test_generate_response_empty_prompt(self):
        """Test generating a response with an empty prompt."""
        logger.info("=== Starting Test Case: Generate Response Empty Prompt ===")

        payload = {
            "model": "llama3.2:3b",
            "prompt": "",
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 400, "Expected status code 400 for empty prompt")
        self.assertIn("error", response.json(), "Response JSON does not contain 'error' key")

        logger.info("=== Test Case Completed ===\n")

    def test_generate_response_large_prompt(self):
        """Test generating a response with a very large prompt."""
        logger.info("=== Starting Test Case: Generate Response Large Prompt ===")

        large_prompt = "A" * 10000  # Example of a very large prompt
        payload = {
            "model": "llama3.2:3b",
            "prompt": large_prompt,
            "stream": False
        }
        response = self.send_post_request("/api/generate", payload)

        self.assertEqual(response.status_code, 200, "Expected status code 200 for large prompt")
        self.assertIn("response", response.json(), "Response JSON does not contain 'response' key")

        logger.info("=== Test Case Completed ===\n")

if __name__ == "__main__":
    unittest.main()
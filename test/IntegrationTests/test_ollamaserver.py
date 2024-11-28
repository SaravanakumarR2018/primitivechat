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
        self.generate_endpoint = "/api/generate"
        self.valid_model = "llama3.2:3b"
        self.valid_prompt = "What is the capital of France?"
        self.streaming_prompt = "Explain the theory of relativity in detail."

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
        """Helper function to send a POST request and handle streaming response."""
        url = f"{self.BASE_URL}{endpoint}"
        logger.info(f"Sending POST request to {url} with payload: {payload}")
        try:
            response = requests.post(url, json=payload, stream=True)  # Enable streaming
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)

            # Handle the streaming response
            try:
                chunks = []
                for chunk in response.iter_lines(decode_unicode=True):
                    if chunk:
                        chunks.append(chunk)
                full_response = ''.join(chunks)  # Combine all chunks into one string
                logger.info(f"Received response: {response.status_code}, {full_response}")

                # If the server responds with a single JSON object, we can parse it.
                try:
                    response_data = response.json()
                    return response_data
                except ValueError:
                    logger.error(f"Invalid JSON received: {full_response}")
                    self.fail(f"Expected JSON response but received: {full_response}")
            except Exception as e:
                logger.error(f"Error processing stream: {e}")
                self.fail(f"Error while handling the streaming response: {str(e)}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            self.fail(f"Request to {url} failed with error: {str(e)}")

    # Positive Test Cases
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

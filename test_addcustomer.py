import unittest
import requests
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAddCustomerAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"

    def test_add_customer(self):
        """Test that a customer can be added successfully."""
        logger.info("Executing test_add_customer: Testing customer addition functionality.")

        url = f"{self.BASE_URL}/addcustomer"
        logger.info(f"Sending POST request to {url}")

        response = requests.post(url)

        # Log the response status code
        logger.info(f"Received response status code: {response.status_code} for URL: {url}")

        # Check if the response is successful
        self.assertEqual(response.status_code, 200, "Expected status code 200 but got {response.status_code}")

        # Check if the response contains customer_guid
        data = response.json()
        logger.info("Processing response data to check for 'customer_guid'.")

        self.assertIn("customer_guid", data, "'customer_guid' not found in response data.")
        logger.info("'customer_guid' found in response data, verifying its type.")

        self.assertIsInstance(data["customer_guid"], str, "'customer_guid' is not a string.")

        logger.info("Test completed successfully for test_add_customer.")

if __name__ == "__main__":
    unittest.main()

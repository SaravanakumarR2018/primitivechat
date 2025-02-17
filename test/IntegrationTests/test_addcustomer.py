import sys
import unittest
import logging
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.backend.utils.api_utils import add_customer

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAddCustomerAPI(unittest.TestCase):
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT', 8000)}"

    def test_add_customer(self):
        """Test that a customer can be added successfully."""
        logger.info("Executing test_add_customer: Testing customer addition functionality.")

        data = add_customer("test_org_123")

        logger.info("Processing response data to check for 'customer_guid'.")

        self.assertIn("customer_guid", data, "'customer_guid' not found in response data.")
        logger.info("'customer_guid' found in response data, verifying its type.")

        self.assertIsInstance(data["customer_guid"], str, "'customer_guid' is not a string.")

        logger.info("Test completed successfully for test_add_customer.")

if __name__ == "__main__":
    unittest.main()

import logging
import os
import unittest

from utils.api_utils import add_customer

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAddCustomerAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def test_add_customer(self):
        """Test that a customer can be added successfully."""
        logger.info("Executing test_add_customer: Testing customer addition functionality.")
        start_org_id = "test_org"
        data = add_customer(start_org_id)

        logger.info("Processing response data to check for 'customer_guid'.")

        self.assertIn("customer_guid", data, "'customer_guid' not found in response data.")
        self.assertIn("org_id", data, "'org_id' not found in response data.")
        logger.info("'customer_guid' and 'org_id' found in response data, verifying their types.")

        self.assertIsInstance(data["customer_guid"], str, "'customer_guid' is not a string.")
        self.assertIsInstance(data["org_id"], str, "'org_id' is not a string.")

        self.assertTrue(data["org_id"].startswith(start_org_id), f"org_id does not start with {start_org_id}")

        logger.info("Test completed successfully for test_add_customer.")

if __name__ == "__main__":
    unittest.main()

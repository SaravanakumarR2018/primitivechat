import unittest
import requests
import logging
import docker
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestCustomFieldAPI(unittest.TestCase):
    BASE_URL = "http://localhost:8000"
    MYSQL_CONTAINER_NAME = "mysql_db"

    def setUp(self):
        """Setup function to initialize valid customer GUID."""
        logger.info("=== Initializing test setup ===")
        self.docker_client = docker.from_env()

        # Ensure MySQL container is running
        mysql_container = self.docker_client.containers.get(self.MYSQL_CONTAINER_NAME)
        if mysql_container.status != "running":
            logger.info("Starting MySQL container for tests.")
            mysql_container.start()

        # Assuming an endpoint `/addcustomer` to create a new customer
        customer_url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(customer_url)
        self.assertEqual(response.status_code, 200, "Failed to create customer")
        self.valid_customer_guid = response.json().get("customer_guid")
        logger.info(f"Valid customer_guid initialized: {self.valid_customer_guid}")

    def test_add_valid_custom_field(self):
        """Test adding a valid custom field."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "test_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        logger.info(f"Testing valid custom field addition with data: {data}")
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200, "Failed to add custom field")
        response_data = response.json()
        self.assertEqual(response_data["field_name"], "test_field")
        logger.info("Test case for valid custom field addition passed.")

    def test_add_custom_field_missing_required_field(self):
        """Test adding a custom field with missing required field."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "missing_required_field",
            "field_type": "VARCHAR(255)"
            # 'required' field is missing
        }
        logger.info(f"Testing missing 'required' field with data: {data}")
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 422, "Missing required field should result in 422")
        self.assertIn("field required", response.text.lower())
        logger.info("Test case for missing required field passed.")

    def test_add_custom_field_invalid_customer_guid(self):
        """Test adding a custom field with invalid customer_guid."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": "256128e2-b963-4019-b870-d6e82db0d631", # Invalid or random customer_guid
            "field_name": "test_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }
        logger.info(f"Testing invalid customer GUID with data: {data}")
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 400, "Invalid customer_guid should result in 400")
        self.assertIn("Database", response.text)
        logger.info("Test case for invalid customer_guid passed.")

    def test_add_duplicate_custom_field_name(self):
        """Test adding a custom field with a duplicate field name."""
        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "duplicate_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }

        # Add the custom field for the first time
        logger.info(f"Adding initial custom field with data: {data}")
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 200, "Failed to add the initial custom field")

        # Try adding the same custom field again
        logger.info(f"Testing duplicate custom field name with data: {data}")
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 400, "Duplicate field name should result in 400")
        self.assertIn(f"A custom field with this name {data['field_name']} already exists.", response.text)
        logger.info("Test case for duplicate custom field name passed.")

    def test_add_custom_field_invalid_field_type(self):
        """Test adding a custom field with an invalid field type."""
        url = f"{self.BASE_URL}/custom_fields"
        invalid_field_type = "INVALID_TYPE"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "invalid_field_type_test",
            "field_type": invalid_field_type,
            "required": True
        }

        # Attempt to add a custom field with an invalid field type
        logger.info(f"Testing invalid field type with data: {data}")
        response = requests.post(url, json=data)

        # Assert that the API returns a 400 status code
        self.assertEqual(response.status_code, 400, "Invalid field type should result in 400")

        # Assert that the error message contains the expected text
        expected_message = (
            f"Unsupported field type: {invalid_field_type}. "
            "Allowed types are: DATE, INT, VARCHAR(255), MEDIUMTEXT, BOOLEAN"
        )
        self.assertIn(expected_message, response.text, "Expected error message not found in response")

        logger.info("Test case for invalid field type passed.")

    def test_database_server_down(self):
        """Test API response when the database server is down."""
        # Stop MySQL container
        mysql_container = self.docker_client.containers.get(self.MYSQL_CONTAINER_NAME)
        logger.info("Stopping MySQL container to simulate database failure.")
        mysql_container.stop()

        url = f"{self.BASE_URL}/custom_fields"
        data = {
            "customer_guid": self.valid_customer_guid,
            "field_name": "test_field",
            "field_type": "VARCHAR(255)",
            "required": True
        }

        logger.info(f"Testing database server down scenario with data: {data}")
        response = requests.post(url, json=data)
        self.assertEqual(response.status_code, 503, "Expected 503 response when DB is down")
        self.assertIn("The database is currently unreachable. Please try again later.", response.text)
        logger.info("Test case for database server down passed.")

        # Restart MySQL container
        logger.info("Restarting MySQL container after test.")
        mysql_container.start()

    def tearDown(self):
        """Clean up resources if necessary."""
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

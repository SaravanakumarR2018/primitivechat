import unittest
from http import HTTPStatus
import requests
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestListCustomFieldsAPI(unittest.TestCase):
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        """Setup function to initialize valid customer GUID."""
        logger.info("=== Initializing test setup ===")

        # Assuming an endpoint `/addcustomer` to create a new customer
        customer_url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(customer_url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create customer")
        self.valid_customer_guid = response.json().get("customer_guid")
        logger.info(f"Valid customer_guid initialized: {self.valid_customer_guid}")

        logger.info(f"Starting test: {self._testMethodName}")

    def test_list_custom_fields_invalid_customer_guid(self):
        """Test listing custom fields for an invalid customer GUID."""
        invalid_customer_guid = "ae0ae9ed-26dd-4319-9f40-0354990ad101"
        url = f"{self.BASE_URL}/custom_fields?customer_guid={invalid_customer_guid}"
        logger.info(f"Testing invalid customer GUID: {invalid_customer_guid}")
        response = requests.get(url)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Invalid customer GUID should result in 400")
        self.assertIn("Database customer_ae0ae9ed-26dd-4319-9f40-0354990ad101 does not exist", response.text)
        logger.info("Negative test case for invalid customer GUID passed.")

    def test_list_custom_fields_no_fields(self):
        """Test listing custom fields for a customer with no fields."""
        # Create a new customer without adding custom fields
        customer_url = f"{self.BASE_URL}/addcustomer"
        response = requests.post(customer_url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to create customer")
        new_customer_guid = response.json().get("customer_guid")

        url = f"{self.BASE_URL}/custom_fields?customer_guid={new_customer_guid}"
        logger.info(f"Testing customer with no custom fields: {new_customer_guid}")
        response = requests.get(url)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND, "No custom fields should result in 404")
        self.assertIn(f"No custom fields found for customer {new_customer_guid}", response.text)
        logger.info("Negative test case for no custom fields passed.")

    def test_list_multiple_custom_fields_all_types(self):
        """Test listing multiple custom fields of all types for a customer."""
        logger.info("Testing multiple custom fields of all types.")

        # List of custom fields to be added
        custom_fields = [
            {"field_name": "varchar_field", "field_type": "VARCHAR(255)", "required": True},
            {"field_name": "integer_field", "field_type": "INT", "required": False},
            {"field_name": "boolean_field", "field_type": "BOOLEAN", "required": True},
            {"field_name": "date_field", "field_type": "DATETIME", "required": False},
            {"field_name": "text_field", "field_type": "TEXT", "required": True},
            {"field_name": "medium_text_field", "field_type": "MEDIUMTEXT", "required": True},
            {"field_name": "float_field", "field_type": "FLOAT", "required": False}  # Added one more field for testing
        ]

        for field in custom_fields:
            data = {
                "customer_guid": self.valid_customer_guid,
                **field
            }
            response = requests.post(f"{self.BASE_URL}/custom_fields", json=data)
            if response.status_code != HTTPStatus.CREATED:
                logger.error(f"Failed to add field: {field['field_name']}. Server response: {response.text}")
            self.assertEqual(response.status_code, HTTPStatus.CREATED,
                             f"Failed to add field: {field['field_name']}")

        # Fetch the custom fields for the customer again after adding
        url = f"{self.BASE_URL}/custom_fields?customer_guid={self.valid_customer_guid}"
        response = requests.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to list custom fields")
        response_data = response.json()

        # Log the actual response data to see what fields are returned
        logger.info(f"Response data: {response_data}")

        # Verify all added fields are present
        self.assertEqual(len(response_data), len(custom_fields), "Mismatch in number of custom fields")
        for expected_field in custom_fields:
            matching_field = next(
                (field for field in response_data if field["field_name"] == expected_field["field_name"]), None)
            self.assertIsNotNone(matching_field, f"Custom field not found: {expected_field['field_name']}")
            self.assertEqual(matching_field["field_type"], expected_field["field_type"],
                             f"Field type mismatch for {expected_field['field_name']}")
            self.assertEqual(matching_field["required"], expected_field["required"],
                             f"Required flag mismatch for {expected_field['field_name']}")

        logger.info("Test for multiple custom fields of all types passed.")

    def _add_50_custom_fields(self):
        """Test adding 50 custom fields to a customer."""
        logger.info("Adding 50 custom fields to the customer.")

        # Create a list of 50 custom fields with alternating required values
        custom_fields = [{"field_name": f"field_{i}", "field_type": "VARCHAR(255)", "required": i % 2 == 0} for i in
                         range(50)]

        # Iterate over each field and send a POST request to add it
        for field in custom_fields:
            data = {
                "customer_guid": self.valid_customer_guid,
                **field
            }
            response = requests.post(f"{self.BASE_URL}/custom_fields", json=data)

            # Log and assert successful creation of each field
            if response.status_code != HTTPStatus.CREATED:
                logger.error(f"Failed to add field: {field['field_name']}. Server response: {response.text}")
            self.assertEqual(response.status_code, HTTPStatus.CREATED,
                             f"Failed to add field: {field['field_name']}")

        logger.info("Successfully added 50 custom fields.")

    def test_pagination_for_custom_fields(self):
        """Test pagination for listing custom fields with different page sizes."""
        logger.info("Testing pagination for custom fields with different page sizes.")

        # Add 50 custom fields for pagination testing
        self._add_50_custom_fields()

        # Different page sizes for testing
        page_sizes = [10, 20, 50]

        for per_page in page_sizes:
            logger.info(f"Testing with per_page={per_page}")

            # Fetch the total number of custom fields to check consistency
            total_fields_url = f"{self.BASE_URL}/custom_fields?customer_guid={self.valid_customer_guid}&page=1&page_size=50"
            total_fields_response = requests.get(total_fields_url)
            self.assertEqual(total_fields_response.status_code, HTTPStatus.OK,
                             f"Failed to fetch total custom fields for per_page={per_page}")
            total_fields_data = total_fields_response.json()

            # Log the total fields count to check if it matches the expected number
            logger.info(f"Total custom fields count: {len(total_fields_data)}")
            self.assertEqual(len(total_fields_data), 50, "Total number of custom fields should be 50")

            # Verify page_number=1 and page_size=60 returns only 50 records
            if per_page == 50:
                oversized_page_url = f"{self.BASE_URL}/custom_fields?customer_guid={self.valid_customer_guid}&page=1&page_size=60"
                oversized_page_response = requests.get(oversized_page_url)
                self.assertEqual(oversized_page_response.status_code, HTTPStatus.OK,
                                 "Failed to fetch data for oversized page_size=60")
                oversized_page_data = oversized_page_response.json()
                logger.info(f"Records returned for page_size=60: {len(oversized_page_data)}")
                self.assertEqual(len(oversized_page_data), 50,
                                 "Expected only 50 records even when page_size=60 was requested")

            # Initialize a list to store all fields across pages
            all_fields = []

            # Fetch multiple pages based on per_page size
            page_num = 1
            while True:
                page_url = f"{self.BASE_URL}/custom_fields?customer_guid={self.valid_customer_guid}&page={page_num}&per_page={per_page}"
                page_response = requests.get(page_url)

                if page_response.status_code == HTTPStatus.NOT_FOUND:
                    logger.info(f"Reached the end of available pages for per_page={per_page}")
                    break

                self.assertEqual(page_response.status_code, HTTPStatus.OK,
                                 f"Failed to fetch page {page_num} for per_page={per_page}")
                page_data = page_response.json()

                # Add the page data to all_fields list
                all_fields.extend(page_data)

                # If the number of fields on the page is less than per_page, it's the last page
                if len(page_data) < per_page:
                    break

                page_num += 1

            # Check if the data from all pages matches the expected fields
            for i, field in enumerate(all_fields):
                self.assertEqual(field["field_name"], f"field_{i}")

    def tearDown(self):
        """Clean up resources if necessary."""
        logger.info(f"Finished test: {self._testMethodName}")
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

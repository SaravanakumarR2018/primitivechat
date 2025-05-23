import logging
import os
import sys
import unittest
from http import HTTPStatus

import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from utils.api_utils import add_customer, create_test_token, create_token_without_org_role, create_token_without_org_id
from src.backend.lib.logging_config import get_primitivechat_logger

# Configure logging
logger = get_primitivechat_logger(__name__)


class TestDeleteCustomFieldAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"
    ORG_ROLE = 'org:admin'

    allowed_custom_field_sql_types = ["VARCHAR(255)", "INT", "BOOLEAN", "DATETIME", "MEDIUMTEXT", "FLOAT", "TEXT"]

    def setUp(self):
        """Setup function to initialize valid customer GUID and custom fields."""
        logger.info("=== Initializing test setup ===")

        # Step 1: Create a new customer
        logger.info("=== Initializing test setup ===")

        self.headers = {}

        # Assuming an endpoint `/addcustomer` to create a new customer
        self.data = add_customer("test_org")
        self.valid_customer_guid = self.data.get("customer_guid")
        self.org_id = self.data.get("org_id")

        # Create Test Token
        self.token = create_test_token(org_id=self.org_id, org_role=self.ORG_ROLE)
        self.headers['Authorization'] = f'Bearer {self.token}'
        logger.info(f"Valid customer_guid initialized: {self.valid_customer_guid}")
        logger.info(f"Starting test: {self._testMethodName}")

    def list_custom_fields(self, expected_fields=None):
        """Reusable function to list all custom fields and optionally validate them."""
        logger.info("Listing all custom fields.")
        url = f"{self.BASE_URL}/custom_fields"
        response = requests.get(url, headers=self.headers)

        if response.status_code == HTTPStatus.NOT_FOUND:
            logger.info(f"No custom fields found for customer {self.valid_customer_guid}")
            return []  # Return an empty list if no custom fields are found
        else:
            self.assertEqual(response.status_code, HTTPStatus.OK, "Failed to list custom fields")
            custom_fields = response.json()

            if expected_fields:
                logger.info("Validating listed custom fields against expected fields.")
                for field in expected_fields:
                    matching_field = next((f for f in custom_fields if f['field_name'] == field['field_name']), None)
                    self.assertIsNotNone(matching_field, f"Expected field {field['field_name']} not found")
                    self.assertEqual(
                        matching_field['field_type'], field['field_type'],
                        f"Field type mismatch for {field['field_name']}. Expected {field['field_type']}, got {matching_field['field_type']}"
                    )

            return custom_fields

    def test_add_and_delete_all_custom_fields(self):
        """Test adding all allowed custom fields, deleting them one by one, and verifying the results."""
        custom_field_url = f"{self.BASE_URL}/custom_fields"

        # Step 1: Add custom fields dynamically
        custom_fields = []
        for i, field_type in enumerate(self.allowed_custom_field_sql_types):
            if field_type.startswith("VARCHAR"):
                field_name = f"varchar_{field_type[7:].replace('(', '').replace(')', '')}_field"
            else:
                field_name = f"{field_type.lower()}_field"

            custom_fields.append({
                "field_name": field_name,
                "field_type": field_type,
                "required": i % 2 == 0
            })

        for field in custom_fields:
            logger.info(f"Adding custom field: {field['field_name']}")
            field_data = {**field}
            response = requests.post(custom_field_url, json=field_data, headers=self.headers)
            self.assertEqual(
                response.status_code,
                HTTPStatus.CREATED,
                f"Failed to add custom field {field['field_name']}"
            )

        # Step 2: Verify all custom fields are added
        initial_fields = self.list_custom_fields()
        self.assertEqual(len(initial_fields), len(custom_fields), "Custom fields count mismatch after addition")

        # Step 3: Delete each custom field one by one and verify
        for field in custom_fields:
            # Define the deletion URL
            url = f"{self.BASE_URL}/custom_fields/{field['field_name']}"
            logger.info(f"Deleting custom field: {field['field_name']}")

            # Perform the deletion
            response = requests.delete(url, headers=self.headers)
            self.assertEqual(response.status_code, HTTPStatus.OK,
                             f"Failed to delete custom field {field['field_name']}")

            # Validate the deletion response
            response_data = response.json()
            self.assertEqual(response_data["field_name"], field["field_name"])
            self.assertEqual(response_data["status"], "deleted")

            # Verify the field is removed from the list
            updated_fields = self.list_custom_fields()
            remaining_field_names = [f["field_name"] for f in updated_fields]
            self.assertNotIn(field["field_name"], remaining_field_names,
                             f"Deleted field {field['field_name']} still present")

        logger.info("Successfully added and deleted all custom fields.")

    def test_delete_custom_field_not_found(self):
        """Test deleting a custom field that doesn't exist."""
        url = f"{self.BASE_URL}/custom_fields/{'non_existent_field'}"
        logger.info("Testing deletion of non-existent custom field.")
        response = requests.delete(url, headers=self.headers)

        self.assertEqual(response.status_code, HTTPStatus.OK, "Expected 200 even when field does not exist")
        response_data = response.json()
        self.assertEqual(response_data["field_name"], "non_existent_field")
        self.assertEqual(response_data["status"], "deleted")
        logger.info("Negative test case for deleting non-existent custom field passed.")

    def test_delete_custom_field_invalid_org_id_or_customer_guid(self):
        """Test deleting a custom field with an invalid customer GUID."""
        invalid_token = create_test_token(org_id="invalid_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}

        url = f"{self.BASE_URL}/custom_fields/{'test_field'}"
        response = requests.delete(url, headers=headers)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST,
                         "Invalid org_id/customer_guid should result in 400")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")

    def test_add_and_delete_one_custom_field(self):
        """Test adding 3 custom fields, deleting one, and verifying the remaining 2 custom fields are present."""

        # Define the API endpoint for adding custom fields
        custom_field_url = f"{self.BASE_URL}/custom_fields"

        # Step 1: Add 3 custom fields
        custom_fields = []
        for i in range(3):
            field_type = "VARCHAR(255)"  # Example field type, you can change as per your allowed field types
            field_name = f"custom_field_{i + 1}"

            custom_fields.append({
                "field_name": field_name,
                "field_type": field_type,
                "required": i % 2 == 0  # Example condition for "required"
            })

        for field in custom_fields:
            logger.info(f"Adding custom field: {field['field_name']}")
            field_data = {**field}
            response = requests.post(custom_field_url, json=field_data, headers=self.headers)
            self.assertEqual(
                response.status_code,
                HTTPStatus.CREATED,
                f"Failed to add custom field {field['field_name']}"
            )

        # Step 2: Verify all 3 custom fields are added
        initial_fields = self.list_custom_fields()
        self.assertEqual(len(initial_fields), len(custom_fields), "Custom fields count mismatch after addition")
        initial_field_names = [f["field_name"] for f in initial_fields]
        for field in custom_fields:
            self.assertIn(field["field_name"], initial_field_names,
                          f"Custom field {field['field_name']} not found in initial list")

        # Step 3: Delete one custom field (let's delete the second one in the list)
        field_to_delete = custom_fields[1]
        url = f"{self.BASE_URL}/custom_fields/{field_to_delete['field_name']}"
        logger.info(f"Deleting custom field: {field_to_delete['field_name']}")

        # Perform the deletion
        response = requests.delete(url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.OK,
                         f"Failed to delete custom field {field_to_delete['field_name']}")

        # Validate the deletion response
        response_data = response.json()
        self.assertEqual(response_data["field_name"], field_to_delete["field_name"])
        self.assertEqual(response_data["status"], "deleted")

        # Step 4: Verify the remaining 2 custom fields are present
        updated_fields = self.list_custom_fields()
        remaining_field_names = [f["field_name"] for f in updated_fields]

        # Verify that the deleted field is no longer present
        self.assertNotIn(field_to_delete["field_name"], remaining_field_names,
                         f"Deleted field {field_to_delete['field_name']} still present")

        # Verify that the other 2 fields are still present
        for field in custom_fields:
            if field["field_name"] != field_to_delete["field_name"]:
                self.assertIn(field["field_name"], remaining_field_names,
                              f"Remaining field {field['field_name']} not found after deletion")

        logger.info("Successfully added 3 custom fields, deleted one, and verified remaining fields.")

    def test_invalid_custom_field_endpoint(self):
        """Test that an invalid custom field API endpoint returns 404 Not Found."""

        # Define the invalid API endpoint URL
        invalid_url = f"{self.BASE_URL}/custom_fields/test_field/random/api/end_point"

        logger.info(f"Testing invalid API endpoint: {invalid_url}")

        # Send a GET request to the invalid URL
        response = requests.get(invalid_url, headers=self.headers)

        # Assert that the response status code is 404 Not Found
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,
                         f"Expected 404 Not Found, but got {response.status_code} for URL: {invalid_url}")

        # Optionally, check that the response contains a message indicating the endpoint does not exist
        response_data = response.json()
        self.assertIn("detail", response_data, "Response should contain a 'detail' key.")
        self.assertEqual(response_data["detail"], "Not Found", "Expected 'Not Found' message in the response.")

        logger.info(f"Successfully validated 404 Not Found response for invalid endpoint: {invalid_url}")

    def test_delete_custom_fields_without_token(self):
        """Test API request without an authentication token."""
        field_to_delete="test_field"
        url = f"{self.BASE_URL}/custom_fields/{field_to_delete}"
        logger.info("Testing API request without token")
        response = requests.delete(url)  # No headers
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Missing token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_delete_custom_fields_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        field_to_delete = "test_field"
        url = f"{self.BASE_URL}/custom_fields/{field_to_delete}"
        headers = {"Authorization": "Bearer corrupted_token"}
        logger.info("Testing API request with corrupted token")
        response = requests.delete(url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_delete_custom_fields_missing_org_id_in_token(self):
        """Test API request where the token does not have an org_id."""
        field_to_delete = "test_field"
        url = f"{self.BASE_URL}/custom_fields/{field_to_delete}"
        token = create_token_without_org_id(org_role=self.ORG_ROLE)  # No org_id
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("Testing API request with missing org_id in token")
        response = requests.delete(url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Missing org_id should result in 400 Bad Request")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_delete_custom_fields_missing_org_role_in_token(self):
        """Test API request where the token does not have an org_role."""
        field_to_delete = "test_field"
        url = f"{self.BASE_URL}/custom_fields/{field_to_delete}"
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        logger.info("Testing API request with missing org_role in token")
        response = requests.delete(url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN, "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_delete_custom_fields_unauthorized_org_role(self):
        headers={}
        # Assuming an endpoint `/addcustomer` to create a new customer
        data = add_customer("test_org")
        valid_customer_guid = data.get("customer_guid")
        org_id = data.get("org_id")

        # Create Test Token for member (not allowed)
        token = create_test_token(org_id=org_id, org_role="org:random_org_role")
        headers['Authorization'] = f'Bearer {token}'

        url = f"{self.BASE_URL}/custom_fields/test_field"

        response = requests.delete(url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN,
                         "Missing org_role should result in 403 Unauthorized")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_delete_custom_fields_invalid_org_id_no_mapped_customer_guid(self):
        """Test API request with an org_id that has no mapped customer_guid."""
        url = f"{self.BASE_URL}/custom_fields/test_field"

        invalid_token = create_test_token(org_id="unmapped_org", org_role=self.ORG_ROLE)
        headers = {"Authorization": f"Bearer {invalid_token}"}
        logger.info("Testing API request with org_id that has no mapped customer_guid")
        response = requests.delete(url, headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST, "Unmapped org_id should result in 400 Bad Request")
        self.assertIn("Database customer_None does not exist", response.text)
        logger.info("Negative test case for invalid org_id/customer_guid passed.")

    def tearDown(self):
        """Clean up resources if necessary."""
        logger.info(f"Finished test: {self._testMethodName}")
        logger.info("=== Test teardown complete ===")

if __name__ == "__main__":
    unittest.main()

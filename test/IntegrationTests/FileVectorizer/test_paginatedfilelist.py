import logging
import os
import unittest
import requests
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from utils.api_utils import add_customer, create_test_token, create_token_without_org_id, create_token_without_org_role
from src.backend.lib.logging_config import log_format

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)


class TestFileListAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        """Setup function to initialize customer, token, and upload files."""
        logger.info("=== Starting setup process ===")

        # Initialize customer and token
        customer_data = add_customer("test_org")
        self.org_id = customer_data.get("org_id")
        self.token = create_test_token(org_id=self.org_id, org_role="org:admin")
        self.headers = {'Authorization': f'Bearer {self.token}'}

        # Upload multiple files for the customer
        self.upload_files(5)  # Upload 5 files
        logger.info("=== Setup process completed ===")

    def upload_files(self, num_files):
        """Helper function to upload multiple files."""
        for i in range(1, num_files + 1):
            test_file = (f"testfile{i}.txt", b"Sample file content")
            files = {"file": test_file}
            upload_response = requests.post(f"{self.BASE_URL}/uploadFile", files=files, headers=self.headers)
            self.assertEqual(upload_response.status_code, 200, f"File upload failed for file {i}")

    def test_valid_pagination(self):
        """Test the API with valid page and page_size parameters."""
        logger.info("Executing test_valid_pagination")

        # Call the /file/list endpoint with valid pagination
        url = f"{self.BASE_URL}/file/list?page=1&page_size=3"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Check if the response is successful
        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")

        # Check if the response contains the correct number of files
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 3, "Expected 3 files in the response")

        # Check if each file has the required fields
        for file in data:
            self.assertIn("fileid", file, "'fileid' not found in response")
            self.assertIn("filename", file, "'filename' not found in response")
            self.assertIn("embeddingstatus", file, "'embeddingstatus' not found in response")

        logger.info("Test completed successfully for test_valid_pagination")

    def test_no_files_found(self):
        """Test the API when no files are found for the customer."""
        logger.info("Executing test_no_files_found")

        # Create a new customer with no files
        customer_data = add_customer("new_test_org")
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}

        # Call the /file/list endpoint for the new customer
        url = f"{self.BASE_URL}/file/list?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Check if the response is successful
        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")

        # Check if the response is an empty list
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 0, "Expected an empty list in the response")

        logger.info("Test completed successfully for test_no_files_found")

    def test_retrieval_with_specific_pagination(self):
        """Test the API with specific page and page_size values."""
        logger.info("Executing test_retrieval_with_specific_pagination")

        # Upload 15 files for testing pagination
        self.upload_files(15)

        # Test with page=2 and page_size=5
        url = f"{self.BASE_URL}/file/list?page=2&page_size=5"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Expect a 200 status code
        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")

        # Check if the response contains 5 files
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 5, "Expected 5 files in the response")

        logger.info("Test completed successfully for test_retrieval_with_specific_pagination")

    def test_retrieve_with_large_page_size(self):
        """Test the API with a large but valid page_size."""
        logger.info("Executing test_retrieve_with_large_page_size")

        url = f"{self.BASE_URL}/file/list?page=1&page_size=100"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Expect a 200 status code
        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")

        # Check if the response contains files
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertTrue(len(data) <= 100, "Expected at most 100 files in the response")

        logger.info("Test completed successfully for test_retrieve_with_large_page_size")

    def test_high_page_number(self):
        """Test the API with a page number higher than the total number of pages."""
        logger.info("Executing test_high_page_number")

        # Call the /file/list endpoint with a high page number
        url = f"{self.BASE_URL}/file/list?page=100&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Expect a 200 status code
        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")

        # Check if the response is an empty list
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 0, "Expected an empty list in the response")

        logger.info("Test completed successfully for test_high_page_number")

    def test_paginated_list_files_without_token(self):
        """Test the API without providing an authentication token."""
        logger.info("Executing test_paginated_list_files_without_token")

        url = f"{self.BASE_URL}/file/list?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url)
        logger.info(f"Received response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 401, "Expected status code 401 for missing token")
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Authentication required", "Unexpected error message")

        logger.info("Test completed successfully for test_paginated_list_files_without_token")

    def test_paginated_list_files_corrupted_token(self):
        """Test the API with a corrupted authentication token."""
        logger.info("Executing test_paginated_list_files_corrupted_token")

        headers = {"Authorization": "Bearer corrupted_token"}
        url = f"{self.BASE_URL}/file/list?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, 401, "Expected status code 401 for corrupted token")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

        logger.info("Test completed successfully for test_paginated_list_files_corrupted_token")

    def test_paginated_list_files_token_without_org_role(self):
        """Test the API with a token missing the org_role claim."""
        logger.info("Executing test_paginated_list_files_token_without_org_role")

        headers = {'Authorization': f'Bearer {create_token_without_org_role(self.org_id)}'}
        url = f"{self.BASE_URL}/file/list?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, 403, "Expected status code 403 for missing org_role")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

        logger.info("Test completed successfully for test_paginated_list_files_token_without_org_role")

    def test_paginated_list_files_token_without_org_id(self):
        """Test the API with a token missing the org_id claim."""
        logger.info("Executing test_paginated_list_files_token_without_org_id")

        headers = {'Authorization': f'Bearer {create_token_without_org_id("org:admin")}'}
        url = f"{self.BASE_URL}/file/list?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, 400, "Expected status code 400 for missing org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

        logger.info("Test completed successfully for test_paginated_list_files_token_without_org_id")

    def test_paginated_list_files_no_mapping_customer_guid(self):
        """Test the API with an org_id that has no mapping to a customer_guid."""
        logger.info("Executing test_paginated_list_files_no_mapping_customer_guid")

        # Create a new org_id without mapping it to a customer_guid
        org_id = "unmapped_org_id"
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}
        url = f"{self.BASE_URL}/file/list?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, 404, "Expected status code 404 for unmapped org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided", "Unexpected error message")

        logger.info("Test completed successfully for test_paginated_list_files_no_mapping_customer_guid")

if __name__ == "__main__":
    unittest.main()

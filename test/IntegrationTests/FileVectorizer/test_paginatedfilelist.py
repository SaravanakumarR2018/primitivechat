import logging
import os
import unittest
import requests
import sys
import uuid
from http import HTTPStatus
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from utils.api_utils import add_customer, create_test_token, create_token_without_org_id, create_token_without_org_role
from src.backend.lib.logging_config import get_primitivechat_logger

# Set up logging configuration
logger = get_primitivechat_logger(__name__)


class TestFileListAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        """Setup function to initialize customer, token, and upload files."""
        logger.info(f"=== Starting setup process for test: {self._testMethodName} ===")

        # Initialize customer and token
        customer_data = add_customer("test_org")
        self.org_id = customer_data.get("org_id")
        self.token = create_test_token(org_id=self.org_id, org_role="org:admin")
        self.headers = {'Authorization': f'Bearer {self.token}'}

        # Upload 50 files for the customer
        self.upload_files(50)
        logger.info(f"=== Setup process completed for test: {self._testMethodName} ===")

    def upload_files(self, num_files):
        """Helper function to upload multiple files with unique filenames."""
        for i in range(1, num_files + 1):
            unique_filename = f"testfile_{uuid.uuid4().hex}.txt"
            test_file = (unique_filename, b"Sample file content")
            files = {"file": test_file}
            upload_response = requests.post(f"{self.BASE_URL}/uploadFile", files=files, headers=self.headers)
            self.assertEqual(upload_response.status_code, HTTPStatus.OK, f"File upload failed for file {i}")

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
        self.assertEqual(response.status_code, HTTPStatus.OK, f"Expected status code 200 but got {response.status_code}")

        # Check if the response is an empty list
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 0, "Expected an empty list in the response")

    def test_high_page_number(self):
        logger.info("Executing test_high_page_number")

        # Call the /file/list endpoint with a high page number
        url = f"{self.BASE_URL}/file/list?page=100&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Expect a 200 status code
        self.assertEqual(response.status_code, HTTPStatus.OK, f"Expected status code 200 but got {response.status_code}")

        # Check if the response is an empty list
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 0, "Expected an empty list in the response")

    def test_valid_pagination(self):
        """Test the API with valid page and page_size parameters."""
        logger.info("Executing test_valid_pagination")

        # Call the /file/list endpoint with valid pagination
        url = f"{self.BASE_URL}/file/list?page=1&page_size=3"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Check if the response is successful
        self.assertEqual(response.status_code, HTTPStatus.OK, f"Expected status code 200 but got {response.status_code}")

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
        self.assertEqual(response.status_code, HTTPStatus.OK, f"Expected status code 200 but got {response.status_code}")

        # Check if the response contains 5 files
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 5, "Expected 5 files in the response")

    def test_retrieve_with_large_page_size(self):
        """Test the API with a large but valid page_size."""
        logger.info("Executing test_retrieve_with_large_page_size")

        url = f"{self.BASE_URL}/file/list?page=1&page_size=100"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Expect a 200 status code
        self.assertEqual(response.status_code, HTTPStatus.OK, f"Expected status code 200 but got {response.status_code}")

        # Check if the response contains files
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertTrue(len(data) <= 100, "Expected at most 100 files in the response")

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

    def test_pagination_for_files(self):
        """Test pagination for files with different page sizes."""
        logger.info("Executing test_pagination_for_files")

        # Define different page sizes for pagination testing
        page_sizes = [10, 20, 30]

        for page_size in page_sizes:
            logger.info(f"Testing with page_size={page_size}")

            all_files = []

            # Fetch files page by page
            page_num = 1
            while True:
                page_url = f"{self.BASE_URL}/file/list?page={page_num}&page_size={page_size}"
                response = requests.get(page_url, headers=self.headers)
                if response.status_code == HTTPStatus.NOT_FOUND:
                    logger.info(f"Reached the end of available pages for page_size={page_size}")
                    break
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f"Failed to fetch page {page_num} for page_size={page_size}"
                )
                # Parse the response JSON
                page_data = response.json()
                all_files.extend(page_data)
                if len(page_data) < page_size:
                    break
                page_num += 1

            # Validate the total number of files retrieved
            self.assertEqual(
                len(all_files),
                50,
                f"Total files retrieved with page_size={page_size} should be 50"
            )

            # Validate that each file has the required fields
            for file in all_files:
                self.assertIn("fileid", file, "'fileid' not found in response")
                self.assertIn("filename", file, "'filename' not found in response")
                self.assertIn("embeddingstatus", file, "'embeddingstatus' not found in response")

            logger.info(f"Pagination test completed successfully for page_size={page_size}")

    def tearDown(self):
        """Teardown function to log the completion of the test case."""
        logger.info(f"=== Finished execution of test: {self._testMethodName} ===")

if __name__ == "__main__":
    unittest.main()

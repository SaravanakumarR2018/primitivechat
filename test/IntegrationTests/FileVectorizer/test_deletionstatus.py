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

@unittest.skip("Skipping all test cases in this class temporarily")
class TestFileDeletionStatusAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        logger.info(f"=== Starting setup process for test: {self._testMethodName} ===")

        # Initialize customer and token
        customer_data = add_customer("test_org")
        self.org_id = customer_data.get("org_id")
        self.token = create_test_token(org_id=self.org_id, org_role="org:admin")
        self.headers = {'Authorization': f'Bearer {self.token}'}

        # Upload and mark exactly 50 files for deletion
        self.upload_files(50)
        self.mark_files_for_deletion()
        logger.info(f"=== Setup process completed for test: {self._testMethodName} ===")

    def upload_files(self, num_files):
        """Helper function to upload multiple files with unique filenames."""
        self.uploaded_filenames = []
        for i in range(1, num_files + 1):
            unique_filename = f"testfile_{uuid.uuid4().hex}.txt"
            test_file = (unique_filename, b"Sample file content")
            files = {"file": test_file}
            upload_response = requests.post( f"{self.BASE_URL}/uploadFile", files=files, headers=self.headers)
            self.assertEqual(upload_response.status_code,HTTPStatus.OK, f"File upload failed for file {i}")
            self.uploaded_filenames.append(unique_filename)

    def mark_files_for_deletion(self):
        """Helper function to mark uploaded files for deletion."""
        for filename in self.uploaded_filenames:
            delete_response = requests.delete(f"{self.BASE_URL}/deletefile", params={"filename": filename}, headers=self.headers)
            self.assertIn(delete_response.status_code, [HTTPStatus.OK, HTTPStatus.ACCEPTED],f"Failed to mark file {filename} for deletion")

    def test_valid_pagination_for_delete_list_files(self):
        logger.info("Executing test_valid_pagination_for_delete_list_files")

        url = f"{self.BASE_URL}/files/deletionstatus?page=1&page_size=5"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, HTTPStatus.OK,
                         f"Expected status code 200 but got {response.status_code}")
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 5, "Expected 5 files in the response")

        # Check if each file has the required fields
        for file in data:
            self.assertIn("file_id", file, "'file_id' not found in response")
            self.assertIn("filename", file, "'filename' not found in response")
            self.assertIn("deletion_status", file, "'deletion_status' not found in response")

    def test_no_files_found_for_delete_list_files(self):
        logger.info("Executing test_no_files_found_for_delete_list_files")

        # Create new customer with no files
        customer_data = add_customer("new_test_org_deletion")
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}

        url = f"{self.BASE_URL}/files/deletionstatus?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, HTTPStatus.OK,f"Expected status code 200 but got {response.status_code}")
        self.assertEqual(len(response.json()), 0, "Expected an empty list in the response")

    def test_high_page_number(self):
        logger.info("Executing test_high_page_number")

        url = f"{self.BASE_URL}/files/deletionstatus?page=100&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, HTTPStatus.OK,
                         f"Expected status code 200 but got {response.status_code}")
        self.assertEqual(len(response.json()), 0, "Expected an empty list in the response")

    def test_retrieval_with_specific_pagination(self):
        logger.info("Executing test_retrieval_with_specific_pagination")

        # Upload 15 files and mark them for deletion
        self.upload_files(15)
        self.mark_files_for_deletion()
        logger.info("Uploaded and marked 15 files for deletion")

        # Test with page=2 and page_size=5
        url = f"{self.BASE_URL}/files/deletionstatus?page=2&page_size=5"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Expect a 200 status code
        self.assertEqual(response.status_code, HTTPStatus.OK,f"Expected status code 200 but got {response.status_code}")

        # Check if the response contains 5 files
        data = response.json()
        logger.info(f"Received {len(data)} files in response")

        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 5, "Expected 5 files in the response")

        # Verify each file has required fields and valid status
        for file in data:
            self.assertIn("file_id", file, "'file_id' not found in response")
            self.assertIn("filename", file, "'filename' not found in response")
            self.assertIn("deletion_status", file, "'deletion_status' not found in response")

    def test_retrieve_with_large_page_size(self):
        logger.info("===== STARTING test_retrieve_with_large_page_size =====")
        logger.info(f"BASE_URL: {self.BASE_URL}")
        logger.info(f"Organization ID: {self.org_id}")
        logger.info(f"Auth token: {self.token[:10]}...")  # Only log first 10 chars for security
        logger.info(f"Headers: {self.headers}")

        # Log the environment variables
        logger.info(f"CHAT_SERVICE_HOST: {os.getenv('CHAT_SERVICE_HOST')}")
        logger.info(f"CHAT_SERVICE_PORT: {os.getenv('CHAT_SERVICE_PORT')}")

        expected_file_count = 50
        logger.info(f"Testing with expected {expected_file_count} uploaded files")
        
        # Log uploaded filenames for verification
        logger.info(f"Number of uploaded files: {len(self.uploaded_filenames)}")
        logger.info(f"First 5 filenames: {self.uploaded_filenames[:5]}")
        
        # Test with large page_size (100)
        url = f"{self.BASE_URL}/files/deletionstatus?page=1&page_size=100"
        logger.info(f"Sending GET request to URL: {url}")

        try:
            logger.info("Attempting to make the request...")
            response = requests.get(url, headers=self.headers, timeout=30)
            logger.info(f"Request completed with status code: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            # Log the raw response content for debugging
            logger.info(f"Raw response content: {response.text[:1000]}")  # Limit to first 1000 chars
            
            # Expect a 200 status code
            self.assertEqual(response.status_code, HTTPStatus.OK, 
                             f"Expected status code 200 but got {response.status_code}. Response: {response.text}")
            
            # Check if the response contains files
            try:
                logger.info("Attempting to parse JSON response...")
                data = response.json()
                logger.info(f"JSON parsing successful. Data type: {type(data)}")
                logger.info(f"Received {len(data)} files in response")
                
                # Log each file's basic info for debugging
                for i, file in enumerate(data[:10]):  # Log first 10 files only
                    logger.info(f"File {i+1}: ID={file.get('file_id', 'N/A')}, Name={file.get('filename', 'N/A')}, Status={file.get('deletion_status', 'N/A')}")
                
                if len(data) != expected_file_count:
                    logger.error(f"MISMATCH: Expected {expected_file_count} files but got {len(data)}")
                    # Log more details about the mismatch
                    if len(data) < expected_file_count:
                        logger.error(f"Missing {expected_file_count - len(data)} files")
                    else:
                        logger.error(f"Got {len(data) - expected_file_count} extra files")
                
                self.assertIsInstance(data, list, "Response is not a list")
                self.assertTrue(len(data) <= 100, f"Expected at most 100 files in the response, got {len(data)}")
                self.assertEqual(len(data), expected_file_count, 
                                f"Expected {expected_file_count} files but got {len(data)}. First few files: {data[:3]}")
                
                # Verify each file has required fields and valid status
                missing_fields = []
                for i, file in enumerate(data):
                    missing = []
                    if "file_id" not in file:
                        missing.append("file_id")
                    if "filename" not in file:
                        missing.append("filename")
                    if "deletion_status" not in file:
                        missing.append("deletion_status")
                    
                    if missing:
                        missing_fields.append(f"File {i}: missing {', '.join(missing)}")
                
                if missing_fields:
                    logger.error(f"Files with missing fields: {missing_fields}")
                
                for field in ["file_id", "filename", "deletion_status"]:
                    for i, file in enumerate(data):
                        self.assertIn(field, file, f"'{field}' not found in response for file {i}: {file}")
                
            except ValueError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Response content that caused the error: {response.text}")
                raise
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed with error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during test: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
            
        logger.info("===== COMPLETED test_retrieve_with_large_page_size =====")

    def test_pagination_for_delete_list_files(self):
        logger.info("Executing test_pagination_for_delete_list_files")

        # Define different page sizes for pagination testing
        page_sizes = [10, 20, 30]

        for page_size in page_sizes:
            logger.info(f"Testing with page_size={page_size}")

            all_files = []
            page_num = 1

            while True:
                page_url = f"{self.BASE_URL}/files/deletionstatus?page={page_num}&page_size={page_size}"
                response = requests.get(page_url, headers=self.headers)
                self.assertEqual(response.status_code, HTTPStatus.OK,f"Failed to fetch page {page_num} for page_size={page_size}" )

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
                self.assertIn("file_id", file, "'file_id' not found in response")
                self.assertIn("filename", file, "'filename' not found in response")
                self.assertIn("deletion_status", file, "'deletion_status' not found in response")

    def test_paginated_delete_list_files_without_token(self):
        logger.info("Executing test_paginated_delete_list_files_without_token")

        url = f"{self.BASE_URL}/files/deletionstatus?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url)
        logger.info(f"Received response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 401, "Expected status code 401 for missing token")
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Authentication required", "Unexpected error message")

    def test_paginated_delete_list_files_corrupted_token(self):
        logger.info("Executing test_paginated_delete_list_files_corrupted_token")

        headers = {"Authorization": "Bearer corrupted_token"}
        url = f"{self.BASE_URL}/files/deletionstatus?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, 401, "Expected status code 401 for corrupted token")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_paginated_delete_list_files_token_without_org_role(self):
        logger.info("Executing test_paginated_delete_list_files_token_without_org_role")

        headers = {'Authorization': f'Bearer {create_token_without_org_role(self.org_id)}'}
        url = f"{self.BASE_URL}/files/deletionstatus?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, 403, "Expected status code 403 for missing org_role")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_paginated_delete_list_files_token_without_org_id(self):
        logger.info("Executing test_paginated_delete_list_files_token_without_org_id")

        headers = {'Authorization': f'Bearer {create_token_without_org_id("org:admin")}'}
        url = f"{self.BASE_URL}/files/deletionstatus?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")

        self.assertEqual(response.status_code, 400, "Expected status code 400 for missing org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_paginated_delete_list_files_no_mapping_customer_guid(self):
        logger.info("Executing test_paginated_delete_list_files_no_mapping_customer_guid")

        # Create a new org_id without mapping it to a customer_guid
        org_id = "unmapped_org_id"
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}
        url = f"{self.BASE_URL}/files/deletionstatus?page=1&page_size=10"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code}")
        logger.info(f"Response content: {response.json()}")

        self.assertEqual(response.status_code, 404, "Expected status code 404 for unmapped org_id")
        self.assertIn("detail", response.json(),"'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided","Unexpected error message")

    def tearDown(self):
        """Teardown function to log the completion of the test case."""
        logger.info(f"=== Finished execution of test: {self._testMethodName} ===")


if __name__ == "__main__":
    unittest.main()

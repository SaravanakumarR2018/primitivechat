import logging
import os
import unittest
import sys
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from utils.api_utils import add_customer, create_test_token, create_token_without_org_role, create_token_without_org_id
from src.backend.lib.logging_config import get_primitivechat_logger

# Set up logging configuration
logger = get_primitivechat_logger(__name__)

class TestFileEmbeddingStatusAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        """Setup function to initialize customer, token, and upload a file to get a valid file_id."""
        logger.info(f"=== Starting setup process for test: {self._testMethodName} ===")

        # Initialize customer and token
        customer_data = add_customer("test_org")
        self.org_id = customer_data.get("org_id")
        self.token = create_test_token(org_id=self.org_id, org_role="org:admin")
        self.headers = {'Authorization': f'Bearer {self.token}'}

        # Upload a file to get a valid file_id
        upload_url = f"{self.BASE_URL}/uploadFile"
        test_file = ("testfile.txt", b"Sample file content")
        files = {"file": test_file}
        logger.info(f"Uploading test file: {test_file[0]}")

        upload_response = requests.post(upload_url, files=files, headers=self.headers)
        logger.info(f"Upload response status code: {upload_response.status_code}")

        # Check if the upload was successful
        self.assertEqual(upload_response.status_code, 200, "File upload failed")

        # Extract file_id from the upload response
        self.valid_file_id = upload_response.json().get("file_id")
        logger.info(f"Received valid file_id: {self.valid_file_id}")

        logger.info(f"=== Setup process completed for test: {self._testMethodName} ===")

    def test_valid_file_id_and_status(self):
        """Test the API with a valid file_id and check the processing stage."""
        logger.info("Executing test_valid_file_id_and_status")

        url = f"{self.BASE_URL}/file/{self.valid_file_id}/embeddingstatus"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Check if the response is successful
        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")

        # Check if the response contains the processing_stage
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIn("processing_stage", data, "'processing_stage' not found in response data")
        logger.info(f"File is in stage: {data['processing_stage']}")

    def test_invalid_file_id(self):
        """Test the API with an invalid file_id."""
        logger.info("Executing test_invalid_file_id")

        invalid_file_id = "invalid-file-id"
        url = f"{self.BASE_URL}/file/{invalid_file_id}/embeddingstatus"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url, headers=self.headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Check if the response indicates an error
        self.assertIn(response.status_code, [400], f"Expected status code 400 but got {response.status_code}")

        # Check if the error message is correct
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIn("detail", data, "'detail' not found in response data")
        self.assertIn("Filename not found", data["detail"], "Error message does not indicate file not found")

    def test_Invalid_customer_guid_file_and_valid_fileid(self):
        """Test the API with a valid file_id but an invalid customer_guid (org_id)."""
        logger.info("Executing test_Invalid_customer_guid_file_and_valid_fileid")

        # Step 1: Create a valid customer and get a valid file_id
        customer_data = add_customer("test_org")
        valid_org_id = customer_data.get("org_id")
        valid_token = create_test_token(org_id=valid_org_id, org_role="org:admin")
        valid_headers = {'Authorization': f'Bearer {valid_token}'}

        # Upload a file to get a valid file_id
        upload_url = f"{self.BASE_URL}/uploadFile"
        test_file = ("testfile.txt", b"Sample file content")
        files = {"file": test_file}
        logger.info(f"Uploading test file: {test_file[0]}")

        upload_response = requests.post(upload_url, files=files, headers=valid_headers)
        logger.info(f"Upload response status code: {upload_response.status_code}")

        # Check if the upload was successful
        self.assertEqual(upload_response.status_code, 200, "File upload failed")

        # Extract file_id from the upload response
        valid_file_id = upload_response.json().get("file_id")
        logger.info(f"Received valid file_id: {valid_file_id}")

        # Step 2: Create a token with an invalid org_id
        invalid_org_id = "Invalid_org_id"
        invalid_token = create_test_token(org_id=invalid_org_id, org_role="org:admin")
        invalid_headers = {'Authorization': f'Bearer {invalid_token}'}

        # Step 3: Call the embedding status API with the invalid token
        url = f"{self.BASE_URL}/file/{valid_file_id}/embeddingstatus"
        logger.info(f"Sending GET request to {url} with invalid org_id")

        response = requests.get(url, headers=invalid_headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Check if the response indicates an error
        self.assertEqual(response.status_code, 404, f"Expected status code 404 but got {response.status_code}")

        # Check if the error message is correct
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIn("detail", data, "'detail' not found in response data")
        self.assertEqual(data["detail"], "Invalid customer_guid provided", "Unexpected error message")

    def test_wrong_customer_guid_and_wrong_file_id(self):
        """Test the API with an invalid customer_guid and an invalid file_id."""
        logger.info("Executing test_wrong_customer_guid_and_wrong_file_id")

        # Step 1: Create a token with an invalid org_id (wrong customer_guid)
        invalid_org_id = "invalid_org_id"
        invalid_token = create_test_token(org_id=invalid_org_id, org_role="org:admin")
        invalid_headers = {'Authorization': f'Bearer {invalid_token}'}

        # Step 2: Use an invalid file_id
        invalid_file_id = "invalid-file-id"
        url = f"{self.BASE_URL}/file/{invalid_file_id}/embeddingstatus"
        logger.info(f"Sending GET request to {url} with invalid customer_guid and invalid file_id")

        response = requests.get(url, headers=invalid_headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Check if the response indicates an error
        self.assertEqual(response.status_code, 404, f"Expected status code 404 but got {response.status_code}")

        # Check if the error message is correct
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIn("detail", data, "'detail' not found in response data")
        self.assertEqual(data["detail"], "Invalid customer_guid provided", "Unexpected error message")

    def test_correct_customer_guid_and_wrong_file_id(self):
        """Test the API with a valid customer_guid but an invalid file_id."""
        logger.info("Executing test_correct_customer_guid_and_wrong_file_id")

        # Step 1: Use the valid token and headers from setUp
        valid_headers = self.headers

        # Step 2: Use an invalid file_id
        invalid_file_id = "invalid-file-id"
        url = f"{self.BASE_URL}/file/{invalid_file_id}/embeddingstatus"
        logger.info(f"Sending GET request to {url} with valid customer_guid and invalid file_id")

        response = requests.get(url, headers=valid_headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Check if the response indicates an error
        self.assertEqual(response.status_code, 400, f"Expected status code 400 but got {response.status_code}")

        # Check if the error message is correct
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIn("detail", data, "'detail' not found in response data")
        self.assertEqual(data["detail"], "Filename not found", "Unexpected error message")

    def test_missing_file_id(self):
        """Test the API with a missing file_id in the URL."""
        logger.info("Executing test_missing_file_id")

        # Step 1: Use the valid token and headers from setUp
        valid_headers = self.headers

        # Step 2: Call the API without a file_id in the URL
        url = f"{self.BASE_URL}/file//embeddingstatus"  # Missing file_id
        logger.info(f"Sending GET request to {url} with missing file_id")

        response = requests.get(url, headers=valid_headers)
        logger.info(f"Received response status code: {response.status_code}")

        # Check if the response indicates an error
        self.assertEqual(response.status_code, 404, f"Expected status code 404 but got {response.status_code}")

        # Check if the error message is correct
        data = response.json()
        logger.info(f"Response data: {data}")

        self.assertIn("detail", data, "'detail' not found in response data")
        self.assertEqual(data["detail"], "Not Found", "Unexpected error message")

    def test_fileid_without_token(self):
        logger.info("Executing file_id_without_token: Testing error handling for missing token")

        url = f"{self.BASE_URL}/file/{self.valid_file_id}/embeddingstatus"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url)
        logger.info(f"Received response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 401)
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Authentication required")

    def test_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        headers = {"Authorization": "Bearer corrupted_token"}
        url = f"{self.BASE_URL}/file/{self.valid_file_id}/embeddingstatus"
        logger.info(f"Sending GET request to {url}")

        response = requests.get(url,  headers=headers)
        self.assertEqual(response.status_code, 401, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_fileid_token_without_org_role(self):
        logger.info("Testing embeddingstatus API with a token missing org_role")

        headers = {'Authorization': f'Bearer {create_token_without_org_role(self.org_id)}'}
        url = f"{self.BASE_URL}/file/{self.valid_file_id}/embeddingstatus"
        response = requests.get(url, headers=headers)

        self.assertEqual(response.status_code, 403, "Expected status code 403 for missing org_role")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_fileid_token_without_org_id(self):
        logger.info("Testing embeddingstatus API with a token missing org_id")

        headers = {'Authorization': f'Bearer {create_token_without_org_id("org:admin")}'}
        url = f"{self.BASE_URL}/file/{self.valid_file_id}/embeddingstatus"
        response = requests.get(url, headers=headers)

        # Expect 400 Bad Request
        self.assertEqual(response.status_code, 400, "Expected status code 400 for missing org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_fileid_no_mapping_customer_guid(self):
        logger.info("Testing embeddingstatus API with no mapping between org_id and customer_guid")

        # Create a new org_id without mapping it to a customer_guid
        org_id = "unmapped_org_id"
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}
        url = f"{self.BASE_URL}/file/{self.valid_file_id}/embeddingstatus"
        response = requests.get(url, headers=headers)

        self.assertEqual(response.status_code, 404, "Expected status code 404 for unmapped org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided", "Unexpected error message")

    def tearDown(self):
        """Teardown function to log the completion of the test case."""
        logger.info(f"=== Finished execution of test: {self._testMethodName} ===")


if __name__ == "__main__":
    unittest.main()

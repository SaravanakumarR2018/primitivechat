import logging
import os
import unittest

import requests

from src.backend.lib.logging_config import get_primitivechat_logger
from utils.api_utils import add_customer, create_test_token, create_test_token,create_token_without_org_role,create_token_without_org_id

logger = get_primitivechat_logger(__name__)

class TestUploadFileAPI(unittest.TestCase):
    BASE_URL=f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        logger.info("===Starting setup process===")

        self.headers = {}
        # Get a valid customer_guid
        customer_data = add_customer("test_org")
        self.valid_customer_guid = customer_data["customer_guid"]
        logger.info(f"Output: Received valid customer_guid:{self.valid_customer_guid}")
        self.org_id = customer_data.get("org_id")
        self.token = create_test_token(org_id=self.org_id, org_role="org:admin")
        self.headers['Authorization'] = f'Bearer {self.token}'

        logger.info("===setup process completed===")

    def test_upload_file(self):
        logger.info("Executing test_upload_file: Testing file upload functionality")

        url=f"{self.BASE_URL}/uploadFile"
        logger.info(f"Sending Post request to {url}")

        # define test data
        test_file = ("testfile.txt", b"Sample file content")
        files = {"file": test_file}

        #make the post request
        response=requests.post(url, files=files, headers=self.headers)

        #Log the response status code
        logger.info(f"Received response status code:{response.status_code} for URL:{url}")

        #check if the response is successful
        self.assertEqual(response.status_code, 200, f"Expected status code 200 but got {response.status_code}")

        #check if the response contains the success message
        data=response.json()
        logger.info("Processing response data to check for success message")

        self.assertIn("message",data,"'message' not found in response data")
        logger.info("'message' found in response data, verifying its content")

        self.assertEqual(data["message"], "File uploaded SuccessFully", "Unexpected message content")

        logger.info("Test completed successfully for test_upload_file")

    def test_upload_without_file(self):
        logger.info("Executing test_upload_without_file: Testing error handling for missing files")

        url=f"{self.BASE_URL}/uploadFile"
        logger.info(f"Sending post URL request to {url}")

        # make post request without file
        response = requests.post(url, headers=self.headers)

        # Log the response status code
        logger.info(f"Received response status code:{response.status_code} for URL :{url}")

        #Assert the correct error code
        self.assertEqual(response.status_code, 422, f"Expected status code 422 but got {response.status_code}")

        #check if the error details are in the response
        data=response.json()
        logger.info("Processing response data to check for error details")

        self.assertIn("detail", data, "'detail' not found in response data")
        logger.info("Error details found in response data, verifying content")

        self.assertIn("file",data["detail"][0]["loc"],"'file' error not found in response details")
        logger.info("Test completed successfully for test_upload_without_file")

    def test_upload_without_token(self):
        logger.info("Executing test_upload_without_token: Testing error handling for missing token")

        url=f"{self.BASE_URL}/uploadFile"
        logger.info(f"Sending POST request to {url}")

        # Create a test file
        test_file = ("testfile.txt", b"Sample file content")
        files = {"file": test_file}

        # Make the POST request without a token
        response = requests.post(url, files=files)

        #Log the response status code
        logger.info(f"Received response status code: {response.status_code} for URL: {url}")

        #Assert the correct error code (401)
        self.assertIn(response.status_code, [401],f"Expected status code 401 but got {response.status_code}")

        # Check if the error details are in the response
        data=response.json()
        logger.info("processing response data to check for error details")

        self.assertIn("detail", data, "'detail' not found in response data")
        logger.info("Error details found in response data, verifying content")

        self.assertIn("authentication", data["detail"].lower(), "Authentication error not found in response details")
        logger.info("Test completed successfully for test_upload_without_token")

    def test_upload_file_with_any_file_type(self):
        logger.info("Executing test_upload_file_with_any_file_type: Testing file upload with various types")

        url=f"{self.BASE_URL}/uploadFile"
        logger.info(f"Sending post request to {url}")

        #define test data
        file_name="testfile.pdf"  #sample files
        file_content=b"%PDF-1.4 sample pdf content"

        #prepare a file as a tuple of(filename,file content)
        test_file=(file_name,file_content)

        # files parameter
        files={"file": test_file}

        #Make the post request to upload file
        response=requests.post(url, files=files, headers=self.headers)

        #Log the response status code
        logger.info(f"Received response status code:{response.status_code} for URL:{url}")

        # Verify the HTTP response status code
        if response.status_code == 200:
            logger.info(
                "Response status code is valid and matches the expected value (200). File uploaded successfully.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        data=response.json()
        logger.info(f"Response data: {data}")

        self.assertIn("message",data, "'message' not found in response data")
        logger.info("'message' found in response data, verifying its content")

        self.assertEqual(data["message"],"File uploaded SuccessFully", "Unexpected message content")
        logger.info("Test completed successfully for test_upload_file_with_any_file_type")

    def test_upload_large_file(self):
        logger.info("Executing test_upload_large_file: Testing large file upload")

        url=f"{self.BASE_URL}/uploadFile"
        logger.info(f"Sending post request to {url}")

        #define large file
        large_file_content=b"0" * 10 ** 7 # A 10MB File
        test_file=("largefile.txt",large_file_content)  # sample file
        files={"file": test_file}

        #Make the post request
        response=requests.post(url, files=files, headers=self.headers)

        #Log the response status code
        logger.info(f"Received response status code:{response.status_code} for URL:{url}")

        # Verify the HTTP response status code
        if response.status_code == 200:
            logger.info(
                "Response status code is valid and matches the expected value (200). File uploaded successfully.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        #Check if the response contains the success message
        data=response.json()
        logger.info("Processing response data to check for success message")

        self.assertIn("message",data,"'message' not found in response data")
        logger.info("'message' found in response data, verifying its content")

        self.assertEqual(data["message"],"File uploaded SuccessFully","Unexpected message content")

        logger.info("Test completed successfully for test_upload_large_file")

    def test_upload_file_with_invalid_customer_guid(self):
        logger.info("Executing test_upload_file_with_invalid_customer_guid: Testing file upload with an invalid customer_guid")

        url=f"{self.BASE_URL}/uploadFile"
        logger.info(f"Sending POST request to {url} with invalid customer_guid")

        # Simulate a token with an invalid or missing customer_guid
        invalid_token = create_test_token(org_id="invalid_org", org_role="org:admin")
        headers = {'Authorization': f'Bearer {invalid_token}'}

        #define valid test file
        file_name="valid_file.txt"  # Sample file
        file_content=b"Sample content for a valid file"
        test_file=(file_name, file_content)

        #Request data
        files={"file": test_file}

        #make post to request
        response=requests.post(url, files=files, headers=headers)

        #log the response
        logger.info(f"Received response status code:{response.status_code} for URL:{url}")
        logger.info(f"Response content:{response.text}")

        #check for the expected error response code 404
        self.assertIn(response.status_code, [404], f"Expected status code 404 but got {response.status_code}")

        data=response.json()

        #verify the response contains error
        self.assertIn("detail", data, "'detail' not found in response data")
        logger.info("'detail' found in response data, verifying its content")

        self.assertEqual(data["detail"],"Invalid customer_guid provided","Unexpected error message content")

        logger.info("Test completed successfully for test_upload_file_with_invalid_customer_guid")
        
    def test_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        headers = {"Authorization": "Bearer corrupted_token"}
        url = f"{self.BASE_URL}/uploadFile"
        # Define a valid test file
        file_name = "valid_file.txt"  # Sample file
        file_content = b"Sample content for a valid file"
        test_file = (file_name, file_content)

        # Request data
        files = {"file": test_file}

        logger.info("Testing API request with corrupted token")
        response = requests.post(url, files=files, headers=headers)
        self.assertEqual(response.status_code, 401, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")
        logger.info("Test completed successfully for test_corrupted_token")

    def test_upload_files_token_without_org_role(self):
        logger.info("Testing upload files API with a token missing org_role")

        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        url = f"{self.BASE_URL}/uploadFile"
        # Define a valid test file
        file_name = "valid_file.txt"  # Sample file
        file_content = b"Sample content for a valid file"
        test_file = (file_name, file_content)

        # Request data
        files = {"file": test_file}
        response = requests.post(url, files=files, headers=headers)

        self.assertEqual(response.status_code, 403, "Expected status code 403 for missing org_role")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

        logger.info("Successfully tested upload files API with token missing org_role")

    def test_upload_files_token_without_org_id(self):
        logger.info("Testing upload files API with a token missing org_id")

        url = f"{self.BASE_URL}/uploadFile"
        headers = {'Authorization': f'Bearer {create_token_without_org_id("org:admin")}'}
        # Define a valid test file
        file_name = "valid_file.txt"  # Sample file
        file_content = b"Sample content for a valid file"
        test_file = (file_name, file_content)

        # Request data
        files = {"file": test_file}
        response = requests.post(url, files=files, headers=headers)

        # Expect 400 Bad Request
        self.assertEqual(response.status_code, 400, "Expected status code 400 for missing org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

        logger.info("Successfully tested upload files API with token missing org_id")


    def test_upload_files_no_mapping(self):
        logger.info("Testing upload files API with no mapping between org_id and customer_guid")

        # Create a new org_id without mapping it to a customer_guid
        org_id = "unmapped_org_id"
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}

        url = f"{self.BASE_URL}/uploadFile"
        # Define a valid test file
        file_name = "valid_file.txt"  # Sample file
        file_content = b"Sample content for a valid file"
        test_file = (file_name, file_content)

        # Request data
        files = {"file": test_file}
        response = requests.post(url, files=files, headers=headers)

        self.assertEqual(response.status_code, 404, "Expected status code 404 for unmapped org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided", "Unexpected error message")

        logger.info("Successfully tested upload files API with no mapping between org_id and customer_guid")



if __name__ == "__main__":
    unittest.main()

import logging
import os
import unittest

import requests

from utils.api_utils import add_customer, create_test_token

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger=logging.getLogger(__name__)

class TestListFileAPI(unittest.TestCase):
    BASE_URL=f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def test_list_files_no_files_uploaded(self):
        logger.info("Testing file listing with no files uploaded")

        # Initialize customer and token
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}

        list_files_url = f"{self.BASE_URL}/listfiles"
        response = requests.get(list_files_url, headers=headers)

        #Verify the HTTP response status code
        if response.status_code==200:
            logger.info("Response status code is valid and matches the expected value (200). No files found.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        #Assert the response
        self.assertEqual(response.status_code, 200, "Failed to list files for new customer")
        self.assertEqual(response.json()["files"], [], "File list should be empty for new customer")

        logger.info("Successfully tested file listing when no files have been uploaded")

    def test_list_files_from_empty_bucket(self):
        logger.info("Testing file listing for an empty bucket")

        # Initialize customer and token
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}

        list_files_url = f"{self.BASE_URL}/listfiles"
        response = requests.get(list_files_url, headers=headers)

        # Verify the HTTP response status code
        if response.status_code == 200:
            logger.info("Response status code is valid and matches the expected value (200). Bucket is empty.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        #Assert the response is successful and the file list is empty
        self.assertEqual(response.status_code, 200, "Failed to list files for empty bucket")
        self.assertEqual(response.json().get("files"), [], "Expected no files in the bucket")

        logger.info("Successfully tested file listing for an empty bucket")

    def test_list_files_from_invalid_customer_guid(self):
        logger.info("Executing test_list_files_from_invalid_customer_guid: Testing list files with an invalid customer_guid")

        url=f"{self.BASE_URL}/listfiles"
        logger.info(f"Sending GET request to {url} with invalid customer_guid")

        # Simulate a token with an invalid or missing customer_guid
        invalid_token = create_test_token(org_id="invalid_org", org_role="org:admin")
        headers = {'Authorization': f'Bearer {invalid_token}'}

        #Make GET request
        response=requests.get(url, headers=headers)
        logger.info(f"Received response status code: {response.status_code} for URL: {url}")
        logger.info(f"Response content: {response.text}")

        self.assertIn(response.status_code, [404], f"Expected status code 404 but got {response.status_code}")
        data=response.json()

        #Verify the response contains the 'detail' field
        self.assertIn("detail", data, "'detail' not found in response data")
        logger.info("'detail' found in response data, verifying its content")

        #Verify that the error message indicates invalid customer_guid
        self.assertEqual(data["detail"], "Invalid customer_guid provided", "Unexpected error message content")

        logger.info("Test completed successfully for test_list_files_from_invalid_customer_guid")

    def test_list_files_two_files_uploaded(self):
        logger.info("Testing file listing after uploading two files")

        # Initialize customer and token
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}

        upload_file_url=f"{self.BASE_URL}/uploadFile"
        files_to_upload=[
            ("test_file1.txt", b"Content of file 1", "text/plain"),
            ("test_file2.txt", b"Content of file 2", "text/plain"),
        ]

        for filename, content, mime_type in files_to_upload:
            files = {"file": (filename, content, mime_type)}
            upload_response = requests.post(upload_file_url, files=files, headers=headers)

            #Verify the HTTP response status code for file upload
            if upload_response.status_code==200:
                logger.info(f"File {filename} uploaded successfully. Status code 200 received.")
            else:
                logger.error(f"Failed to upload file {filename}. Status code: {upload_response.status_code}. Expected: 200.")
                raise AssertionError(f"Expected status code 200 for file upload but got {upload_response.status_code}")

            self.assertEqual(upload_response.status_code, 200, f"File upload failed for {filename}")

        list_files_url = f"{self.BASE_URL}/listfiles"
        response = requests.get(list_files_url, headers=headers)

        #Verify response
        self.assertEqual(response.status_code, 200, "Failed to list files")

        #Verify files in response
        response_data=response.json()
        self.assertEqual(set(response_data.get("files")), {"test_file1.txt", "test_file2.txt"}, "Files do not match")

        logger.info("Successfully tested file listing after uploading two files")

    def test_list_files_three_files_uploaded(self):
        logger.info("Testing file listing after uploading three files")

        # Initialize customer and token
        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}

        upload_file_url=f"{self.BASE_URL}/uploadFile"
        files_to_upload=[
            ("tested1.txt", b"Content of file 1", "text/plain"),
            ("tested2.txt", b"Content of file 2", "text/plain"),
            ("tested3.txt", b"Content of file 3", "text/plain")
        ]

        for filename, content, mime_type in files_to_upload:
            files = {"file": (filename, content, mime_type)}
            upload_response = requests.post(upload_file_url, files=files, headers=headers)
            self.assertEqual(upload_response.status_code, 200, f"File upload failed for {filename}")
            logger.info(f"Uploaded {filename} successfully.")

            #Verify the HTTP response status code for listing files
            if upload_response.status_code==200:
                logger.info("Successfully retrieved file list. Status code 200 received.")
            else:
                logger.error(f"Failed to retrieve file list. Status code: {upload_response.status_code}. Expected: 200.")
                raise AssertionError(f"Expected status code 200 but got {upload_response.status_code}")

        list_files_url = f"{self.BASE_URL}/listfiles"
        response = requests.get(list_files_url, headers=headers)

        #Verify response
        self.assertEqual(response.status_code, 200, "Failed to list files for valid customer_guid")

        #Verify the presence of the 'files' key in the response
        response_data=response.json()
        self.assertIn("files", response_data, "'files' key is missing in the response")

        # Verify the file names in the response
        listed_files = response_data.get("files")
        self.assertIsInstance(listed_files, list, "'files' is not a list")
        expected_file_names=[file[0] for file in files_to_upload]
        self.assertEqual(set(listed_files), set(expected_file_names),"File names in response do not match uploaded files")

        logger.info("Successfully tested file listing after uploading three files")


if __name__ == "__main__":
    unittest.main()

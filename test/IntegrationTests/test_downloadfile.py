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

# Constants
TEST_ORG = "test_org"
ORG_ADMIN_ROLE = "org:admin"
INVALID_GUID = "invalid-guid"

class TestDownloadFileAPI(unittest.TestCase):
    BASE_URL=f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def test_download_file_valid_customer(self):
        logger.info("Testing valid file download")

        # Setup: Create a customer and upload a test file
        customer_data = add_customer(TEST_ORG)
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role=ORG_ADMIN_ROLE)
        headers = {'Authorization': f'Bearer {token}'}

        # Upload the file
        upload_file_url = f"{self.BASE_URL}/uploadFile"
        files = {"file": ("testfile.txt", b"Test content", "text/plain")}
        upload_response = requests.post(upload_file_url, files=files, headers=headers)

        # Verify the HTTP response status code for file upload
        if upload_response.status_code == 200:
            logger.info("Successfully uploaded file. Status code 200 received.")
        else:
            logger.error(f"Failed to upload file. Status code: {upload_response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {upload_response.status_code}")
        self.assertEqual(upload_response.status_code, 200, "Failed to upload file")

        # Download the file
        download_file_url = f"{self.BASE_URL}/downloadfile"
        params = {"filename": "testfile.txt"}
        response = requests.get(download_file_url, params=params, headers=headers)

        self.assertEqual(response.status_code, 200, "Failed to download file")
        self.assertEqual(response.content, b"Test content", "Downloaded content mismatch")

        logger.info("Successfully tested valid file download for customer")

    def test_download_file_invalid_customer_guid(self):
        logger.info("Testing download with invalid customer GUID")

        # Setup: Create a token with an invalid customer GUID
        token = create_test_token(org_id="invalid_org", org_role=ORG_ADMIN_ROLE)
        headers = {'Authorization': f'Bearer {token}'}

        # Test: Attempt to download a file
        download_file_url = f"{self.BASE_URL}/downloadfile"
        params = {"filename": "testfile.txt"}
        response = requests.get(download_file_url, params=params, headers=headers)

        # Verify the HTTP response status code
        if response.status_code == 404:
            logger.info("Correctly received 404 status code for invalid customer GUID.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 404.")
            raise AssertionError(f"Expected status code 404 but got {response.status_code}")

        self.assertEqual(response.status_code, 404, "Expected 404 for invalid customer GUID")
        self.assertIn("detail", response.json(), "'detail' not found in response data")
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided", "Unexpected error message")

    def test_download_file_from_empty_bucket(self):
        logger.info("Testing download from an empty bucket")

        # Setup: Create a new customer with an empty bucket
        customer_data = add_customer(TEST_ORG)
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role=ORG_ADMIN_ROLE)
        headers = {'Authorization': f'Bearer {token}'}

        # Test: Attempt to download a non-existent file
        download_file_url = f"{self.BASE_URL}/downloadfile"
        params = {"filename": "file.txt"}
        response = requests.get(download_file_url, params=params, headers=headers)

        # Verify the HTTP response status code for empty bucket (should be 400)
        if response.status_code == 400:
            logger.info("Correctly received 400 status code for empty bucket.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 400.")
            raise AssertionError(f"Expected status code 400 but got {response.status_code}")

        self.assertEqual(response.status_code, 400, "Expected 400 for empty bucket")
        self.assertIn("detail", response.json(), "'detail' not found in response data")
        self.assertIn("Failed to download file", response.json()["detail"], "Unexpected error message")

        logger.info("Successfully tested download from an empty bucket")

    def test_download_file_without_filename(self):
        logger.info("Testing download request without specifying a filename")

        # Setup: Create a customer and token
        customer_data = add_customer(TEST_ORG)
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role=ORG_ADMIN_ROLE)
        headers = {'Authorization': f'Bearer {token}'}

        # Test: Attempt to download without a filename
        download_file_url = f"{self.BASE_URL}/downloadfile"
        response = requests.get(download_file_url, headers=headers)

        #Verify the HTTP response status code for missing filename (should be 422)
        if response.status_code==422:
            logger.info("Correctly received 422 status code for missing filename.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 422.")
            raise AssertionError(f"Expected status code 422 but got {response.status_code}")

        self.assertEqual(response.status_code, 422, "Expected 422 for missing filename")
        self.assertIn("detail", response.json(), "'detail' not found in response data")
        self.assertEqual(response.json()["detail"][0]["msg"], "Field required", "Unexpected validation message")

        logger.info("Successfully tested download request without specifying a filename")

    def test_download_and_verify_uploaded_files(self):
        logger.info("Testing file download, verification, and file name matching after uploading files")

        #Setup:Create a customer and upload multiple files
        customer_data = add_customer(TEST_ORG)
        org_id = customer_data.get("org_id")
        token = create_test_token(org_id=org_id, org_role=ORG_ADMIN_ROLE)
        headers = {'Authorization': f'Bearer {token}'}

        files_to_upload = [
            ("file1.txt", b"Content of file 1", "text/plain"),
            ("file2.txt", b"Content of file 2", "text/plain"),
            ("file3.txt", b"Content of file 3", "text/plain"),
        ]

        # Upload files
        upload_file_url = f"{self.BASE_URL}/uploadFile"
        for filename, content, _ in files_to_upload:
            files = {"file": (filename, content, "text/plain")}
            upload_response = requests.post(upload_file_url, files=files, headers=headers)
            self.assertEqual(upload_response.status_code, 200, f"File upload failed for {filename}")
            logger.info(f"Uploaded {filename} successfully.")

            # Verify the HTTP response status code for file upload
            if upload_response.status_code==200:
                logger.info(f"Uploaded {filename} successfully.")
            else:
                logger.error(f"File upload failed for {filename}. Status code: {upload_response.status_code}. Expected: 200.")
                raise AssertionError(f"Expected status code 200 but got {upload_response.status_code}")

        #List files for the customer
        list_files_url = f"{self.BASE_URL}/listfiles"
        list_response = requests.get(list_files_url, headers=headers)

        #Verify response for file listing
        self.assertEqual(list_response.status_code, 200, "Failed to list files for valid customer_guid")
        response_data=list_response.json()
        self.assertIn("files", response_data, "'files' key is missing in the response")

        #Extract listed file names and verify
        listed_files=response_data.get("files")
        self.assertIsInstance(listed_files, list, "'files' is not a list")
        expected_file_names=[file[0] for file in files_to_upload]
        self.assertEqual(set(listed_files), set(expected_file_names),"File names in response do not match uploaded files")
        logger.info(f"Listed files match the uploaded files: {expected_file_names}")

        #Download and verify each file
        download_file_url=f"{self.BASE_URL}/downloadfile"
        for filename,expected_content, _ in files_to_upload:
            params={"filename": filename}
            download_response=requests.get(download_file_url, params=params, headers=headers)

            #Verify the HTTP response status code
            self.assertEqual(download_response.status_code, 200, f"Failed to download file {filename}")
            logger.info(f"Downloaded {filename} successfully.")

            #Verify the content of the downloaded file
            self.assertEqual(download_response.content, expected_content, f"Content mismatch for file {filename}")
            logger.info(f"Verified content of {filename} successfully.")

        logger.info("Successfully tested downloading, verifying, and matching file names")


if __name__ == "__main__":
    unittest.main()
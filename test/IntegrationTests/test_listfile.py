import unittest
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger=logging.getLogger(__name__)

class TestListFileAPI(unittest.TestCase):
    BASE_URL="http://localhost:8000"

    def setUp(self):
        logger.info("=== Starting setup process ===")

        add_customer_url=f"{self.BASE_URL}/addcustomer"
        logger.info(f"Requesting new customer from:{add_customer_url}")

        response=requests.post(add_customer_url)
        self.assertEqual(response.status_code, 200, "Failed to create customer")

        customer_data=response.json()
        self.customer_guid=customer_data.get("customer_guid")
        logger.info(f"Received valid customer_guid: {self.customer_guid}")

        # upload a test file here to ensure that there are files to list
        upload_file_url=f"{self.BASE_URL}/uploadFile"
        test_file_data ={"customer_guid": self.customer_guid}
        test_file=("file",("testfile.txt",b"Hello,Python","text/plain"))
        file_response = requests.post(upload_file_url, data=test_file_data, files=[test_file])

        self.assertEqual(file_response.status_code, 200, "File upload failed during setup")

        logger.info("=== Setup process completed ===")

    def test_list_files_success(self):
        logger.info("Testing file listing for a valid customer_guid")

        list_files_url=f"{self.BASE_URL}/listfiles"
        params={"customer_guid": self.customer_guid}
        response=requests.get(list_files_url, params=params)

        # Verify the HTTP response status code
        if response.status_code==200:
            logger.info("Response status code is valid and matches the expected value (200). File listing successful.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        # Assert the response
        self.assertEqual(response.status_code, 200, "Failed to list files for valid customer_guid")
        self.assertIn("files", response.json(), "No 'files' key returned in response")

        logger.info("Successfully tested file listing for a valid customer_guid")

    def test_list_files_no_files_uploaded(self):
        logger.info("Testing file listing with no files uploaded")

        # Create a new customer without uploading any file
        add_customer_url=f"{self.BASE_URL}/addcustomer"
        response=requests.post(add_customer_url)
        self.assertEqual(response.status_code, 200, "Failed to create customer")

        customer_data=response.json()
        new_customer_guid=customer_data.get("customer_guid")

        list_files_url=f"{self.BASE_URL}/listfiles"
        params={"customer_guid": new_customer_guid}
        response=requests.get(list_files_url, params=params)

        # Verify the HTTP response status code
        if response.status_code==200:
            logger.info("Response status code is valid and matches the expected value (200). No files found.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        # Assert the response
        self.assertEqual(response.status_code, 200, "Failed to list files for new customer")
        self.assertEqual(response.json()["files"], [], "File list should be empty for new customer")

        logger.info("Successfully tested file listing when no files have been uploaded")

    def test_list_files_from_empty_bucket(self):
        logger.info("Testing file listing for an empty bucket")

        # Create a new customer to get a valid GUID
        add_customer_url=f"{self.BASE_URL}/addcustomer"
        response=requests.post(add_customer_url)
        self.assertEqual(response.status_code, 200, "Failed to create customer")

        customer_data=response.json()
        customer_guid=customer_data.get("customer_guid")
        logger.info(f"Created new customer with GUID: {customer_guid}")

        # Verify the bucket exists but no files are uploaded
        list_files_url=f"{self.BASE_URL}/listfiles"
        params={"customer_guid": customer_guid}
        response=requests.get(list_files_url, params=params)

        # Verify the HTTP response status code
        if response.status_code==200:
            logger.info("Response status code is valid and matches the expected value (200). Bucket is empty.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        # Assert the response is successful and the file list is empty
        self.assertEqual(response.status_code, 200, "Failed to list files for empty bucket")
        self.assertEqual(response.json().get("files"), [], "Expected no files in the bucket")

        logger.info("Successfully tested file listing for an empty bucket")

    def test_list_files_from_invalid_customer_guid(self):
        logger.info("Executing test_list_files_from_invalid_customer_guid: Testing list files with an invalid customer_guid")

        invalid_customer_guid="invalid-customer-guid"

        url=f"{self.BASE_URL}/listfiles"
        logger.info(f"Sending GET request to {url} with invalid customer_guid")

        # Request parameters
        params={"customer_guid":invalid_customer_guid}

        #Make GET request
        response = requests.get(url, params=params)

        logger.info(f"Received response status code: {response.status_code} for URL: {url}")
        logger.info(f"Response content: {response.text}")

        self.assertIn(response.status_code, [404], f"Expected status code 404 but got {response.status_code}")

        data=response.json()

        # Verify the response contains the 'detail' field
        self.assertIn("detail", data, "'detail' not found in response data")
        logger.info("'detail' found in response data, verifying its content")

        # Verify that the error message indicates invalid customer_guid
        self.assertEqual(data["detail"], "Invalid customer_guid provided", "Unexpected error message content")

        logger.info("Test completed successfully for test_list_files_from_invalid_customer_guid")


if __name__ == "__main__":
    unittest.main()

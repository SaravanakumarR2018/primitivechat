import unittest
import requests
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger=logging.getLogger(__name__)

class TestListFileAPI(unittest.TestCase):
    # Get the port from environment variables (default to 8000 if not set)
    BASE_URL = f"http://localhost:{os.getenv('CHAT_SERVICE_PORT', 8000)}"

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

        #Create a new customer to get a valid GUID
        add_customer_url=f"{self.BASE_URL}/addcustomer"
        response=requests.post(add_customer_url)
        self.assertEqual(response.status_code, 200, "Failed to create customer")

        customer_data=response.json()
        customer_guid=customer_data.get("customer_guid")
        logger.info(f"Created new customer with GUID: {customer_guid}")

        #Verify the bucket exists but no files are uploaded
        list_files_url=f"{self.BASE_URL}/listfiles"
        params={"customer_guid": customer_guid}
        response=requests.get(list_files_url, params=params)

        #Verify the HTTP response status code
        if response.status_code==200:
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

        invalid_customer_guid="invalid-customer-guid"

        url=f"{self.BASE_URL}/listfiles"
        logger.info(f"Sending GET request to {url} with invalid customer_guid")

        #Request parameters
        params={"customer_guid": invalid_customer_guid}

        #Make GET request
        response=requests.get(url, params=params)
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

        #Create a customer and upload two files
        add_customer_url=f"{self.BASE_URL}/addcustomer"
        response=requests.post(add_customer_url)

        #Verify the HTTP response status code
        if response.status_code==200:
            logger.info("Successfully created customer. Status code 200 received.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        self.assertEqual(response.status_code, 200, "Failed to create customer")
        customer_guid=response.json().get("customer_guid")
        self.assertIsNotNone(customer_guid, "Customer GUID is missing in the response")

        upload_file_url=f"{self.BASE_URL}/uploadFile"
        files_to_upload=[
            ("file1.txt", b"Content of file 1", "text/plain"),
            ("file2.txt", b"Content of file 2", "text/plain"),
        ]

        for filename,content,mime_type in files_to_upload:
            file_data={"customer_guid": customer_guid}
            files={"file": (filename, content, mime_type)}
            upload_response=requests.post(upload_file_url, data=file_data, files=files)

            #Verify the HTTP response status code for file upload
            if upload_response.status_code==200:
                logger.info(f"File {filename} uploaded successfully. Status code 200 received.")
            else:
                logger.error(f"Failed to upload file {filename}. Status code: {upload_response.status_code}. Expected: 200.")
                raise AssertionError(f"Expected status code 200 for file upload but got {upload_response.status_code}")

            self.assertEqual(upload_response.status_code, 200, f"File upload failed for {filename}")

        #List files
        list_files_url=f"{self.BASE_URL}/listfiles"
        params={"customer_guid": customer_guid}
        response=requests.get(list_files_url, params=params)

        #Verify response
        self.assertEqual(response.status_code, 200, "Failed to list files")

        #Verify files in response
        response_data=response.json()
        self.assertEqual(set(response_data.get("files")), {"file1.txt", "file2.txt"}, "Files do not match")

        logger.info("Successfully tested file listing after uploading two files")

    def test_list_files_three_files_uploaded(self):
        logger.info("Testing file listing after uploading three files")

        #Create a new customer
        add_customer_url=f"{self.BASE_URL}/addcustomer"
        response=requests.post(add_customer_url)

        #Verify the HTTP response status code for customer creation
        if response.status_code == 200:
            logger.info("Successfully created customer. Status code 200 received.")
        else:
            logger.error(f"Unexpected status code: {response.status_code}. Expected: 200.")
            raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        self.assertEqual(response.status_code, 200, "Failed to create customer")
        customer_guid=response.json().get("customer_guid")
        self.assertIsNotNone(customer_guid, "Customer GUID is missing in the response")
        logger.info(f"Created customer with GUID: {customer_guid}")

        #Upload three files for the customer
        upload_file_url=f"{self.BASE_URL}/uploadFile"
        files_to_upload=[
            ("file1.txt", b"Content of file 1", "text/plain"),
            ("file2.txt", b"Content of file 2", "text/plain"),
            ("file3.txt", b"Content of file 3", "text/plain")
        ]

        for filename,content,mime_type in files_to_upload:
            file_data={"customer_guid": customer_guid}
            files={"file": (filename, content, mime_type)}
            upload_response=requests.post(upload_file_url, data=file_data, files=files)
            self.assertEqual(upload_response.status_code, 200, f"File upload failed for {filename}")
            logger.info(f"Uploaded {filename} successfully.")

            #Verify the HTTP response status code for listing files
            if response.status_code==200:
                logger.info("Successfully retrieved file list. Status code 200 received.")
            else:
                logger.error(f"Failed to retrieve file list. Status code: {response.status_code}. Expected: 200.")
                raise AssertionError(f"Expected status code 200 but got {response.status_code}")

        #List files for the customer
        list_files_url=f"{self.BASE_URL}/listfiles"
        params={"customer_guid": customer_guid}
        response=requests.get(list_files_url, params=params)

        #Verify response
        self.assertEqual(response.status_code, 200, "Failed to list files for valid customer_guid")

        #Verify the presence of the 'files' key in the response
        response_data=response.json()
        self.assertIn("files", response_data, "'files' key is missing in the response")

        #Verify the file names in the response
        listed_files=response_data.get("files")
        self.assertIsInstance(listed_files, list, "'files' is not a list")
        expected_file_names=[file[0] for file in files_to_upload]
        self.assertEqual(set(listed_files), set(expected_file_names),"File names in response do not match uploaded files")

        logger.info("Successfully tested file listing after uploading three files")


if __name__ == "__main__":
    unittest.main()

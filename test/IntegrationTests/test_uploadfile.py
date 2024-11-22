import unittest
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger=logging.getLogger(__name__)

class TestUploadFileAPI(unittest.TestCase):
    BASE_URL="http://localhost:8000"

    def setUp(self):
        logger.info("===Starting setup process===")

        #Get a valid customer_guid
        add_customer_url=f"{self.BASE_URL}/addcustomer"
        logger.info(f"Input:Requesting new customer from : {add_customer_url}")

        customer_response=requests.post(add_customer_url)
        logger.info(f"Output: Customer creation response status:{customer_response.status_code}")

        #Assert the customer creation was successful
        self.assertEqual(customer_response.status_code,200)
        customer_data=customer_response.json()
        self.valid_customer_guid=customer_data["customer_guid"]
        logger.info(f"Output: Received valid customer_guid:{self.valid_customer_guid}")

        logger.info("===setup process completed===")


    def test_upload_file(self):
        logger.info("Executing test_upload_file: Testing file upload functionality")

        url=f"{self.BASE_URL}/uploadFile"
        logger.info(f"Sending Post request to {url}")

        #define test data
        test_file=("testfile.txt", b"Sample file content")
        data={"customer_guid":self.valid_customer_guid}
        files={"file":test_file}

        #make the post request
        response=requests.post(url,data=data, files=files)

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

        data={"customer_guid":self.valid_customer_guid}

        #make post request without file
        response=requests.post(url,data=data)

        #Log the response status code
        logger.info(f"Received response status code:{response.status_code} for URL :{url}")

        #Assert the correct error code
        self.assertEqual(response.status_code,422, f"Expected status code 422 but got {response.status_code}")

        #check if the error details are in the response
        data=response.json()
        logger.info("Processing response data to check for error details")

        self.assertIn("detail", data, "'detail' not found in response data")
        logger.info("Error details found in response data, verifying content")

        self.assertIn("file",data["detail"][0]["loc"],"'file' error not found in response details")
        logger.info("Test completed successfully for test_upload_without_file")


    def test_upload_without_customer_guid(self):
        logger.info("Executing test_upload_with_invalid_customer_guid: Testing error handling for invalid customer_guid")

        url=f"{self.BASE_URL}/uploadFile"
        logger.info(f"Sending post request to {url}")

        without_guid="without customer_guid"
        test_file=("testfile.txt",b"Sample file content")
        files={"files":test_file}

        #Make the post request
        response= requests.post(url, files=files)

        #Log the response status code
        logger.info(f"Received response status code:{response.status_code} for URL:{url}")

        #Assert the correct error code
        self.assertEqual(response.status_code, 422, f"Expected status code 422 but got {response.status_code}")

        #Check if the error details are in the response
        data=response.json()
        logger.info("processing response data to check for error details")

        self.assertIn("detail", data, "'detail' not found in response data")
        logger.info("Error details found in response data, Verifying content")

        self.assertIn("customer_guid",data["detail"][0]["loc"],"'customer_guid' error not found in response details")
        logger.info("Test completed successfully for test_upload_without_customer_guid")


    def test_upload_file_with_any_file_type(self):
        logger.info("Executing test_upload_file_with_any_file_type: Testing file upload with various types")

        url=f"{self.BASE_URL}/uploadFile"
        logger.info(f"Sending post request to {url}")

        #define test data
        file_name="testfile.pdf"    #sample files
        file_content=b"%PDF-1.4 sample pdf content"

        #prepare a file as a tuple of(filename,file content)
        test_file=(file_name,file_content)

        #files parameter
        data = {"customer_guid": self.valid_customer_guid}
        files={"file":test_file}

        #Make the post request to upload file
        response=requests.post(url,data=data, files=files)

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
        large_file_content=b"0" * 10**7 #A 10MB File
        data = {"customer_guid": self.valid_customer_guid}
        test_file=("largefile.txt",large_file_content)  #sample file
        files={"file":test_file}

        #Make the post request
        response=requests.post(url,data=data, files=files)

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
        logger.info(f"sending post request to {url}")

        #define invalid customer guid
        invalid_customer_guid="invalid_guid"

        #define valid test file
        file_name="valid_file.txt" #sample file
        file_content=b"Sample content for a valid file"
        test_file=(file_name,file_content)

        #request data
        data={"customer_guid":invalid_customer_guid}
        files={"file":test_file}

        #make post to request
        response=requests.post(url, data=data, files=files)

        #log the response
        logger.info(f"Received response status code:{response.status_code} for URL:{url}")
        logger.info(f"Response content:{response.text}")

        #check for the expected error response code 404
        self.assertIn(response.status_code,[404], f"Expected status code 404 but got {response.status_code}")

        data=response.json()

        #verify the response contains error
        self.assertIn("detail", data, "'detail' not found in response data")
        logger.info("'detail' found in response data, verifying its content")

        self.assertEqual(data["detail"],"Invalid customer_guid provided","Unexpected error message content")

        logger.info("Test completed successfully for test_upload_file_with_invalid_customer_guid")


if __name__ == "__main__":
    unittest.main()

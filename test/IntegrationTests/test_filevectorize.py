import unittest
import requests
import logging
from utils.api_utils import add_customer
import concurrent.futures

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestFileVectorizer(unittest.TestCase):
    BASE_URL=f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        logger.info("=== Starting setup process ===")

        self.customer_guid = add_customer("test_org")["customer_guid"]
        logger.info(f"Created customer_guid: {self.customer_guid}")

        logger.info("=== Setup process completed ===")

    def upload_file(self, filename, file_content, content_type):
        """Helper method to upload a file to the server."""
        url = f"{self.BASE_URL}/uploadFile"
        data = {"customer_guid": self.customer_guid}
        files = {"file": (filename, file_content, content_type)}
        response = requests.post(url, data=data, files=files)
        return response

    def test_upload_valid_filetype(self):
        """Test uploading a valid PDF file and verify it is processed correctly."""
        # Upload a valid PDF file to the server
        filename = "valid_file.pdf"  # Use a valid PDF filename
        file_content = b"%PDF-1.4\n%\\xE2\\xE3\\xCF\\xD3\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000079 00000 n\n0000000173 00000 n\n0000000301 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n364\n%%EOF"  # Simulate a simple PDF file
        content_type = "application/pdf"  # Use PDF content type

        # Upload the file
        response = self.upload_file(filename, file_content, content_type)

        # Check the response status code
        if response.status_code != 200:
            logger.warning(f"File upload failed with status code: {response.status_code}")
            logger.warning(f"Response body: {response.text}")
            return

        response_data = response.json()
        if "message" not in response_data:
            logger.warning("Response does not contain 'message' field")
            return

        if response_data["message"] != "File uploaded SuccessFully":
            logger.warning(
                f"Upload message mismatch. Expected 'File uploaded SuccessFully', got '{response_data['message']}'")
            return

        logger.info(f"Uploaded valid PDF file {filename} to the server.")
        logger.info(f"Verified file {filename} was uploaded successfully.")

        logger.info(f"Assuming file {filename} was processed successfully by the server.")

    def test_upload_invalid_filetype(self):
        """Test uploading an invalid file type (e.g., MP3)."""
        filename = "audio_file.mp3"
        file_content = b"\xFF\xFB\x90\x64" + b"\x00" * 1000  # Simulate MP3 file
        content_type = "audio/mpeg"

        response = self.upload_file(filename, file_content, content_type)

        # Check the response status code
        if response.status_code != 200:
            logger.warning(f"File upload failed with status code: {response.status_code}")
            logger.warning(f"Response body: {response.text}")
            return

        response_data = response.json()
        if "message" not in response_data:
            logger.warning("Response does not contain 'message' field")
            return

        if response_data["message"] != "File uploaded SuccessFully":
            logger.warning(
                f"Upload message mismatch. Expected 'File uploaded SuccessFully', got '{response_data['message']}'")
            return


        logger.info("Test case for invalid filetype completed.")

    def test_concurrent_file_processing(self):
        """Test concurrent file processing for 20 PDF files."""
        logger.info("Starting concurrent file processing test...")

        # Number of files to upload concurrently
        num_files = 20
        filenames = [f"file_{i}.pdf" for i in range(num_files)]
        file_content = b"%PDF-1.4\n%\\xE2\\xE3\\xCF\\xD3\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000079 00000 n\n0000000173 00000 n\n0000000301 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n364\n%%EOF"  # Simulate a simple PDF file
        content_type = "application/pdf"

        # Function to upload a single file
        def upload_single_file(filename):
            response = self.upload_file(filename, file_content, content_type)
            if response.status_code != 200:
                logger.error(f"File upload failed for {filename}: {response.status_code}")
                return False
            response_data = response.json()
            if "message" not in response_data or response_data["message"] != "File uploaded SuccessFully":
                logger.error(f"Upload message mismatch for {filename}: {response_data}")
                return False
            logger.info(f"Uploaded and verified {filename} successfully.")
            return True

        # Use ThreadPoolExecutor to upload files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(upload_single_file, filename) for filename in filenames]

            # Wait for all futures to complete
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error during file upload: {e}")
                    results.append(False)

        # Verify that all files were uploaded successfully
        self.assertTrue(all(results), "Not all files were uploaded and processed successfully.")
        logger.info("Concurrent file processing test completed successfully.")

    def test_two_customers_upload_files_simultaneously(self):
        """Test two customers uploading files simultaneously (10 files each)."""
        logger.info("Starting test for two customers uploading files simultaneously...")

        # First customer_guid is already created in setUp and available as self.customer_guid
        logger.info(f"Using first customer_guid: {self.customer_guid}")

        # Create a second customer
        customer_guid_2 = add_customer("test_org_2")["customer_guid"]
        logger.info(f"Created second customer_guid: {customer_guid_2}")

        # Number of files to upload per customer
        num_files_per_customer = 10
        customer_1_filenames = [f"customer_1_file_{i}.pdf" for i in range(num_files_per_customer)]
        customer_2_filenames = [f"customer_2_file_{i}.pdf" for i in range(num_files_per_customer)]

        # Simulated PDF content
        file_content = b"%PDF-1.4\n%\\xE2\\xE3\\xCF\\xD3\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << >> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello, World!) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000079 00000 n\n0000000173 00000 n\n0000000301 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n364\n%%EOF"
        content_type = "application/pdf"

        # Function to upload files for a single customer
        def upload_files_for_customer(customer_guid, filenames):
            def upload_single_file(filename):
                response = self.upload_file(filename, file_content, content_type)
                if response.status_code != 200:
                    logger.error(
                        f"File upload failed for {filename} (customer {customer_guid}): {response.status_code}")
                    return False
                response_data = response.json()
                if "message" not in response_data or response_data["message"] != "File uploaded SuccessFully":
                    logger.error(f"Upload message mismatch for {filename} (customer {customer_guid}): {response_data}")
                    return False
                logger.info(f"Uploaded and verified {filename} for customer {customer_guid} successfully.")
                return True

            # Use ThreadPoolExecutor to upload files concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_files_per_customer) as executor:
                futures = [executor.submit(upload_single_file, filename) for filename in filenames]
                results = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error during file upload for customer {customer_guid}: {e}")
                        results.append(False)
            return all(results)

        # Upload files for both customers concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_1 = executor.submit(upload_files_for_customer, self.customer_guid, customer_1_filenames)
            future_2 = executor.submit(upload_files_for_customer, customer_guid_2, customer_2_filenames)

            # Wait for both customers' uploads to complete
            customer_1_success = future_1.result()
            customer_2_success = future_2.result()

        # Verify that all files were uploaded successfully for both customers
        self.assertTrue(customer_1_success, "Not all files were uploaded and processed successfully for customer 1.")
        self.assertTrue(customer_2_success, "Not all files were uploaded and processed successfully for customer 2.")
        logger.info("Test for two customers uploading files simultaneously completed successfully.")


if __name__ == "__main__":
    unittest.main()
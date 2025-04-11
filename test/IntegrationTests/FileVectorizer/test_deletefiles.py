import logging
import os
import sys
import unittest
import requests
import subprocess
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from utils.api_utils import add_customer, create_test_token, create_token_without_org_id, create_token_without_org_role
from src.backend.lib.logging_config import log_format

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)


class TestDeleteFileAPI(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        logger.info("=== Setting up test environment for DeleteFile API ===")

        # Setup test customer and authentication
        customer_data = add_customer("test_org")
        self.valid_customer_guid = customer_data["customer_guid"]
        self.org_id = customer_data.get("org_id")
        self.token = create_test_token(org_id=self.org_id, org_role="org:admin")
        self.headers = {'Authorization': f'Bearer {self.token}'}

        # Upload a test file to delete
        if "test_full_file_lifecycle_with_realtime_monitoring" not in self._testMethodName:
            self.test_filename = "test_delete_file.txt"
            self._upload_test_file()

        logger.info(f"=== Setup process completed for test: {self._testMethodName} ===")

    def _upload_test_file(self):
        """Helper method to upload a test file"""
        url = f"{self.BASE_URL}/uploadFile"
        test_file = (self.test_filename, b"Test file content for deletion")
        response = requests.post(url, files={"file": test_file}, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Failed to setup test file")
        self.file_id = response.json().get("file_id")

    def test_delete_file_success(self):
        logger.info("Executing test_delete_file_success: Testing successful file deletion")

        url = f"{self.BASE_URL}/deletefile"
        params = {"filename": self.test_filename}

        response = requests.delete(url, headers=self.headers, params=params)

        logger.info(f"Response status: {response.status_code}, content: {response.text}")

        self.assertEqual(response.status_code, 200,
                         f"Expected 200 but got {response.status_code}")

        data = response.json()
        self.assertIn("message", data, "Response missing 'message' field")
        self.assertEqual(data["message"], "File marked for deletion",
                         "Unexpected success message")
        self.assertEqual(data["filename"], self.test_filename,
                         "Filename in response doesn't match request")

    def test_delete_nonexistent_file(self):
        logger.info("Executing test_delete_nonexistent_file: Testing deletion of non-existent file")

        url = f"{self.BASE_URL}/deletefile"
        params = {"filename": "nonexistent_file.txt"}

        response = requests.delete(url, headers=self.headers, params=params)

        logger.info(f"Response status: {response.status_code}, content: {response.text}")

        # Verify the response status code matches your API behavior
        self.assertEqual(response.status_code, 500,
                         f"Expected status code 500 but got {response.status_code}")

        # Verify the error message structure
        data = response.json()
        self.assertIn("detail", data, "Error detail missing from response")
        self.assertEqual(data["detail"], "Error processing delete request",
                         "Unexpected error message content")

    def test_delete_file_missing_filename(self):
        logger.info("Executing test_delete_file_missing_filename: Testing deletion without filename")

        url = f"{self.BASE_URL}/deletefile"

        response = requests.delete(url, headers=self.headers)  # No filename parameter

        logger.info(f"Response status: {response.status_code}, content: {response.text}")

        self.assertEqual(response.status_code, 422,  # FastAPI typically returns 422 for missing params
                         f"Expected 422 but got {response.status_code}")

        data = response.json()
        self.assertIn("detail", data, "Error detail missing")

    def test_delete_already_deleted_file(self):
        logger.info("Testing deletion of already deleted file")

        # First delete the file
        delete_url = f"{self.BASE_URL}/deletefile"
        params = {"filename": self.test_filename}
        first_response = requests.delete(delete_url, params=params, headers=self.headers)
        self.assertEqual(first_response.status_code, 200)

        # Try deleting again
        second_response = requests.delete(delete_url, params=params, headers=self.headers)
        logger.info(f"Second deletion response: {second_response.status_code}")

        # Should return 200 with "File already marked for deletion" message
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.json()["message"], "File already marked for deletion")

    def test_delete_without_token(self):
        logger.info("Executing test_download_without_token: Testing error handling for missing token")

        url = f"{self.BASE_URL}/deletefile"
        logger.info(f"Sending GET request to {url}")

        params = {"filename": self.test_filename}

        # Make the get request without a token
        response = requests.delete(url, params=params)
        logger.info(f"OUTPUT: Response status code: {response.status_code}")
        logger.info(f"OUTPUT: Response content: {response.text}")

        self.assertEqual(response.status_code, 401)
        response_json = response.json()
        self.assertEqual(response_json.get("detail"), "Authentication required")

    def test_corrupted_token(self):
        """Test API request with a corrupted authentication token."""
        headers = {"Authorization": "Bearer corrupted_token"}
        url = f"{self.BASE_URL}/deletefile"
        params = {"filename": self.test_filename}

        logger.info("Testing API request with corrupted token")
        response = requests.delete(url, params=params, headers=headers)
        self.assertEqual(response.status_code, 401, "Corrupted token should result in 401 Unauthorized")
        self.assertEqual(response.json()["detail"], "Authentication required", "Unexpected error message")

    def test_delete_files_token_without_org_role(self):
        logger.info("Testing download files API with a token missing org_role")

        customer_data = add_customer("test_org")
        org_id = customer_data.get("org_id")
        headers = {'Authorization': f'Bearer {create_token_without_org_role(org_id)}'}
        url = f"{self.BASE_URL}/deletefile"
        params = {"filename": self.test_filename}
        response = requests.delete(url, params=params, headers=headers)

        self.assertEqual(response.status_code, 403, "Expected status code 403 for missing org_role")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Forbidden: Insufficient role", "Unexpected error message")

    def test_delete_files_token_without_org_id(self):
        logger.info("Testing download files API with a token missing org_id")

        url = f"{self.BASE_URL}/deletefile"
        headers = {'Authorization': f'Bearer {create_token_without_org_id("org:admin")}'}
        params = {"filename": self.test_filename}
        response = requests.delete(url, params=params, headers=headers)

        # Expect 400 Bad Request
        self.assertEqual(response.status_code, 400, "Expected status code 400 for missing org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Org ID not found in token", "Unexpected error message")

    def test_delete_files_no_mapping_customer_guid(self):
        logger.info("Testing download files API with no mapping between org_id and customer_guid")

        # Create a new org_id without mapping it to a customer_guid
        org_id = "unmapped_org_id"
        token = create_test_token(org_id=org_id, org_role="org:admin")
        headers = {'Authorization': f'Bearer {token}'}

        url = f"{self.BASE_URL}/deletefile"
        params = {"filename": self.test_filename}
        response = requests.delete(url, params=params, headers=headers)

        self.assertEqual(response.status_code, 404, "Expected status code 404 for unmapped org_id")
        self.assertIn("detail", response.json(), "'detail' key not found in response")
        self.assertEqual(response.json()["detail"], "Invalid customer_guid provided", "Unexpected error message")

    def test_full_file_lifecycle_with_realtime_monitoring(self):
        logger.info("Starting test_full_file_lifecycle_with_realtime_monitoring")

        TEST_FILES = [
            "Googleprocess.pdf", "images1.png", "OptionMenu1.java",
            "upgrade.php", "Cen_files1.pdf", "Benefits.js",
            "PrinceBot.docx", "sample.xlsx", "SingleJsonFile.json",
            "_config.yaml", "ast_sci_data_tables_sample.pdf",
            "december.jpeg", "finalepisode.docx", "images.xlsx",
            "table.json", "sivu.jpeg", "Full_Pitch.pptx",
            "images1.png", "gitClass.cpp", "Cen_files1.pdf"
        ]
        TEST_DIR = os.path.join(os.path.dirname(__file__), "FilesTesting")

        if not os.path.exists(TEST_DIR):
            self.fail(f" Test directory '{TEST_DIR}' not found")

        customers = []
        for i in range(5):
            customer_data = add_customer(f"test_org_{i}")
            token = create_test_token(org_id=customer_data.get("org_id"), org_role="org:admin")
            headers = {'Authorization': f'Bearer {token}'}
            files_to_upload = TEST_FILES[:10] if i % 2 == 0 else TEST_FILES[10:]

            customers.append({
                "customer_guid": customer_data["customer_guid"],
                "org_id": customer_data["org_id"],
                "token": token,
                "headers": headers,
                "files_to_upload": files_to_upload,
                "uploaded_files": []
            })

        upload_url = f"{self.BASE_URL}/uploadFile"
        delete_url = f"{self.BASE_URL}/deletefile"
        embedding_status_url = f"{self.BASE_URL}/file/list"
        deletion_status_url = f"{self.BASE_URL}/files/deletionstatus"

        logger.info("====Uploading 50 Files (10 per customer) ====")
        for idx, customer in enumerate(customers):
            logger.info(f"Customer {idx + 1}: Uploading {len(customer['files_to_upload'])} files...")

            for filename in customer["files_to_upload"]:
                file_path = os.path.join(TEST_DIR, filename)
                if not os.path.exists(file_path):
                    logger.warning(f"File {filename} not found, skipping")
                    continue

                with open(file_path, 'rb') as file:
                    response = requests.post(
                        upload_url,
                        files={"file": (filename, file)},
                        headers=customer["headers"]
                    )

                self.assertEqual(response.status_code, 200, f"Failed to upload {filename}")
                file_id = response.json().get("file_id")
                customer["uploaded_files"].append((filename, file_id))
                logger.info(f"Uploaded {filename} (ID: {file_id})")

            self.assertEqual(
                len(customer["uploaded_files"]), 10,
                f"Customer {idx + 1} has {len(customer['uploaded_files'])} files (expected 10)"
            )

        logger.info("==== Monitoring Embedding Status ====")
        for idx, customer in enumerate(customers):
            logger.info(f"Customer {idx + 1}: Checking embedding progress...")
            start_time = time.time()

            while True:
                response = requests.get(
                    embedding_status_url,
                    headers=customer["headers"],
                    params={"page": 1, "page_size": 100}
                )
                self.assertEqual(response.status_code, 200)

                relevant_status = [
                    f for f in response.json()
                    if f["filename"] in dict(customer["uploaded_files"])
                    and f["embeddingstatus"] != "SUCCESS"
                ]

                # Detailed status logging
                logger.info(f"Customer {idx + 1} - {len(relevant_status)}/{len(customer['uploaded_files'])} files:")
                for file_status in relevant_status:
                    logger.info(
                        f"filename: {file_status.get('filename')} | "
                        f"file_id: {file_status.get('fileid')} | "
                        f"embeddingstatus: {file_status.get('embeddingstatus')}"
                    )

                if all(f["embeddingstatus"] == "SUCCESS" for f in relevant_status):
                    logger.info(f"Customer {idx + 1}: All files embedded in {time.time() - start_time:.1f}s!")
                    break

                time.sleep(2)  # Poll every second

        logger.info("==== Deleting Files + Vectorizer Control ====")
        for idx, customer in enumerate(customers):
            logger.info(f"Customer {idx + 1}: Initiating deletion...")

            # Mark files for deletion
            for filename, _ in customer["uploaded_files"]:
                response = requests.delete(
                    delete_url,
                    params={"filename": filename},
                    headers=customer["headers"]
                )
                self.assertEqual(response.status_code, 200, f"Failed to delete {filename}")

            # Monitor deletion with vectorizer control
            last_control_time = time.time()
            control_interval = 30  # seconds
            start_time = time.time()

            while True:
                try:
                    current_time = time.time()

                    # Vectorizer control (every 30s)
                    if current_time - last_control_time >= control_interval:
                        logger.info("Stopping file vectorizer...")
                        self.control_file_vectorizer()
                        last_control_time = current_time

                    # Check deletion status
                    response = requests.get(
                        deletion_status_url,
                        headers=customer["headers"],
                        params={"page": 1, "page_size": 100}
                    )
                    self.assertEqual(response.status_code, 200)

                    # Log detailed deletion status
                    pending_files = [
                        f for f in response.json()
                        if f["filename"] in dict(customer["uploaded_files"])
                           and f["deletion_status"] != "DELETION_COMPLETED"
                    ]

                    logger.info(f"Customer {idx + 1} - {len(pending_files)} files pending:")
                    for file in pending_files:
                        logger.info(
                            f"filename: {file.get('filename')} | "
                            f"file_id: {file.get('file_id')} | "
                            f"deletion_status: {file.get('deletion_status')}"
                        )

                    if not pending_files:
                        logger.info(f"Customer {idx + 1}: All files deleted in {time.time() - start_time:.1f}s!")
                        break

                    time.sleep(2)  # Poll every second

                except Exception as e:
                    logger.error(f"Deletion monitoring error: {str(e)}")
                    time.sleep(5)  # Longer pause on error

        logger.info("====Final Verification ====")
        for idx, customer in enumerate(customers):
            response = requests.get(
                deletion_status_url,
                headers=customer["headers"],
                params={"page": 1, "page_size": 100}
            )
            self.assertEqual(response.status_code, 200)

            undeleted_files = [
                f for f in response.json()
                if f["filename"] in dict(customer["uploaded_files"])
                   and f["deletion_status"] != "DELETION_COMPLETED"
            ]

            self.assertListEqual(
                undeleted_files, [],
                f"Customer {idx + 1} has {len(undeleted_files)} undeleted files"
            )

    def control_file_vectorizer(self):
        container_name = "chat_service"
        try:
            subprocess.run( ["docker", "exec", container_name, "pkill", "-9", "-f","file_vectorize_main"],check=True)
            logger.info("Successfully killed file_vectorize_main process with pkill -9")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to kill file_vectorize_main: {e}")

if __name__ == '__main__':
    unittest.main()

import logging
import os
import sys
import unittest
import requests
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from utils.api_utils import add_customer, create_test_token
from src.backend.lib.logging_config import get_primitivechat_logger

logger = get_primitivechat_logger(__name__)

class TestFileLifecycleAPI(unittest.TestCase):
    def setUp(self):
        self.BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"
        self.TEST_DIR = os.path.join(os.path.dirname(__file__), "FilesTesting")

        if not os.path.exists(self.TEST_DIR):
            self.fail(f"Test directory '{self.TEST_DIR}' not found")

        self.TEST_FILES = [
            "Googleprocess.pdf", "images1.png", "OptionMenu1.java", "actions.yaml", "alarm_clock.py",
            "upgrade.php", "KabilanA.pdf", "Benefits.js", "CEN_files2.pdf", "Project_Flow.docx",
            "download_files2.pdf", "images_1.jpg", "ATM.docx", "images_2.jpg", "Karthi_CV_Resume.pdf",
            "pasted_image.png", "PrinceBot.docx", "sample.xlsx", "SingleJsonFile.json", "_config.yaml",
            "ast_sci_data_tables_sample.pdf", "december.jpeg", "finalepisode.docx", "images.xlsx", "table.json",
            "sivu.jpeg", "Full_Pitch.pptx", "images_1.jpg", "gitClass.cpp", "Cen_files1.pdf",
            "formatedpage.docx", "CEN_files_3.pdf", "DataDocumentationfile.json", "images_3.jpg", "cloud_computing_books.pptx",
            "sample_2.json", "PhaseFinalCopy.docx", "OPERATING.pptx", "CEN_files_8.pdf", "AllChartsFormatted.json",
            "CEN_files_4.pdf", "cyber_security_table.pptx", "CEN_files_5.pdf", "CEN_files_6.pdf", "NewFIleExtract.json",
            "CEN_files_7.pdf", "ss.jpeg", "A_basic_paragraph.png", "downloaded_files1.pdf", "downloaded_files3.pdf"
        ]

        self.customers = []
        for i in range(5):
            customer_data = add_customer(f"test_org_{i}")
            token = create_test_token(org_id=customer_data.get("org_id"), org_role="org:admin")
            headers = {'Authorization': f'Bearer {token}'}
            files_to_upload = self.TEST_FILES[i * 10:(i + 1) * 10]

            self.customers.append({
                "customer_guid": customer_data["customer_guid"],
                "org_id": customer_data["org_id"],
                "token": token,
                "headers": headers,
                "files_to_upload": files_to_upload,
                "uploaded_files": []
            })

    def test_file_upload_and_embedding_monitoring(self):
        upload_url = f"{self.BASE_URL}/uploadFile"
        embedding_status_url = f"{self.BASE_URL}/file/list"

        logger.info("Uploading and monitoring files for each customer")

        for idx, customer in enumerate(self.customers):
            logger.info(f"Customer {idx + 1}: Uploading files")

            for filename in customer["files_to_upload"]:
                file_path = os.path.join(self.TEST_DIR, filename)

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

        logger.info("Checking embedding status for each customer")
        for idx, customer in enumerate(self.customers):
            start_time = time.time()

            while True:
                response = requests.get(
                    embedding_status_url,
                    headers=customer["headers"],
                    params={"page": 1, "page_size": 100}
                )
                self.assertEqual(response.status_code, 200)
                data = response.json()

                # Assert that the number of files returned is 10
                self.assertEqual(len(data), 10, f"Expected 10 files but got {len(data)}")

                relevant_status = [
                    f for f in data
                    if f["filename"] in dict(customer["uploaded_files"])
                ]

                logger.info(f"Customer {idx + 1} - {len(relevant_status)} files:")
                for file_status in relevant_status:
                 logger.info(
                        f"file_id: {file_status.get('fileid')} | "
                        f"filename: {file_status.get('filename')} | "
                        f"embeddingstatus: {file_status.get('embeddingstatus')}"
                )

                if all(f["embeddingstatus"] == "SUCCESS" for f in relevant_status):
                    logger.info(f"Customer {idx + 1}: All files embedded in {time.time() - start_time:.1f}s")
                    break

                time.sleep(3)

    def tearDown(self):
        logger.info(f"=== Tear down completed for test: {self._testMethodName} ===")


if __name__ == '__main__':
    unittest.main()

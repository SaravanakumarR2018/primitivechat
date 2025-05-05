import json
import sys
import unittest
import logging
import requests
import os
import shutil
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from utils.api_utils import add_customer, create_test_token
from src.backend.embedding.extract_file.extract_file import UploadFileForChunks
from src.backend.weaviate.weaviate_manager import WeaviateManager

from src.backend.lib.logging_config import get_primitivechat_logger

# Setup logging configuration
logger = get_primitivechat_logger(__name__)

TEST_FILES = ["Googleprocess.pdf", "images_1.jpg", "Project_Flow.docx", "OPERATING.pptx","december.jpeg",
              "sample.xlsx", "A_basic_paragraph.png", "NewFIleExtract.json", "Benefits.js", "upgrade.php",
              "alarm_clock.py", "actions.yaml", "OptionMenu1.java"]

TEST_DIR = os.path.join(os.path.dirname(__file__), "FilesTesting")
OUTPUT_DIR = "FilesTestingOutput"


class FileExtractionHelper:

    @staticmethod
    def extract_file_content(input_file_path: str, output_dir: str = None, customer_guid: str = None):

        customer_guid = customer_guid
        filename = os.path.basename(input_file_path)

        processor = UploadFileForChunks(test_mode=True)

        try:

            processor.extract_file(customer_guid, filename, local_path=input_file_path)

            # Simulate upload workflow
            local_path = f"/tmp/{customer_guid}/{filename}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            shutil.copy2(input_file_path, local_path)

            processor.extract_file(customer_guid, filename, local_path=local_path)
            output_file_path = f"/tmp/{customer_guid}/{filename}.rawcontent"

            with open(output_file_path, 'r', encoding='utf-8') as f:
                extracted_content = f.read()

            final_output_path = output_file_path

            if output_dir:
                new_output_path = os.path.join(output_dir, f"{filename}.rawcontent")
                os.makedirs(output_dir, exist_ok=True)
                shutil.copy2(output_file_path, new_output_path)
                output_file_path = new_output_path

            return final_output_path, extracted_content, customer_guid

        except Exception as e:
            raise Exception(f"File extraction failed: {str(e)}")


class TestFileLifecycleWithMonitoring(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.weaviate = WeaviateManager()

        # Create test customer
        self.customer_data = add_customer("test_org_single")
        self.customer_guid = self.customer_data["customer_guid"]

        # Generate auth token
        self.headers = {
            'Authorization': f'Bearer {create_test_token(
                org_id=self.customer_data["org_id"],
                org_role="org:admin"
            )}'
        }

    def test_full_lifecycle(self):

        # 1. Upload all test files
        uploaded_files = []
        for filename in TEST_FILES:
            file_path = os.path.join(TEST_DIR, filename)

            with open(file_path, 'rb') as f:
                response = requests.post(
                    f"{self.BASE_URL}/uploadFile",
                    files={"file": (filename, f)},
                    headers=self.headers
                )
            self.assertEqual(response.status_code, 200)
            uploaded_files.append((filename, response.json().get("file_id")))

            # 2. Monitor embedding status
            self._monitor_embedding_status(uploaded_files)

            # extract to get .rawcontent
            output_path, extracted_content, _ = FileExtractionHelper.extract_file_content(
                file_path,
                output_dir=OUTPUT_DIR,
                customer_guid=self.customer_guid
            )

            # Validate extraction
            self.assertTrue(os.path.exists(output_path))
            extracted_data = json.loads(extracted_content)
            self.assertIsInstance(extracted_data, list)

            # 4. Validate each page separately against Weaviate data
            self._validate_pages(filename)

    def _monitor_embedding_status(self, uploaded_files):
        """Simplified but detailed embedding monitor"""
        logger.info(f"Starting embedding monitor for {len(uploaded_files)} files")
        start_time = time.time()
        expected_file_count = len(uploaded_files)

        while True:
            response = requests.get(
                f"{self.BASE_URL}/file/list",
                headers=self.headers,
                params={"page": 1, "page_size": 100}
            )

            if response.status_code != 200:
                time.sleep(3)
                continue

            response_data = response.json()

            # Validate file count
            if len(response_data) != expected_file_count:
                logger.warning(f"File count mismatch: Expected {expected_file_count}, got {len(response_data)}")
                time.sleep(3)
                continue

            # Get relevant files and log details
            relevant_files = [
                f for f in response_data
                if f["filename"] in dict(uploaded_files)
            ]

            # ADD DETAILED LOGGING HERE
            for file_status in relevant_files:
                logger.info(
                    f"• {file_status.get('filename')}: "
                    f"{file_status.get('fileid')} | "
                    f"Status: {file_status.get('embeddingstatus')}"
                )

            # Check completion
            completed = sum(1 for f in relevant_files if f.get("embeddingstatus") == "SUCCESS")
            if completed == expected_file_count:
                logger.info(f"All files completed in {time.time() - start_time:.1f}s")
                break

            time.sleep(3)

    def _validate_pages(self, filename):
        """
        Validate each page individually by comparing extracted file content to Weaviate uploaded data.
        """
        try:
            with open(os.path.join(OUTPUT_DIR, f"{filename}.rawcontent"), 'r', encoding='utf-8') as f:
                extracted_pages = json.load(f)
        except Exception as e:
            self.fail(f"Failed to load extracted content for {filename}: {str(e)}")

        class_name = self.weaviate.generate_weaviate_class_name(self.customer_guid)
        ext = os.path.splitext(filename)[1].lower()

        for page in extracted_pages:
            page_num = page["metadata"]["page_number"]
            extracted_text = page["text"]

            try:
                result = self.weaviate.client.query.get(
                    class_name,
                    ["text", "page_numbers", "filename"]
                ).with_where({
                    "operator": "And",
                    "operands": [
                        {"path": ["filename"], "operator": "Equal", "valueText": filename},
                        {"path": ["page_numbers"], "operator": "ContainsAny", "valueInt": [page_num]}
                    ]
                }).do()
            except Exception as e:
                self.fail(f"Error querying Weaviate for {filename} page {page_num}: {str(e)}")

            if not result or not isinstance(result, dict):
                self.fail(f"Invalid Weaviate response format for {filename} page {page_num}")

            data = result.get("data", {}).get("Get", {}).get(class_name, [])
            if not isinstance(data, list):
                if isinstance(data, dict):
                    data = [data]
                else:
                    self.fail(f"Invalid Weaviate items format for {filename} page {page_num}")

            if not data:
                self.fail(f"No Weaviate results for {filename} page {page_num}")

            norm_extracted = " ".join(extracted_text.strip().split()).lower()
            found = False

            if ext == ".pptx":
                combined_text = " ".join(
                    [" ".join(record.get("text", "").strip().split()).lower() for record in data]
                )
                if norm_extracted in combined_text or combined_text in norm_extracted:
                    found = True
            else:
                for record in data:
                    record_text = record.get("text", "")
                    norm_record = " ".join(record_text.strip().split()).lower()
                    if norm_record and (norm_record in norm_extracted or norm_extracted in norm_record):
                        found = True
                        break

            if not found:
                self.fail(f"Extracted text for {filename} page {page_num} not found in Weaviate upload")
            else:
                logger.info(f"Successfully validated {filename} page {page_num}")

    def tearDown(self):
        logger.info("Tearing down test")
        if os.path.exists(OUTPUT_DIR):
            if os.listdir(OUTPUT_DIR):  # Check if directory is not empty
                logger.info(f"Removing {len(os.listdir(OUTPUT_DIR))} files from {OUTPUT_DIR}")
            shutil.rmtree(OUTPUT_DIR)
            logger.info(f"Removed output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    unittest.main()
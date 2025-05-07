import json
import sys
import unittest
import logging
import weaviate
from weaviate import Client
import requests
import os
import uuid
import shutil
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from utils.api_utils import add_customer, create_test_token

from src.backend.lib.logging_config import get_primitivechat_logger


# Setup logging configuration
logger = get_primitivechat_logger(__name__)

TEST_FILES = ["Full_Pitch.pptx","december.jpeg","Googleprocess.pdf","images_1.jpg","Project_Flow.docx",
              "sample.xlsx","A_basic_paragraph.png","NewFIleExtract.json","Benefits.js","upgrade.php",
              "alarm_clock.py","actions.yaml","OptionMenu1.java"]

TEST_DIR = os.path.join(os.path.dirname(__file__), "FilesTesting")
OUTPUT_DIR = "FilesTestingOutput"


class TestFileLifecycleWithMonitoring(unittest.TestCase):
    BASE_URL = f"http://{os.getenv('CHAT_SERVICE_HOST')}:{os.getenv('CHAT_SERVICE_PORT')}"

    def setUp(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.customer_data = add_customer("test_org_single")
        self.customer_guid = self.customer_data["customer_guid"]
        self.headers = {'Authorization': f'Bearer {create_test_token(org_id=self.customer_data["org_id"],org_role="org:admin")}'}

    def test_full_lifecycle(self):

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

            self._monitor_embedding_status(uploaded_files)

            self.assertTrue(os.path.exists(file_path), f"Test file not found at {file_path}")

            container_path = f"/tmp/{self.customer_guid}/{filename}"
            os.makedirs(os.path.dirname(container_path), exist_ok=True)
            shutil.copy2(file_path, container_path)

            response = requests.post(
                f"{self.BASE_URL}/extractfile",
                json={
                "filename": filename,
                "customer_guid": self.customer_guid,
                "local_path": container_path
                }
            )
            self.assertEqual(response.status_code, 200)
            response_data = response.json()

            extracted_content = response_data.get("rawcontent")
            self.assertIsNotNone(extracted_content, f"No extracted content returned for {filename}")

            output_path = os.path.join(OUTPUT_DIR, f"{filename}.rawcontent")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(extracted_content, f)
     
            logger.info(f"Extracted raw content for {filename} saved at {output_path}")
            self.assertTrue(len(json.dumps(extracted_content).strip()) > 0, f"No extracted content found for {filename}")

            self._validate_pages(filename, extracted_content)
 

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
      
            if len(response_data) != expected_file_count:
                logger.warning(f"File count mismatch: Expected {expected_file_count}, got {len(response_data)}")
                time.sleep(3)
                continue

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
                logger.info(f"All files completed in {time.time()-start_time:.1f}s")
                break

            time.sleep(3)

    def generate_weaviate_class_name(self,customer_guid):

        return f"Customer_{customer_guid.replace('-', '_')}"        

    def _validate_pages(self, filename, extracted_pages):
        class_name = self.generate_weaviate_class_name(self.customer_guid)
    
        # Initialize Weaviate client
        client = Client(f"http://{os.getenv('WEAVIATE_HOST')}:{os.getenv('WEAVIATE_PORT')}")
    
        for page in extracted_pages:
            page_num = page["metadata"]["page_number"]
            extracted_text = page["text"]
        
            try:
                result = client.query\
                    .get(class_name, ["text", "page_numbers", "filename"])\
                    .with_where({
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
            found = False  # Initialize found flag

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

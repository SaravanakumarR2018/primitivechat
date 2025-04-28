import os
import logging
from src.backend.minio.minio_manager import MinioManager
from src.backend.lib.logging_config import get_primitivechat_logger

# Configure Logging
logger = get_primitivechat_logger(__name__)


class LocalFileDownloadAndUpload:
    def __init__(self):
        self.minio_manager = MinioManager()

    def download_and_save_file(self, customer_guid: str, filename: str):
        try:
            file_pointer = self.minio_manager.download_file(customer_guid, filename)

            # Check if file_pointer is valid
            if isinstance(file_pointer, dict) and "error" in file_pointer:
                logger.error(f"Error retrieving file: {file_pointer['error']}")
                raise Exception(f"Error retrieving file: {file_pointer['error']}")

            local_path = f"/tmp/{customer_guid}/{filename}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            with open(local_path, "wb") as local_file:
                for chunk in file_pointer.stream(32 * 1024):
                    local_file.write(chunk)

            logger.info(f"File '{filename}' downloaded and stored at '{local_path}'")
            return local_path
        except Exception as e:
            logger.error(f"Unexpected error during file download '{filename}': {e}")
            raise Exception(f"File download failed: {e}")

    def upload_extracted_content(self, customer_guid: str, filename: str, output_file: str):

        try:
            with open(output_file, "rb") as file_pointer:
                self.minio_manager.upload_file(customer_guid, f"{filename}.txt", file_pointer)

            logger.info(f"Raw content file '{filename}.txt' uploaded to MinIO bucket '{customer_guid}'")
        except Exception as e:
            logger.error(f"Failed to upload raw content: {e}")
            raise Exception(f"File upload failed: {e}")
    
    def upload_chunked_content(self, customer_guid: str, filename: str, output_file: str):

        try:
            with open(output_file, "rb") as file_pointer:
                self.minio_manager.upload_file(customer_guid, f"{filename}.chunked.txt", file_pointer)

            logger.info(f"Raw content file '{filename}.chunked.txt' uploaded to MinIO bucket '{customer_guid}'")
        except Exception as e:
            logger.error(f"Failed to upload raw content: {e}")
            raise Exception(f"File upload failed: {e}")
        

import logging
import os

from minio import Minio
from minio.error import S3Error

#Configure logging
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')
logger=logging.getLogger(__name__)

class MinioManager:
    def __init__(self):

        try:
            self.client=Minio(
                os.getenv('MINIO_HOST','minio:9000'),
                access_key=os.getenv('MINIO_ROOT_USER','minioadmin'),
                secret_key=os.getenv('MINIO_ROOT_PASSWORD','minioadmin'),
                secure=False
            )
            logger.info("Successfully connected to MinIO.")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO Connection:{e}")
            raise e

    def add_storage_bucket(self,bucket_name):
        #create a new storage bucket in MinIO

        try:
            if not self.client.bucket_exists(bucket_name):
                logger.debug(f"Creating MinIO bucket:{bucket_name}")
                self.client.make_bucket(bucket_name)
                logger.info(f"MinIO bucket '{bucket_name}' created successfully")
                return "Created Successfully"
            else:
                logger.info(f"MinIO bucket '{bucket_name}' already exists")
        except S3Error as e:
            logger.error(f"Error creating MinIO bucket '{bucket_name}' : {e}")
            return f"Failed to create bucket: {e}"
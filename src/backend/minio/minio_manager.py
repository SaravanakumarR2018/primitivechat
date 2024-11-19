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

    #upload a file to the specified MinIO bucket
    def upload_file(self,bucket_name,filename,file_data):
        logger.debug(f"Starting file upload. Bucket:'{bucket_name}', File:'{filename}'")

        try:
            if not self.client.bucket_exists(bucket_name):
                logger.info(f"Bucket '{bucket_name}' does not exist")

            self.client.put_object(
                bucket_name=bucket_name,
                object_name=filename,
                data=file_data,
                length=-1,
                part_size=10 * 1024 * 1024,
            )
            logger.info(f"File '{filename}'upload successfully to bucket'{bucket_name}'")
            return {"File Uploaded Successfully"}
        except S3Error as e:
            logger.error(f"Error uploading file '{filename}' to MinIO bucket '{bucket_name}':{e}")
            return {"error":f"Failed to upload file:{e}"}
        except Exception as e:
            logger.error(f"Unexpected error during file upload:{e}")
            return {"error":f"An error occurred:{e}"}

    #list the files in the MinIO bucket
    def list_files(self, bucket_name):
        try:
            if not self.client.bucket_exists(bucket_name):
                logger.error(f"Bucket '{bucket_name}' does not exist.")
                raise Exception(f"Bucket '{bucket_name}' does not exist.")

            objects = self.client.list_objects(bucket_name)
            file_list = [obj.object_name for obj in objects]
            if not file_list:
                logger.info(f"No files found in bucket '{bucket_name}'.")
            return file_list
        except S3Error as e:
            logger.error(f"Error listing files in bucket '{bucket_name}': {e}")
            return {"error":f"Error listing files in bucket {bucket_name}"}
        except Exception as e:
            logger.error(f"Unexpected error while listing files: {e}")
            return f"Unexpected error while listing the files:'{bucket_name}':{e}"

    #Download a file from MinIO bucket
    def download_file(self,bucket_name,filename):
        try:
            response=self.client.get_object(bucket_name,filename)

            logger.info(f"File '{filename}' Downloaded Successfully from bucket '{bucket_name}'")
            return response

        except S3Error as e:
            logger.error(f"Error downloading file '{filename}' from bucket '{bucket_name}'{e}")
            return {"error":f"Failed to download file: {e}"}

        except Exception as e:
            logger.error(f"Unexpected error during file download:{e}")
            return {"error":f"An error occurred:{e}"}


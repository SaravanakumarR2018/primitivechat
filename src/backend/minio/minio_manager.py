import logging
import os
from fastapi import HTTPException

from minio import Minio
from minio.error import S3Error

from src.backend.lib.logging_config import log_format
from src.backend.lib.singleton_class import Singleton

from src.backend.lib.logging_config import get_primitivechat_logger


#Configure logging
logger = get_primitivechat_logger(__name__)

class MinioManager(metaclass=Singleton):
    def __init__(self):
        minio_host = os.getenv('MINIO_HOST')
        minio_port = os.getenv('MINIO_SERVER_PORT')
        minio_user = os.getenv('MINIO_ROOT_USER')
        minio_password = os.getenv('MINIO_ROOT_PASSWORD')

        # Log the retrieved environment variables for debugging
        logger.debug(f"MinIO Host: {minio_host}, Port: {minio_port}, User: {minio_user}, Password: {minio_password}")

        if not all([minio_host, minio_port, minio_user, minio_password]):
            raise ValueError("One or more MinIO environmental variables are not set")

        try:
            self.client = Minio(
                f"{minio_host}:{minio_port}",
                access_key=minio_user,
                secret_key=minio_password,
                secure=False
            )
            logger.info("Successfully connected to MinIO.")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO Connection: {e}")
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
                raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

            objects = self.client.list_objects(bucket_name)
            file_list = [obj.object_name for obj in objects]
            if not file_list:
                logger.info(f"No files found in bucket '{bucket_name}'.")
            return file_list
        except S3Error as e:
            logger.error(f"Error listing files in bucket '{bucket_name}': {e}")
            return {"error":f"Error listing files in bucket {bucket_name}"}
        except Exception as e:
            if isinstance(e,HTTPException):
                logger.error(f"Invalid customer_guid:{e.detail}")
                raise e
            else:
                logger.error(f"Unexpected error while listing a files: {e}")
                raise HTTPException(status_code=500, detail=f"Unexpected error while listing a files in bucket '{bucket_name}'")

    #Download a file from MinIO bucket
    def download_file(self,bucket_name,filename):
        try:
            if not self.client.bucket_exists(bucket_name):
                logger.error(f"Bucket '{bucket_name}' does not exist.")
                raise HTTPException(status_code=404, detail="Invalid customer_guid provided")

            response = self.client.get_object(bucket_name, filename)
            if not response:
                logger.error(f"File '{filename}' does not exist in bucket '{bucket_name}'")
                raise HTTPException(status_code=400, detail="File does not exist in the specified bucket")

            logger.info(f"File '{filename}' downloaded successfully from bucket '{bucket_name}'.")
            return response

        except S3Error as e:
            logger.error(f"Error downloading file '{filename}' from bucket '{bucket_name}'{e}")
            return {"error":f"Failed to download file: {e}"}

        except Exception as e:
            if isinstance(e, HTTPException):
                if e.status_code==404:
                    logger.error(f"Invalid customer_guid:{e.detail}")
                    raise e
                else:
                    logger.error(f"File '{filename}' does not exist in bucket '{bucket_name}': {e}")
                    raise e
            else:
                logger.error(f"Unexpected error during file download:{e}")
                return {"error":f"An error occurred:{e}"}

    def delete_file(self, bucket_name, filename):
        try:
            # Check if bucket exists
            if not self.client.bucket_exists(bucket_name):
                logger.error(f"Bucket '{bucket_name}' does not exist.")
                return {"error": f"Bucket '{bucket_name}' does not exist."}

            # Remove the file from the bucket
            self.client.remove_object(bucket_name, filename)
            logger.info(f"File '{filename}' deleted successfully from bucket '{bucket_name}'.")
            return {"message": "File deleted successfully"}

        except S3Error as e:
            logger.error(f"Error deleting file '{filename}' from bucket '{bucket_name}': {e}")
            return {"error": f"Failed to delete file: {e}"}

        except Exception as e:
            logger.error(f"Unexpected error during file deletion: {e}")
            return {"error": f"An error occurred: {e}"}


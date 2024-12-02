import logging
import os
from fastapi import FastAPI, HTTPException,Form
from src.backend.minio.minio_manager import MinioManager

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()

# MinIO Manager
minio_manager = MinioManager()

@app.post("/downloadFile", tags=["File Management"])
async def download_file(customer_guid: str = Form(...),filename: str = Form(...)):

    logger.debug(f"Request received for downloading file '{filename}'")

    # Specify local directory
    local_directory = "/home/kabilan-a/Documents/Public"
    os.makedirs(local_directory, exist_ok=True)

    try:
        # Validate that directory exists and is writable
        if not os.access(local_directory, os.W_OK):
            logger.error(f"Write access to directory '{local_directory}' is not permitted.")
            raise HTTPException(status_code=500, detail=f"Cannot write to directory: {local_directory}")

        #filename to avoid path traversal
        file_name = os.path.basename(filename)
        logger.debug(f"Sanitized filename: {file_name}")

        # Construct full path for local file
        local_path = os.path.join(local_directory, file_name)
        logger.debug(f"Local path for saving the file: {local_path}")

        # Download the file from MinIO
        file_object = minio_manager.download_file(bucket_name=customer_guid, filename=file_name)
        if not file_object:
            logger.error(f"File '{file_name}' not found in MinIO bucket '{customer_guid}'.")
            raise HTTPException(status_code=404, detail=f"File '{file_name}' not found in MinIO bucket.")

        # Write file to the local directory
        with open(local_path, "wb") as local_file:
            for chunk in file_object.stream(32 * 1024):
                local_file.write(chunk)

        # Read the file back to confirm it exists and is accessible
        logger.debug(f"Reading back the file: {local_path}")
        with open(local_path, "rb") as local_file:
            file_content = local_file.read()  # Ensure the file can be read
            logger.debug(f"Successfully read file: {local_path}")
            logger.info(f"File content size: {len(file_content)} bytes")

        logger.info(f"File '{file_name}' successfully downloaded to '{local_path}'.")

        # Return a success response
        return {
            "message": f"File '{file_name}' successfully written, read, and is available at '{local_directory}'",
            "file_path": local_path
        }

    except HTTPException as http_error:
        logger.error(f"HTTPException occurred: {http_error.detail}")
        raise http_error  # Reraise for FastAPI to handle

    except Exception as e:
        logger.error(f"Unexpected error during file download: {e}")
        raise HTTPException(status_code=500,detail=f"An unexpected error occurred: {e}")

    finally:
        logger.debug("Exiting download_file()")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
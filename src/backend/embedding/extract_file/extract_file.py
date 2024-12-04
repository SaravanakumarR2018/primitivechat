import os
import logging
import magic  # Used to detect file type
from src.backend.minio.minio_manager import MinioManager
import easyocr
import numpy as np
import pdfplumber
import json

# Configure Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class UploadFileForChunks:
    def __init__(self):
        self.minio_manager = MinioManager()
        self.file_extract = FileExtractor()

    def download_and_save_file(self, customer_guid: str, filename: str):

        try:
            file_pointer = self.minio_manager.download_file(customer_guid, filename)

            # Check if file_pointer is valid
            if isinstance(file_pointer, dict) and "error" in file_pointer:
                logger.error(f"Error retrieving file: {file_pointer['error']}")
                raise Exception(f"Error retrieving file: {file_pointer['error']}")

            local_path = f"/tmp/{customer_guid}/{filename}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Save file locally from stream
            with open(local_path, "wb") as local_file:
                for chunk in file_pointer.stream(32 * 1024):  # Stream in 32 KB chunks
                    local_file.write(chunk)

            logger.info(f"File '{filename}' downloaded and stored at '{local_path}'")
            return local_path
        except Exception as e:
            logger.error(f"Unexpected error during file download '{filename}': {e}")
            raise Exception(f"File download failed: {e}")

    def upload_extracted_content(self, customer_guid: str, filename: str, output_file: str):

        try:
            with open(output_file, "rb") as file_pointer:
                self.minio_manager.upload_file(customer_guid, f"{filename}.rawcontent", file_pointer)

            logger.info(f"Raw content file '{filename}.rawcontent' uploaded to MinIO bucket '{customer_guid}'")
        except Exception as e:
            logger.error(f"Failed to upload raw content: {e}")
            raise Exception(f"File upload failed: {e}")

    def extract_file(self, customer_guid: str, filename: str):
        logger.info(f"Extracting PDF file '{filename}' for customer '{customer_guid}'")

        #Download and save file locally
        local_path = self.download_and_save_file(customer_guid, filename)

        #Verify file type
        try:
            file_type = self.file_extract.detect_file_type(local_path)
            if file_type != ".pdf":
                logger.error(f"File '{filename}' is not a valid PDF (detected type: {file_type})")
                raise Exception("Invalid file type: Uploaded file is not a PDF.")
            logger.info(f"Verified file '{filename}' as a valid PDF.")
        except Exception as e:
            logger.error(f"Error detecting file type for '{filename}': {e}")
            raise Exception("File type detection failed.")

        #Extract PDF content
        try:
            output_file = self.file_extract.extract_pdf_content(customer_guid, local_path, filename)
            # Step 4: Upload extracted content
            self.upload_extracted_content(customer_guid, filename, output_file)
            return {"message": "PDF extracted and uploaded successfully."}
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise Exception(f"File extraction failed.{e}")


class FileExtractor:
    def __init__(self):
        self.ocr_reader = easyocr.Reader(['en'], gpu=False)

    def detect_file_type(self, file_path: str):
        MIME_TO_EXTENSION = {"application/pdf": ".pdf"}
        try:
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(file_path)
            extension = MIME_TO_EXTENSION.get(file_type)
            if not extension:
                logger.error(f"Unsupported file type detected: {file_type}")
                raise Exception("Unsupported file type: This system only supports PDF files.")
            return extension
        except Exception as e:
            logger.error(f"Error detecting file type for {file_path}: {e}")
            raise Exception(f"File type detection failed: {e}")

    def format_table_as_text(self, table):
        try:
            if table is None or not table:
                logger.error("Empty or None table received for formatting.")
                return "Empty table"

            table = [[str(item) if item is not None else "" for item in row] for row in table]
            max_columns = max(len(row) for row in table)
            table = [row + [""] * (max_columns - len(row)) for row in table]  # Fill missing cells with empty strings
            col_widths = [max(len(str(item)) for item in col) for col in zip(*table)]
            row_format = " | ".join(f"{{:<{w}}}" for w in col_widths)
            formatted_table = "\n".join(row_format.format(*row) for row in table)
            return formatted_table.strip()

        except Exception as e:
            logger.error(f"Error formatting table: {e}")
            raise Exception(f"Table formatting failed: {e}")

    def extract_pdf_content(self, customer_guid: str, file_path: str, filename: str):
        results = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    page_elements = []

                    for block in page.extract_words():
                        page_elements.append({
                            "type": "text",
                            "content": block["text"],
                            "x0": block["x0"],
                            "y0": block["top"]
                        })

                    for table in page.extract_tables():
                        table_text = self.format_table_as_text(table)
                        bbox = page.find_tables()[0].bbox  # Get bounding box for the first table
                        page_elements.append({
                            "type": "table",
                            "content": table_text,
                            "x0": bbox[0],
                            "y0": bbox[1]
                        })
                    if not page.extract_text():
                        pil_image = page.to_image(resolution=300).original
                        numpy_image = np.array(pil_image)
                        ocr_result = self.ocr_reader.readtext(numpy_image)
                        page_elements.append({
                            "type": "image",
                            "content":ocr_result.strip(),
                            "x0": 0,  # Assuming full-page images
                            "y0": 0
                        })
                    page_elements.sort(key=lambda e: (e["y0"], e["x0"]))
                    page_text = " ".join([element["content"] for element in page_elements])
                    results.append({
                            "metadata": {"page_number": page_number},
                            "text": page_text
                    })

            # Save the extracted content
            output_file = f"/tmp/{customer_guid}/{filename}.rawcontent"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as raw_content_file:
                json.dump(results, raw_content_file, indent=4)

            logger.info(f"Extracted content saved to '{output_file}'")
            return output_file
        except Exception as e:
            logger.error(f"Error extracting content from PDF file '{filename}': {e}")
            raise Exception(f"PDF content extraction failed: {e}")


if __name__ == "__main__":
    customer_guid = "fc461914-321e-4f1f-bba1-ab767ad8edd2"
    filename = "sample.pdf"
    upload_file_for_chunks = UploadFileForChunks()
    upload_file_for_chunks.extract_file(customer_guid, filename)

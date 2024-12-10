import os
import logging
import magic  # Used to detect file type
import pytesseract
from src.backend.minio.minio_manager import MinioManager
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
        logger.info(f"Extracting file '{filename}' for customer '{customer_guid}'")

        #Download and save file locally
        local_path = self.download_and_save_file(customer_guid, filename)

        #Verify file type
        try:
            file_type = self.file_extract.detect_file_type(local_path)
            if file_type == ".pdf":
                logger.info(f"Verified file '{filename}' as a valid PDF.")
            else:
                logger.error(f"File '{filename}' is not a valid file (detected type: {file_type})")
                raise Exception("Invalid file type: Uploaded file is not a Valid.")
        except Exception as e:
            logger.error(f"Error detecting file type for '{filename}': {e}")
            raise Exception("File type detection failed.")

        #Extract Files content here
        try:
            if file_type==".pdf":
                output_file_path = self.file_extract.extract_pdf_content(customer_guid, local_path, filename)
                self.upload_extracted_content(customer_guid, filename, output_file_path)
                return {"message": "PDF extracted and uploaded successfully."}
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise Exception(f"File extraction failed.{e}")

class FileExtractor:

    def detect_file_type(self, file_path: str):
        MIME_TO_EXTENSION = {
            "application/pdf": ".pdf"
        }
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
            if not table:
                logger.error("Empty or None table received for formatting.")
                return "Empty table"

            headers = table[0]  # Assuming the first row is the header
            rows = table[1:]  # All subsequent rows
            result = []

            # Iterate through each row in the table and format the data generically
            for row in rows:
                formatted_row = ", ".join(
                    [f"{headers[i]}: {row[i] if i < len(row) else 'NA'}" for i in range(len(headers))])
                result.append(formatted_row)

            return "\n".join(result).strip()

        except Exception as e:
            logger.error(f"Error formatting table: {e}")
            raise Exception(f"Table formatting failed: {e}")

    def is_within_bbox(self, point: tuple, bbox: tuple):
        x, y = point
        x0, y0, x1, y1 = bbox
        return x0 <= x <= x1 and y0 <= y <= y1

    def is_vertical_text(self, element):
        # Check if both 'x0' and 'x1' keys exist in the element
        if 'x0' in element and 'x1' in element:
            return abs(element["x0"] - element["x1"]) < abs(element["y0"] - element["y1"]) * 0.5
        return False

    def reverse_vertical_text(self, text):
        return text[::-1]

    def extract_pdf_content(self, customer_guid: str, file_path: str, filename: str):

        try:
            results = []
            with pdfplumber.open(file_path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    page_elements = []
                    page_width = page.width
                    mid_x = page_width / 2  # Midpoint for left/right classification

                    # Extract text blocks and classify into left/right or full-paragraph
                    left_content = []
                    right_content = []
                    all_content = []

                    for block in page.extract_words():
                        x0 = block["x0"]
                        y0 = block["top"]

                        # Classify into left or right sections
                        if x0 < mid_x:
                            left_content.append({"text": block["text"], "y0": y0})
                        else:
                            right_content.append({"text": block["text"], "y0": y0})

                        all_content.append({"text": block["text"], "y0": y0})

                    # Check if left and right content exists
                    has_left = len(left_content) > 0
                    has_right = len(right_content) > 0

                    # Determine layout type
                    if has_left and has_right:
                        # Left/Right Layout: Process separately and merge
                        left_content = sorted(left_content, key=lambda b: b["y0"])
                        right_content = sorted(right_content, key=lambda b: b["y0"])
                        merged_content = " ".join([b["text"] for b in left_content + right_content])
                    else:
                        # Full-Paragraph Layout: Sort all text blocks and merge them
                        sorted_content = sorted(all_content, key=lambda b: b["y0"])
                        merged_content = " ".join([b["text"] for b in sorted_content])

                    # Append merged text content to page_elements
                    page_elements.append({
                        "type": "text",
                        "content": merged_content,
                        "x0": 0,
                        "y0": 0  # No specific position for merged content
                    })

                    # Extract text and table data from the page
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # Format and collect table data
                            table_text = self.format_table_as_text(table)
                            page_elements.append({
                                "type": "table",
                                "content": table_text,
                                "x0": 0,
                                "y0": 0
                            })

                    # If there's no extracted text, perform OCR and append image-based text
                    if not page.extract_text():
                        page_image = page.to_image(resolution=300).original
                        ocr_text = pytesseract.image_to_string(page_image)
                        page_elements.append({
                            "type": "image",
                            "content": ocr_text.strip(),
                            "x0": 0,
                            "y0": 0
                        })

                    # Sort page elements by vertical position (y0) and horizontal position (x0)
                    page_elements.sort(key=lambda w: (w["y0"], w["x0"]))

                    # Handle reversed vertical text
                    corrected_content = []
                    for element in page_elements:
                        if element["type"] == "text" and self.is_vertical_text(element):
                            corrected_content.append(self.reverse_vertical_text(element["content"]))
                        else:
                            corrected_content.append(element["content"])

                    # Join the corrected content
                    page_text = " ".join(corrected_content)

                    # Append the result for this page (with metadata and content)
                    results.append({
                        "metadata": {"page_number": page_number},
                        "text": page_text
                    })

                # Save the extracted content to a file
                output_file_path = f"/tmp/{customer_guid}/{filename}.rawcontent"
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                with open(output_file_path, "w", encoding="utf-8") as raw_content_file:
                    json.dump(results, raw_content_file, indent=4)

                logger.info(f"Extracted content saved to '{output_file_path}'")
                return output_file_path
        except Exception as e:
            logger.error(f"Error extracting content from PDF file '{filename}': {e}")
            raise Exception(f"PDF content extraction failed: {e}")


if __name__ == "__main__":
    customer_guid = "ecb2fc17-6ec2-4629-a78f-b2d9a87a3540"
    filename = "NewRFOCFile.pdf"
    upload_file_for_chunks = UploadFileForChunks()
    upload_file_for_chunks.extract_file(customer_guid, filename)

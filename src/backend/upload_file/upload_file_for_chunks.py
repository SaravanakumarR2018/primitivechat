import json
import os
import pdfplumber
import magic
import easyocr
import numpy as np
import logging

#config logging
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CheckFileType:

    def check_file_type(self, filename):
        mime_to_extension = {
            "application/pdf": ".pdf"
        }
        try:
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(filename)
            extension = mime_to_extension.get(file_type)
            if not extension:
                logger.error(f"Unknown MIME type detected: {file_type}")
                return None
            return extension
        except Exception as e:
            logger.error(f"Error detecting file type for {filename}: {e}")
            return None


class ExtractFiles:

    def __init__(self):

        # Initialize EasyOCR Reader
        self.ocr_reader = easyocr.Reader(['en'], gpu=False)

    def format_table_as_text(self, table):
        table = [[str(item) if item is not None else "" for item in row] for row in table]
        col_widths = [max(len(str(item)) for item in col) for col in zip(*table)]
        row_format = " | ".join(f"{{:<{w}}}" for w in col_widths)
        formatted_table = "\n".join(row_format.format(*row) for row in table)
        return formatted_table.strip()

    def extract_pdf_with_layout(self, filename, output_json_path):
        results = []

        with pdfplumber.open(filename) as pdf:
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

                    pil_image = page.to_image(resolution=300).original
                    numpy_image = np.array(pil_image)
                    ocr_result = self.ocr_reader.readtext(numpy_image)
                    ocr_text = " ".join([text[1] for text in ocr_result])

                    page_elements.append({
                        "type": "image",
                        "content": f"Data obtained from image: {ocr_text.strip()}",
                        "x0": 0,  # Assuming full-page images
                        "y0": 0
                    })

                page_elements.sort(key=lambda e: (e["y0"], e["x0"]))

                page_text = " ".join([element["content"] for element in page_elements])

                results.append({
                    "page_number": page_number,
                    "text": page_text
                })

        with open(output_json_path, "w", encoding="utf-8") as output_file:
            json.dump(results, output_file, indent=4, ensure_ascii=False)
        print(f"Extraction complete. Data saved to {output_json_path}")
        return output_json_path


class PDFReader:

    def pdf_reader(self, input_json_path):
        try:
            with open(input_json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"Error: The file {input_json_path} was not found.")
            return None
        except json.JSONDecodeError:
            print(f"Error: Failed to decode the JSON file {input_json_path}.")
            return None


class UploadFileForChunks:

    def __init__(self):

        self.check_file_type_instance = CheckFileType()
        self.extract_files = ExtractFiles()
        self.pdf_reader = PDFReader()

    def process_document(self, filename):

        file_type = self.check_file_type_instance.check_file_type(filename)
        if file_type and file_type.endswith(".pdf"):
            output_json_path = f"output/{os.path.basename(filename)}_extracted.json"

            if not os.path.exists(os.path.dirname(output_json_path)):
                os.makedirs(os.path.dirname(output_json_path))

            # Extract data
            extract_data = self.extract_files.extract_pdf_with_layout(filename, output_json_path)

            # Read the extracted data
            data = self.pdf_reader.pdf_reader(extract_data)
            self.raw_content_store_bucket(filename, data)

            return output_json_path

    def raw_content_store_bucket(self, filename, data):
        try:
            # Generate raw content file name
            base_filename, file_extension = os.path.splitext(os.path.basename(filename))
            raw_content_filename = f"{base_filename}{file_extension}.rawcontent"
            raw_content_path = os.path.join(os.path.dirname(filename), raw_content_filename)

            # Save the extracted data to the raw content file
            with open(raw_content_path, "w", encoding="utf-8") as raw_file:
                json.dump(data, raw_file, indent=4, ensure_ascii=False)

            logger.info(f"Raw content uploaded successfully as {raw_content_filename}")
            print(f"Raw content saved at: {raw_content_path}")
            return {"message": "Raw content uploaded successfully"}
        except Exception as e:
            logger.error(f"Failed to upload raw content: {e}")
            raise e


if __name__ == "__main__":

    pdf_file_path = "/home/kabilan-a/Documents/PrinceCatalogue.pdf"


    processor = UploadFileForChunks()

    if not os.path.exists(pdf_file_path):
        print(f"Error: File not found at {pdf_file_path}")
    else:
        try:
            # Process the document
            processor.process_document(pdf_file_path)
        except Exception as e:
            print(f"Error occurred during processing: {e}")

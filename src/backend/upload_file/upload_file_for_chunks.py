import json
import os
import pdfplumber
import pytesseract
import magic
from src.backend.minio.minio_manager import MinioManager, logger


class CheckFileType:

    def check_file_type(self, filename):

        mime_to_extension = {
            # "text/x-python": ".py",  # Python files
            # "application/javascript": ".js",  # JavaScript files
            # "text/css": ".css",  # CSS files
            # "audio/mpeg": ".mp3",  # MP3 files
            # "text/html": ".html",  # HTML files
            # "application/json": ".json",  # JSON files
            # "image/jpeg": ".jpg",  # JPEG image files
            # "image/png": ".png",  # PNG image files
            "application/pdf": ".pdf",  # PDF files
            # "audio/x-wav": ".wav",  # WAV files
            # "text/plain": ".txt",  # Text files
            # "text/csv": ".csv",  # CSV files
            # "text/tab-separated-values": ".tsv",  # TSV files
            # "application/xml": ".xml",  # XML files
            # "application/vnd.ms-excel": ".xls",  # Excel files (.xls)
            # "application/vnd.oasis.opendocument.spreadsheet": ".ods",  # ODS files
            # "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",  # DOCX files
            # "application/msword": ".doc",  # DOC files
            # "application/epub+zip": ".epub",  # EPUB files
            # "application/vnd.ms-powerpoint": ".ppt",  # PPT files
            # "application/vnd.apple.keynote": ".key",  # Keynote files
            # "application/x-chm": ".chm",  # CHM files
            # "application/x-tex": ".tex",  # LaTeX files
            # "application/rtf": ".rtf",  # RTF files
            # "image/bmp": ".bmp",  # BMP files
            # "image/gif": ".gif",  # GIF files
            # "image/tiff": ".tiff",  # TIFF files
            # "image/svg+xml": ".svg",  # SVG files
            # "application/vnd.adobe.illustrator": ".ai",  # AI files (Illustrator)
            # "audio/x-wav": ".wav",  # WAV audio files
            # "audio/mpeg": ".mp3",  # MP3 audio files
            # "application/java-archive": ".jar",  # JAR files (Java Archive)
            # "application/x-zip-compressed": ".zip",  # ZIP files
            # "application/x-tar": ".tar",  # TAR files
            # "application/x-rar-compressed": ".rar",  # RAR files
            # "application/x-7z-compressed": ".7z",  # 7z files
        }
        try:
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(filename)
            extension = mime_to_extension.get(file_type)
            if not extension:
                logger.warning(f"Unknown MIME type detected: {file_type}")
                return None
            return extension
        except Exception as e:
            logger.error(f"Error detecting file type for {filename}: {e}")
            return None

class PDFReader:

    def pdf_reader(self,input_json_path):

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

class ExtractFiles:


    def format_table_as_text(self,table):
        col_widths = [max(len(str(item)) for item in col) for col in zip(*table)]
        row_format = " | ".join(f"{{:<{w}}}" for w in col_widths)
        formatted_table = "\n".join(row_format.format(*row) for row in table)
        return formatted_table.strip()

    # def extract_images_from_docx(self,docx_path):
    #     images = []
    #     doc = docx.Document(docx_path)
    #     for rel in doc.part.rels.values():
    #         if "image" in rel.target_ref:
    #             img_data = rel.target_part.blob  # Extract image data
    #             image = Image.open(io.BytesIO(img_data))  # Open image
    #             images.append(image)
    #     return images
    #
    # def for_html_table_as_text(self, table):
    #     table_text = []
    #     for row in table.find_all('tr'):
    #         row_text = [cell.get_text(strip=True) for cell in row.find_all('td')]
    #         table_text.append(" | ".join(row_text))
    #     return "\n".join(table_text)
    #
    # def extract_image_from_base64(self, base64_string):
    #     # Decode base64 string to image and perform OCR
    #     image_data = base64.b64decode(base64_string)
    #     image = Image.open(io.BytesIO(image_data))
    #     ocr_text = pytesseract.image_to_string(image)  # Perform OCR on image
    #     return ocr_text.strip()
    #
    # def extract_image_for_csvfile(self, image_path):
    #     # Open image file and perform OCR
    #     image = Image.open(image_path)
    #     ocr_text = pytesseract.image_to_string(image)  # Perform OCR on image
    #     return ocr_text.strip()

    def extract_pdf_with_layout(self,filename,output_json_path):

        results = []

        with pdfplumber.open(filename) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_elements = []

                # Extract text blocks with their bounding boxes
                for block in page.extract_words():
                    page_elements.append({
                        "type": "text",
                        "content": block["text"],
                        "x0": block["x0"],
                        "y0": block["top"]
                    })

                # Extract tables with their bounding boxes
                for table in page.extract_tables():
                    table_text =self.format_table_as_text(table)
                    bbox = page.find_tables()[0].bbox  # Get bounding box for the first table
                    page_elements.append({
                        "type": "table",
                        "content": table_text,
                        "x0": bbox[0],
                        "y0": bbox[1]
                    })

                # OCR for images or non-text content
                if not page.extract_text():
                    page_image = page.to_image(resolution=300).original
                    ocr_text = pytesseract.image_to_string(page_image)
                    page_elements.append({
                        "type": "image",
                        "content": f"Data obtained from image: {ocr_text.strip()}",
                        "x0": 0,  # Assuming full-page images
                        "y0": 0
                    })

                # Sort elements by their Y-coordinate and then X-coordinate for layout
                page_elements.sort(key=lambda e: (e["y0"], e["x0"]))

                # Combine elements into a single text flow
                page_text = " ".join([element["content"] for element in page_elements])

                # Append page result
                results.append({
                    "page_number": page_number,
                    "text": page_text
                })

        # Save to JSON
        with open(output_json_path, "w", encoding="utf-8") as output_file:
            json.dump(results, output_file, indent=4, ensure_ascii=False)
        print(f"Extraction complete. Data saved to {output_json_path}")
        return output_json_path

class UploadFileForChunks:
        def __init__(self):

            self.minio_manager=MinioManager()

            self.check_file_type_instance = CheckFileType()

            self.extract_files=ExtractFiles()

            self.pdf_reader=PDFReader()


        def process_document(self, bucket_name, filename):

            customer_guid, filename = self.minio_manager.download_file(self, bucket_name, filename)

            file_type = self.check_file_type_instance.check_file_type(filename)

            if file_type.endswith(".pdf"):
                extract_data=self.extract_files.extract_pdf_with_layout(self,filename)
                self.pdf_reader.pdf_reader(extract_data)
                self.raw_content_store_bucket(customer_guid,filename)

                """All the files checking here like .docs,.pptx//etc"""

        def raw_content_store_bucket(self,customer_guid,filename):

            try:
                base_filename, file_extension = os.path.splitext(os.path.basename(filename))
                raw_content_filename = f"{base_filename}{file_extension}.rawcontent"


                self.minio_manager.upload_file(
                    #bucket_name=customer_guid,
                    filename=raw_content_filename,
                    raw_content_filename=raw_content_filename
                )
                logger.info(f"Raw content uploaded successfully as {raw_content_filename}")
            except Exception as e:
                logger.error(f"Failed to upload raw content: {e}")
                raise














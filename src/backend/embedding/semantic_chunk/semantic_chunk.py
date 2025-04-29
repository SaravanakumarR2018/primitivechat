import json
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from src.backend.minio.minio_manager import MinioManager
from src.backend.embedding.lib.download_and_upload_file import LocalFileDownloadAndUpload

from src.backend.lib.logging_config import log_format
from src.backend.lib.singleton_class import Singleton

from src.backend.lib.logging_config import get_primitivechat_logger


# Configure Logging
logger = get_primitivechat_logger(__name__)

class ProcessAndUploadBucket:
    def __init__(self):
        self.minio_manager = MinioManager()
        self.chunk_processor = SemanticChunkProcessor()
        self.download_and_upload = LocalFileDownloadAndUpload()

    def process_and_upload(self, customer_guid: str, filename: str):
        try:
            local_input_path = self.download_and_upload.download_and_save_file(customer_guid, filename)
            base_filename = filename.replace(".txt", "")
            with open(local_input_path, "r", encoding="utf-8") as file:
                pages = json.load(file)

            chunks = self.chunk_processor.generate_chunks(pages, customer_guid, base_filename)

            output_filename = base_filename + ".chunked.txt"
            local_output_path = f"/tmp/{customer_guid}/{output_filename}"
            with open(local_output_path, "w", encoding="utf-8") as outputfile:
                json.dump(chunks, outputfile, indent=4)

            logger.info(f"Processed file saved as '{local_output_path}'.")

            self.download_and_upload.upload_chunked_content(customer_guid, base_filename, local_output_path)

        except Exception as e:
            logger.error(f"Error in processing and uploading: {e}")
            raise Exception(f"Failed to upload file.{e}")

class SemanticChunkProcessor(metaclass=Singleton):
    def __init__(self, model_name='all-mpnet-base-v2', max_tokens=300, similarity_threshold=0.4):
        try:
            self.model = self.load_model(model_name)
            self.max_tokens = max_tokens
            self.similarity_threshold = similarity_threshold
            self.nlp = spacy.load('en_core_web_sm')
        except Exception as e:
            logger.error(f"Error initializing SemanticChunkProcessor: {e}")
            raise Exception(f"Initialization failed: {e}")

    def load_model(self, model_name):
        try:
            return SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Error loading SentenceTransformer model '{model_name}': {e}")
            raise Exception(f"Model loading failed: {e}")

    def generate_chunks(self, pages, customer_guid, filename):
        try:
            chunks = []
            current_chunk = {"text": "", "page_numbers": set()}
            current_tokens = 0
            chunk_number = 1

            for page in pages:
                text = page.get("text", "")
                page_number = page.get("metadata", {}).get("page_number", None)
                if page_number is None:
                    logger.warning(f"Warning: Page {page} has no 'page_number' key.")
                    continue
                doc = self.nlp(text)  # Process the text with spaCy
                sentences = [sent.text.strip() for sent in doc.sents]  # Split into sentences

                for sentence in sentences:
                    sentence_tokens = len(sentence.split())  # Count tokens in the sentence

                    # Calculate similarity
                    if current_chunk["text"]:
                        similarity = cosine_similarity(
                            [self.model.encode(current_chunk["text"])],
                            [self.model.encode(sentence)]
                        )[0][0]
                    else:
                        similarity = self.similarity_threshold  + 1

                    # Check if new chunziplet.html.txk should be created
                    if (current_tokens + sentence_tokens > self.max_tokens) or (similarity < self.similarity_threshold):
                        if current_chunk["text"]:
                            chunks.append({
                                "metadata": {
                                    "chunk_number": chunk_number,
                                    "page_numbers": sorted(list(current_chunk["page_numbers"])),
                                    "customer_guid": customer_guid,
                                    "filename": filename
                                },
                                "text": current_chunk["text"].strip()
                            })
                            chunk_number += 1  # Increment chunk number

                        # Reset current chunk
                        current_chunk = {"text": "", "page_numbers": set()}
                        current_tokens = 0

                    current_chunk["text"] += sentence + " "
                    current_chunk["page_numbers"].add(page_number)
                    current_tokens += sentence_tokens

            # Add the last chunk if it contains any text
            if current_chunk["text"].strip():
                chunks.append({
                    "metadata": {
                        "chunk_number": chunk_number,
                        "page_numbers": sorted(list(current_chunk["page_numbers"])),
                        "customer_guid": customer_guid,
                        "filename": filename
                    },
                    "text": current_chunk["text"].strip()
                })

            return chunks
        except Exception as e:
            logger.error(f"Error in generate_chunks: {e}")
            raise Exception(f"Chunk generation failed: {e}")


if __name__ == "__main__":
    customer_guid = "d3d62569-03b4-41ce-94bf-918a97684763"
    filename = "ziplet.html.txt"
    final_processor=ProcessAndUploadBucket()
    final_processor.process_and_upload(customer_guid, filename)

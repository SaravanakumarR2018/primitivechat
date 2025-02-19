import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.backend.db.database_manager import DatabaseManager
from src.backend.embedding.extract_file.extract_file import UploadFileForChunks
from src.backend.embedding.semantic_chunk.semantic_chunk import ProcessAndUploadBucket
from src.backend.weaviate.weaviate_manager import WeaviateManager

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize DatabaseManager instance
db_manager = DatabaseManager()

class FileVectorizer:

    def __init__(self, max_workers=5, polling_interval=10):
        logger.info("Initializing FileVectorizer...")
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.polling_interval = polling_interval
        self.shutdown_event = threading.Event()
        self.worker_thread = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker_thread.start()

        # Initialize components
        self.extracted = UploadFileForChunks()
        self.chunked = ProcessAndUploadBucket()
        self.vectorizer= WeaviateManager()

        logger.info("FileVectorizer initialized components successfully.")

    def extract_file(self, customer_guid, filename):
        logger.info(f"Extracting file: {filename} for customer: {customer_guid}")
        try:
            self.extracted.extract_file(customer_guid, filename)
            return True
        except Exception as e:
            logger.error(f"Error during extraction of {filename}: {e}")
            return False

    def chunk_file(self, customer_guid, filename):
        chunk_filename = f"{filename}.txt"
        logger.info(f"Chunking file: {chunk_filename} for customer: {customer_guid}")
        try:
            self.chunked.process_and_upload(customer_guid,chunk_filename)
            return True
        except Exception as e:
            logger.error(f"Error during chunking of {filename}: {e}")
            return False

    def vectorize_file(self, customer_guid, filename):
        vectorize_filename = f"{filename}.chunked.txt"
        logger.info(f"Vectorizing file: {vectorize_filename} for customer: {customer_guid}")
        try:
            self.vectorizer.processing(customer_guid,vectorize_filename)
            return True
        except Exception as e:
            logger.error(f"Error during vectorizing of {filename}: {e}")

    def process_file(self, customer_guid, filename):

        try:
            file_record = db_manager.get_file_status(customer_guid, filename)
            if not file_record:
                logger.warning(f"File {filename} not found in database, skipping...")
                return

            status, error_retry = file_record

            if status in ["todo","extract_error"]:
                if self.extract_file(customer_guid, filename):
                    db_manager.update_status(customer_guid, filename, "extracted")
                else:
                    db_manager.update_status(customer_guid, filename, "extract_error", error_retry + 1)
                    return

            file_record = db_manager.get_file_status(customer_guid, filename)
            status, error_retry = file_record

            if status in ["extracted", "chunk_error"]:
                if self.chunk_file(customer_guid, filename):
                    db_manager.update_status(customer_guid, filename, "chunked")
                else:
                    db_manager.update_status(customer_guid, filename, "chunk_error", error_retry + 1)
                    return

            file_record = db_manager.get_file_status(customer_guid, filename)
            status, error_retry = file_record

            if status in ["chunked", "vectorize_error"]:
                if self.vectorize_file(customer_guid,filename):
                    db_manager.update_status(customer_guid, filename, "completed")
                else:
                    db_manager.update_status(customer_guid, filename, "vectorize_error", error_retry + 1)
                    return

            if error_retry >= 7:
                db_manager.remove_from_common_db(customer_guid, filename)

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")

    def worker_loop(self):
        logger.info("Starting background worker thread...")
        while not self.shutdown_event.is_set():
            try:
                logger.info("Checking for 'todo','extracted' and 'chunked' files...")
                pending_files = db_manager.get_todo_files()

                if not pending_files:
                    logger.info("No files to process. Sleeping...")
                    time.sleep(self.polling_interval)
                    continue

                futures = []
                for customer_guid, filename, _ in pending_files:
                    futures.append(self.executor.submit(self.process_file, customer_guid, filename))

                # Wait for all submitted tasks to complete
                for future in as_completed(futures):
                    future.result()

                logger.info("All pending files processed. Sleeping before next poll...")
                time.sleep(self.polling_interval)

            except Exception as e:
                logger.error(f"Worker thread crashed: {e}", exc_info=True)

    def stop(self):
        logger.info("Stopping background worker...")
        self.shutdown_event.set()
        self.worker_thread.join()
        self.executor.shutdown(wait=True)
        logger.info("Background worker stopped.")

#testing
if __name__ == "__main__":
    worker = FileVectorizer()
    worker.worker_loop()  # Start worker loop

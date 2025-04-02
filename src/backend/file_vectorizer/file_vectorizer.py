import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.backend.db.database_manager import DatabaseManager
from src.backend.embedding.extract_file.extract_file import UploadFileForChunks
from src.backend.embedding.semantic_chunk.semantic_chunk import ProcessAndUploadBucket
from src.backend.weaviate.weaviate_manager import WeaviateManager
from src.backend.minio.minio_manager import MinioManager
from src.backend.lib.logging_config import log_format

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

db_manager = DatabaseManager()

class FileVectorizer:

    def __init__(self, max_workers=5, polling_interval=2):
        logger.info("Initializing FileVectorizer...")
        self.max_threads=max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.polling_interval = polling_interval
        self.shutdown_event = threading.Event()
        self.worker_thread = threading.Thread(target=self.worker_loop, daemon=True)
        self.deletion_thread = threading.Thread(target=self.deletion_loop, daemon=True)
        self.worker_thread.start()
        self.deletion_thread.start()

        # Initialize components
        self.minio=MinioManager()
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
            self.vectorizer.insert_data(customer_guid,vectorize_filename)
            return True
        except Exception as e:
            logger.error(f"Error during vectorizing of {filename}: {e}")
            return False

    def process_file(self, customer_guid, filename):

        try:
            file_record = db_manager.get_file_status(customer_guid, filename)
            if not file_record:
                logger.warning(f"File {filename} not found in database, skipping...")
                return

            status, error_retry = file_record

            if status in ["todo", "extract_error"]:
                try:
                    if self.extract_file(customer_guid, filename):
                        db_manager.update_status(customer_guid, filename, "extracted", "", error_retry)
                    else:
                        raise Exception("Extraction failed without an exception.")
                except Exception as e:
                    error_message = str(e)
                    db_manager.update_status(customer_guid, filename, "extract_error", error_message, error_retry + 1)
                    if error_retry >= 7:
                        db_manager.remove_from_common_db(customer_guid, filename, error=True)
                    return

            file_record = db_manager.get_file_status(customer_guid, filename)
            status, error_retry = file_record

            if status in ["extracted", "chunk_error"]:
                try:
                    if self.chunk_file(customer_guid, filename):
                        db_manager.update_status(customer_guid, filename, "chunked", "", error_retry)
                    else:
                        raise Exception("Chunking failed without an exception.")
                except Exception as e:
                    error_message = str(e)
                    db_manager.update_status(customer_guid, filename, "chunk_error", error_message, error_retry + 1)
                    if error_retry >= 7:
                        db_manager.remove_from_common_db(customer_guid, filename, error=True)
                    return

            file_record = db_manager.get_file_status(customer_guid, filename)
            status, error_retry = file_record

            if status in ["chunked", "vectorize_error"]:
                try:
                    if self.vectorize_file(customer_guid, filename):
                        db_manager.update_status(customer_guid, filename, "completed", "", error_retry)
                        # Delete extracted and chunked files from MinIO
                        extracted_file = f"{filename}.txt"
                        chunked_file = f"{filename}.chunked.txt"
                        try:
                            self.minio.delete_file(customer_guid, extracted_file)
                            self.minio.delete_file(customer_guid, chunked_file)
                            logger.info(f"Deleted extracted and chunked files for {filename} from MinIO.")
                        except Exception as e:
                            logger.error(f"Error deleting extracted and chunked files from MinIO: {e}")

                        # Remove file from common_db (since it's successfully processed)
                        db_manager.remove_from_common_db(customer_guid, filename, error=False)
                    else:
                        raise Exception("Vectorization failed without an exception.")
                except Exception as e:
                    error_message = str(e)
                    db_manager.update_status(customer_guid, filename, "vectorize_error", error_message, error_retry + 1)
                    if error_retry >= 7:
                        db_manager.remove_from_common_db(customer_guid, filename, error=True)
                    return
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")

    def process_deletion(self, customer_guid: str, file_id: str):

        logger.info(f"Processing deletion for {file_id} (customer: {customer_guid})")

        try:
            # Get file record by ID
            file_record = db_manager.get_file_record_by_id(customer_guid, file_id)
            if not file_record:
                logger.warning(f"File with ID {file_id} not found")
                return

            filename = file_record.filename  # used for weaviate and minio for filename

            # Get current status
            deletion_record = db_manager.get_deletion_status(customer_guid, file_id)
            if not deletion_record:
                logger.warning(f"File {file_id} not marked for deletion")
                return
            delete_status, error_retry = deletion_record

            if delete_status in ["todo", "in_progress"]:

                # Step 1: Delete from Weaviate
                try:
                    self.vectorizer.delete_objects_by_customer_and_filename(customer_guid, filename)
                    logger.info(f"Successfully deleted from Weaviate: {filename}")
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Weaviate deletion failed: {error_message}")
                    db_manager.update_deletion_status(customer_guid, file_id, 'in_progress', error_message,error_retry + 1)
                    if error_retry >= 7:
                        db_manager.finalize_deletion(customer_guid, file_id, error=True)
                        return

                # Step 2: Delete a from MinIO
                try:
                    self.minio.delete_file(customer_guid, filename)
                    logger.info(f"Successfully deleted from MinIO: {filename}")
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"MinIO deletion failed: {error_message}")
                    db_manager.update_deletion_status(customer_guid, file_id, 'in_progress', error_message,error_retry + 1)
                    if error_retry >= 7:
                        db_manager.finalize_deletion(customer_guid, file_id, error=True)
                    return

                # Finalize success
                db_manager.finalize_deletion(customer_guid, file_id, error=False)
                logger.info(f"Completed deletion for {file_id}")

        except Exception as e:
            error_message = str(e)
            logger.error(f"Deletion process failed: {error_message}")

    def worker_loop(self):
        logger.info("Starting background worker thread...")
        while not self.shutdown_event.is_set():
            try:
                logger.debug("Checking for 'todo','extracted' and 'chunked' files...")
                pending_files = db_manager.get_todo_files(self.max_threads)

                if not pending_files:
                    logger.debug("No files to process. Sleeping...")
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

    def deletion_loop(self):
        """Background thread to process file deletions"""
        logger.info("Starting background deletion thread...")
        while not self.shutdown_event.is_set():
            try:
                logger.debug("Checking todo files for deleting a file")
                pending_deletions = db_manager.get_pending_deletions(self.max_threads)

                if not pending_deletions:
                    logger.debug("No files to process for delete. Sleeping...")
                    time.sleep(self.polling_interval)
                    continue

                futures = []
                for customer_guid, file_id in pending_deletions:
                    futures.append(
                        self.executor.submit(self.process_deletion, customer_guid, file_id))

                for future in as_completed(futures):
                    future.result()
                time.sleep(self.polling_interval)

            except Exception as e:
                logger.error(f"Deletion thread error: {e}", exc_info=True)

    def stop(self):
        logger.info("Stopping background worker...")
        self.shutdown_event.set()

        # Give the worker thread some time to exit gracefully
        self.worker_thread.join(timeout=5)

        if self.worker_thread.is_alive():
            logger.warning("Worker thread did not terminate in time. Forcing shutdown...")

        self.executor.shutdown(wait=False)  # Shut down executor immediately
        logger.info("Background worker stopped.")

#testing
if __name__ == "__main__":
    worker = FileVectorizer()
    try:
        worker.worker_loop()
    except KeyboardInterrupt:
        worker.stop()

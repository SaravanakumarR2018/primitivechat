import logging
import time
from src.backend.file_vectorizer.file_vectorizer import FileVectorizer
from src.backend.lib.logging_config import get_primitivechat_logger

# Configure logging
logger = get_primitivechat_logger(__name__)

def main():
    logger.info("Starting file vectorizer process...")
    vectorizer = FileVectorizer()
    while True:
        try:
            vectorizer.worker_loop()
            logger.info("File vectorization completed successfully.")
        except Exception as e:
            logger.error(f"Error during file vectorization: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()

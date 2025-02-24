import logging
from src.backend.file_vectorizer.file_vectorizer import FileVectorizer # Replace with your actual module

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting file vectorizer process...")
    vectorizer = FileVectorizer()
    while True:
        try:
            vectorizer.worker_loop()
            logger.info("File vectorization completed successfully.")
        except Exception as e:
            logger.error(f"Error during file vectorization: {e}")

if __name__ == "__main__":
    main()
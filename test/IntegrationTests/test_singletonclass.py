import unittest
import logging
#from src.backend.chat_service.llm_service import LLMService
from src.backend.db.database_manager import DatabaseManager
from src.backend.embedding.extract_file.extract_file import UploadFileForChunks
from src.backend.embedding.semantic_chunk.semantic_chunk import ProcessAndUploadBucket
from src.backend.embedding.semantic_chunk.semantic_chunk import SemanticChunkProcessor
from src.backend.file_vectorizer.file_vectorizer import FileVectorizer
from src.backend.minio.minio_manager import MinioManager
from src.backend.weaviate.weaviate_manager import WeaviateManager
from src.backend.lib.logging_config import get_primitivechat_logger

# Set up logging configuration
logger = get_primitivechat_logger(__name__)


class TestSingletonClasses(unittest.TestCase):
    """Test suite for singleton classes."""

    # def test_llm_service_singleton(self):
    #     """Test if LLMService is a true singleton."""
    #     logger.info("Testing LLMService singleton behavior...")

    #     # Create two instances
    #     llm1 = LLMService()
    #     llm2 = LLMService()

    #     self.assertIs(llm1, llm2, "LLMService is not a singleton!")

    #     self.assertEqual(llm1, llm2, "Class attributes mismatch!")
    #     logger.info("LLMService passed singleton test.")

    def test_database_manager_singleton(self):
        """Test if DatabaseManager is a true singleton."""
        logger.info("Testing DatabaseManager singleton behavior...")

        db1 = DatabaseManager()
        db2 = DatabaseManager()

        self.assertIs(db1, db2, "DatabaseManager is not a singleton!")

        self.assertEqual(db1, db1,"Class attributes mismatch!")
        logger.info(" DatabaseManager passed singleton test.")

    def test_process_upload_chunks_singleton(self):
        """Test if UploadFileForChunks is a true singleton."""
        logger.info("Testing UploadFileForChunks singleton behavior...")

        uploader1 = UploadFileForChunks
        uploader2 = UploadFileForChunks

        self.assertIs(uploader1, uploader2, "UploadFileForChunks is not a singleton!")

        self.assertEqual(uploader1, uploader2,"Class attributes mismatch!")
        logger.info("UploadFileForChunks passed singleton test.")

    def test_process_upload_bucket_singleton(self):
        """Test if ProcessAndUploadBucket is a true singleton."""
        logger.info("Testing ProcessAndUploadBucket singleton behavior...")

        bucket1 = ProcessAndUploadBucket
        bucket2 = ProcessAndUploadBucket

        self.assertIs(bucket1, bucket2, "ProcessAndUploadBucket is not a singleton!")

        self.assertEqual(bucket1, bucket2,"Class attributes mismatch!")
        logger.info("ProcessAndUploadBucket passed singleton test.")

    def test_semantic_chunk_process_singleton(self):
        """Test if SemanticChunkProcessor is a true singleton."""
        logger.info("Testing SemanticChunkProcessor singleton behavior...")

        semantic1 = SemanticChunkProcessor
        semantic2 = SemanticChunkProcessor

        self.assertIs(semantic1, semantic2, "SemanticChunkProcessor is not a singleton!")

        self.assertEqual(semantic1, semantic2,"Class attributes mismatch!")
        logger.info("SemanticChunkProcessor passed singleton test.")

    def test_file_vectorizer_singleton(self):
        """Test if FileVectorizer is a true singleton."""
        logger.info("Testing FileVectorizer singleton behavior...")

        filevectorizer1 = FileVectorizer
        filevectorizer2 = FileVectorizer

        self.assertIs(filevectorizer1, filevectorizer2, "FileVectorizer is not a singleton!")

        self.assertEqual(filevectorizer1, filevectorizer2,"Class attributes mismatch!")
        logger.info("FileVectorizer passed singleton test.")

    def test_minio_manager_singleton(self):
        """Test if MinioManager is a true singleton."""
        logger.info("Testing MinioManager singleton behavior...")

        minio1 = MinioManager
        minio2 = MinioManager

        self.assertIs(minio1, minio2, "MinioManager is not a singleton!")

        self.assertEqual(minio1, minio2,"Class attributes mismatch!")
        logger.info("MinioManager passed singleton test.")

    def test_weaviate_manager_singleton(self):
        """Test if WeaviateManager is a true singleton."""
        logger.info("Testing WeaviateManager singleton behavior...")

        weaviate1 = WeaviateManager
        weaviate2 = WeaviateManager

        self.assertIs(weaviate1, weaviate2, "WeaviateManager is not a singleton!")

        self.assertEqual(weaviate1, weaviate2,"Class attributes mismatch!")
        logger.info("WeaviateManager passed singleton test.")


if __name__ == "__main__":
    unittest.main()

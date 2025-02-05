import logging
from weaviate import Client
from src.backend.weaviate.weaviate_manager import WeaviateManager  # Import the updated WeaviateManager class

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DataDeletionManager:
    def __init__(self):
        try:
            self.client = Client(f"http://localhost:9002")
            logger.info("Successfully connected to Weaviate")
            self.weaviate=WeaviateManager()
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate connection: {e}")
            raise e

    def delete_objects_by_customer_and_filename(self,customer_guid, filename):
        try:
            class_name=self.weaviate.generate_weaviate_class_name(customer_guid)
            response = self.client.batch.delete_objects(
                class_name=class_name,
                where={
                    "operator": "And",
                    "operands": [
                        {"path": ["customer_guid"], "operator": "Equal", "valueText": customer_guid},
                        {"path": ["filename"], "operator": "Equal", "valueText": filename}
                    ]
                }
            )
            if response.get("errors"):
                logger.error(f"Error deleting objects: {response['errors']}")
            else:
                logger.info(f"Successfully deleted all objects for customer_guid: {customer_guid} and filename: {filename}")

        except Exception as e:
            logger.error(f"Error executing batch deletion for customer_guid: {customer_guid} and filename: {filename} - {str(e)}")

if __name__ == "__main__":
    customer_guid = "837da906-13f0-48df-977a-ec20adbcd6d22"
    filename = "ast_sci_data_tables_sample.pdf"
    deletion_manager = DataDeletionManager()
    deletion_manager.delete_objects_by_customer_and_filename(customer_guid, filename)

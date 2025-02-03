import weaviate
import logging

# Configure Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DataDeletionManager:
    def __init__(self, client):
        self.client = client

    def get_class_name(self):
        return "SemanticChunkSearch"

    def delete_data(self, customer_guid: str, filename: str):
        try:
            class_name = self.get_class_name()

            # Query objects to delete using partial match for filename
            response = self.client.query.get(
                class_name, ["_additional { id }"]
            ).with_where({
                "operator": "And",
                "operands": [
                    {"path": ["customer_guid"], "operator": "Equal", "valueText": customer_guid},
                    { "path": ["filename"], "operator": "Equal", "valueText": filename }  # Partial match
                ]
            }).do()

            objects = response.get("data", {}).get("Get", {}).get(class_name, [])

            if not objects:
                logger.info(f"No data found for customer_guid: {customer_guid} and filename: {filename}")
                return

            # Delete each object
            for obj in objects:
                obj_id = obj["_additional"]["id"]
                self.client.data_object.delete(obj_id, class_name=class_name)
                logger.info(f"Deleted object {obj_id}")

            logger.info(f"Successfully deleted all chunks for customer_guid: {customer_guid} and filename: {filename}")
        except Exception as e:
            logger.error(f"Unexpected error while deleting data: {e}")


if __name__ == "__main__":
    try:
        weaviate_client = weaviate.Client("http://localhost:8080")
        deletion_manager = DataDeletionManager(weaviate_client)

        customer_guid = "e06d99222-c856-4171-b3af10"
        filename = "Full_Pitch.pptx"

        # Retrieve existing filenames for debugging
        response = weaviate_client.query.get(
            "SemanticChunkSearch", ["filename", "customer_guid"]
        ).with_where({
            "path": ["customer_guid"],
            "operator": "Equal",
            "valueText": customer_guid
        }).do()

        logger.info(f"Existing files for customer {customer_guid}: {response}")


        deletion_manager.delete_data(customer_guid, filename)
    except Exception as e:
        logger.error(f"Unexpected error in execution: {e}")

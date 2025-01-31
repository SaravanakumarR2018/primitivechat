import weaviate
import json
import logging

# Configure Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SchemaManager:
    def __init__(self, client):
        self.client = client

    def get_class_name(self):
        return "SemanticChunkSearch"

    def create_schema(self):
        try:
            class_name = self.get_class_name()
            existing_classes = self.client.schema.get().get("classes", [])
            if any(cls["class"] == class_name for cls in existing_classes):
                logger.info(f"Schema {class_name} already exists. Deleting it first...")
                self.client.schema.delete_class(class_name)

            schema = {
                "class": class_name,
                "description": "Schema for storing semantic chunks of a document.",
                "properties": [
                    {
                        "name": "text",
                        "dataType": ["text"],
                        "description": "The chunked text content from the document.",
                        "indexInverted": True
                    },
                    {
                        "name": "chunk_number",
                        "dataType": ["int"],
                        "description": "An object containing metadata like chunk number",
                        "indexInverted": False
                    },
                    {
                        "name": "page_numbers",
                        "dataType": ["int[]"],
                        "description": "An object containing metadata like page number",
                        "indexInverted": False
                    },
                    {
                        "name": "customer_guid",
                        "dataType": ["text"],
                        "description": "A unique identifier for the customer (namespace-like isolation).",
                        "indexInverted": True
                    },
                    {
                        "name": "filename",
                        "dataType": ["text"],
                        "description": "The name of the file this chunk originates from.",
                        "indexInverted": False
                    }
                ],
                "vectorizer": "text2vec-transformers"
            }
            self.client.schema.create_class(schema)
            logger.info(f"Schema {class_name} created successfully!")
        except Exception as e:
            logger.error(f"Unexpected error in schema creation: {e}")

class DataManager:
    def __init__(self, client):
        self.client = client

    def get_class_name(self):
        return "SemanticChunkSearch"

    def insert_data_from_file(self, customer_guid: str, file_path: str):
        try:
            class_name = self.get_class_name()
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, list):
                logger.error("Invalid JSON format: Expected a list of objects.")
            # Insert each data chunk
            for index, entry in enumerate(data):
                text = entry.get("text", "").strip()
                metadata = entry.get("metadata", {})

                chunk_data = {
                    "text": text,
                    "customer_guid": customer_guid,
                    "filename": metadata.get("filename", ""),
                    "chunk_number": metadata.get("chunk_number", index + 1),
                    "page_numbers": metadata.get("page_numbers", [])
                }
                self.client.data_object.create(chunk_data, class_name=class_name)
            logger.info(f"Data inserted for {customer_guid} successfully!")
        except Exception as e:
            logger.error(f"Unexpected error inserting data for {customer_guid}: {e}")

class WeaviateClient:
    def __init__(self, url: str):
        try:
            self.client = weaviate.Client(url)
            logger.info("Successfully connected to Weaviate.")
            self.schema_manager = SchemaManager(self.client)
            self.data_manager = DataManager(self.client)
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")

    def get_class_name(self):
        return "SemanticChunkSearch"

    def query_data(self, customer_guid: str):
        try:
            class_name = self.get_class_name()

            result = self.client.query.get(
                class_name, ["text", "chunk_number", "page_numbers", "filename", "customer_guid"]
            ).with_where({
                "path": ["customer_guid"],
                "operator": "Equal",
                "valueText": customer_guid
            }).do()

            logger.info(f"Query successful for {customer_guid}")
            logger.debug(json.dumps(result, indent=2))
            return result
        except Exception as e:
            logger.error(f"Unexpected error querying data for {customer_guid}: {e}")

    def semantic_search(self, customer_guid: str, concepts: list):
        try:
            class_name = self.get_class_name()

            result = self.client.query.get(
                class_name, ["text", "chunk_number", "page_numbers", "filename", "customer_guid"]
            ).with_where({
                "path": ["customer_guid"],
                "operator": "Equal",
                "valueText": customer_guid
            }).with_near_text({
                "concepts": concepts
            }).do()

            logger.info(f"Semantic search successful for {customer_guid} with concepts {concepts}")
            logger.debug(json.dumps(result, indent=2))
            return result
        except Exception as e:
            logger.error(f"Unexpected error in semantic search for {customer_guid}: {e}")

    def hybrid_search(self, customer_guid: str, query_text: str, concepts: list, alpha=0.5):
        try:
            class_name = self.get_class_name()
            result = self.client.query.get(
                class_name, ["text", "chunk_number", "page_numbers", "filename", "customer_guid"]
            ).with_where({
                "path": ["customer_guid"],
                "operator": "Equal",
                "valueText": customer_guid
            }).with_hybrid(
                query=query_text, alpha=alpha
            ).do()

            logger.info(f"Hybrid search successful for {customer_guid} with query '{query_text}'")
            logger.debug(json.dumps(result, indent=2))
            return result
        except Exception as e:
            logger.error(f"Unexpected error in hybrid search for {customer_guid}: {e}")

def main():
    customer_guid = "e06d99222-c856-4171-b3af8-78a5f97c988811"
    chunk_fileName = "/home/kabilan-a/Downloads/0.4all-mpnet-base-v2/Full_Pitch.pptx.0.4.all-mpnet-base-v2.txt"

    try:
        weaviate_client = WeaviateClient("http://localhost:8080")

        # Create schema
        weaviate_client.schema_manager.create_schema()

        # Insert data
        weaviate_client.data_manager.insert_data_from_file(customer_guid, chunk_fileName)

        # Query data
        weaviate_client.query_data(customer_guid)

        # Perform semantic search
        weaviate_client.semantic_search(customer_guid, ["Landscape and Regional Market Share"])

        # Perform hybrid search
        weaviate_client.hybrid_search(customer_guid, "Customer Support", ["Customer Support Market Projection"])

    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}")

if __name__ == "__main__":
    main()

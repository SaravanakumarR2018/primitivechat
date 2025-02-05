import logging
import json
from weaviate import Client
from sentence_transformers import SentenceTransformer
from src.backend.weaviate.weaviate_manager import WeaviateManager

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class WeaviateSearch:
    def __init__(self):
        try:
            self.client = Client(f"http://localhost:8080")
            logger.info("Successfully connected to Weaviate")

            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Successfully connected to Weaviate with external embedding model.")

            self.weaviate=WeaviateManager()

        except Exception as e:
            logger.error(f"Failed to initialize Weaviate connection: {e}")
            raise e

    def insert_data_from_file(self, customer_guid: str, file_path: str):

        try:
            class_names=self.weaviate.generate_weaviate_class_name(customer_guid)

            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("Invalid JSON format: Expected a list of objects.")

            for index, entry in enumerate(data):
                if "text" not in entry or "metadata" not in entry:
                    raise ValueError(f"Missing required fields in entry {index}")

                text = entry["text"].strip()
                metadata = entry["metadata"]

                if not metadata.get("filename"):
                    raise ValueError(f"Missing filename in metadata for entry {index}")

                embedding = self.model.encode(text).tolist()

                chunk_data = {
                    "text": text,
                    "customer_guid": customer_guid,
                    "filename": metadata["filename"],
                    "chunk_number": metadata["chunk_number"],
                    "page_numbers": metadata["page_numbers"]
                }

                self.client.data_object.create(chunk_data, class_name=class_names, vector=embedding)

            logger.info(f"Data inserted for {class_names} successfully with external embeddings!")
        except Exception as e:
            logger.error(f"Unexpected error inserting data for {customer_guid}: {e}")
            raise e

    def search_query(self, customer_guid, question, alpha=0.5):
        try:
            # Get the query vector for the question
            query_vector = self.model.encode(question).tolist()

            class_names=self.weaviate.generate_weaviate_class_name(customer_guid)

            # Perform the query with the provided vector
            result = self.client.query.get(
               class_names, ["text", "chunk_number", "page_numbers", "filename", "customer_guid"]
            ).with_hybrid(query=question, alpha=alpha, vector=query_vector).do()

            if not result or "data" not in result or "Get" not in result["data"]:
                raise ValueError(f"Unexpected search result format: {result}")

            if class_names not in result["data"]["Get"]:
                raise ValueError(f"No results found for customer: {class_names}")

            for obj in result["data"]["Get"][class_names]:
                if obj["customer_guid"] != customer_guid:
                    raise ValueError("Internal server error: Customer GUID mismatch detected!")

            logger.info(f"Search query successful for {customer_guid} with query '{question}'")
            return result

        except Exception as e:
            logger.error(f"Unexpected error in search query for {customer_guid}: {e}")
            raise e

class SearchProcessor:
    def __init__(self):
        self.weaviate_manager = WeaviateManager()
        self.search_manager = WeaviateSearch()

    def processor(self,customer_guid ,file_path):

        try:
            self.weaviate_manager.create_schema_per_customer_guid(customer_guid)

            self.search_manager.insert_data_from_file(customer_guid, file_path)

            # Perform search
            search_result = self.search_manager.search_query(customer_guid, "Automobile Land Speed Records")
            logger.info(f"Search Result: {json.dumps(search_result, indent=4)}")

        except Exception as e:
            logger.error(f"Unexpected error in main execution: {e}")

if __name__ == "__main__":
    customer_guid = "837da906-13f0-48df-977a-ec20adbcd6d22"
    file_path = "/home/kabilan-a/Downloads/0.4all-mpnet-base-v2/ast_sci_data_tables_sample.pdf.0.4.all-mpnet-base-v2.txt"
    search_process = SearchProcessor()
    search_process.processor(customer_guid,file_path)

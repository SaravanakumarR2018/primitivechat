import logging
import weaviate
from weaviate import Client
import os
import json
#from sentence_transformers import SentenceTransformer

#config logging
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeaviateManager:
    def __init__(self):

        try:
            weaviate_host = os.getenv('WEAVIATE_HOST','localhost')  # Get the Weaviate host from environment variable
            weaviate_port = os.getenv('WEAVIATE_PORT','9002')  # Get the Weaviate port from environment variable

            if not weaviate_host or not weaviate_port:
                raise ValueError("WEAVIATE_HOST and WEAVIATE_PORT must be set")

            self.client = Client(f"http://{weaviate_host}:{weaviate_port}")
            logger.info("Successfully connected to Weaviate")
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate connection: {e}")
            raise e

        self.model = self.load_model()

    def load_model(self, model_path="src/models/all-mini-llm-base-v2", model_name="sentence-transformers/all-MiniLM-L6-v2"):
        try:
            if os.path.exists(model_path) and os.listdir(model_path):
                logger.info(f"Loading model from local directory: {model_path}")
                return SentenceTransformer(model_path)
            else:
                logger.info("Model not found locally. Downloading from the internet...")
                model = SentenceTransformer(model_name)
                model.save(model_path)
                logger.info(f"Model downloaded and saved to: {model_path}")
                return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise e

    def generate_weaviate_class_name(self,customer_guid):

        return f"Customer_{customer_guid.replace('-', '_')}"

    def add_weaviate_customer_class(self,customer_guid):

        valid_class_name=self.generate_weaviate_class_name(customer_guid)
        try:

            schema=self.client.schema.get()
            class_names=[class_obj['class'] for class_obj in schema.get("classes",[])]

            if valid_class_name not in class_names:
                logger.debug(f"Creating Weaviate schema class:{valid_class_name}")
                class_obj={
                    "class":valid_class_name,
                    "description":"Schema for customer data",
                    "properties":[
                        {
                            "name": "message",
                            "dataType": ["text"],
                            "description":"Customer message data"
                        },
                        {
                            "name":"timestamp",
                            "dataType":["date"],
                            "description":"Timestamp of the message"
                        }
                    ]
                }
                self.client.schema.create_class(class_obj)
                logger.info(f"Weaviate class '{valid_class_name}' created successfully")
                return "Created Successfully"
            else:
                logger.info(f"Weaviate class'{valid_class_name}'already exists")
                return "schema already exists"
        except weaviate.exceptions.RequestError as e:
            logger.error(f"Error creating Weaviate schema for '{valid_class_name}:{e}")
            return f"Error:{e}"
        except Exception as e:
            logger.error(f"Unexpected error:{e}")
            return f"Unexpected error:{e}"

    def create_schema_per_customer_guid(self, customer_guid):
        try:
            class_name = self.generate_weaviate_class_name(customer_guid)

            # Check if the class exists using a Weaviate query
            class_exists = self.client.schema.exists(class_name)

            if not class_exists:
                schema_obj = {
                    "class": class_name,
                    "description": "Schema for storing semantic chunks of a customer" + customer_guid,
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
                            "indexInverted": True
                        }
                    ]
                }
                self.client.schema.create_class(schema_obj)
                logger.info(f"Schema '{class_name}' created successfully!")
            else:
                logger.info(f"Schema '{class_name}' already exists, skipping creation.")

        except Exception as e:
            logger.error(f"Unexpected error creating schema: {e}")

    def insert_data(self, customer_guid: str, file_path: str):
        try:
            # Ensure the class schema is created before inserting data
            class_names = self.generate_weaviate_class_name(customer_guid)
            self.create_schema_per_customer_guid(customer_guid)

            # Remove embeddings for the file and start fresh embedding
            filename = os.path.basename(file_path)
            self.delete_objects_by_customer_and_filename(customer_guid, filename)

            # Read and validate data
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError("Invalid JSON format: Expected a list of objects.")

            # Process all embeddings first
            texts = [entry["text"].strip() for entry in data if "text" in entry and "metadata" in entry]
            embeddings = self.model.encode(texts).tolist()

            for index, (entry, embedding) in enumerate(zip(data, embeddings)):
                metadata = entry["metadata"]
                if not metadata.get("filename"):
                    raise ValueError(f"Missing filename in metadata for entry {index}")

                chunk_data = {
                    "text": entry["text"].strip(),
                    "customer_guid": customer_guid,
                    "filename": metadata["filename"],
                    "chunk_number": metadata["chunk_number"],
                    "page_numbers": metadata["page_numbers"]
                }

                # Insert the data object into Weaviate
                self.client.data_object.create(
                    data_object=chunk_data,
                    class_name=class_names,
                    vector=embedding
                )

            logger.info(f"Data inserted for {class_names} successfully!")
        except Exception as e:
            logger.error(f"Unexpected error inserting data for {customer_guid}: {e}")
            raise e

    def search_query(self, customer_guid, question, alpha=0.5):
        try:
            # Get the query vector for the question
            query_vector = self.model.encode(question).tolist()

            class_names = self.generate_weaviate_class_name(customer_guid)

            # Perform the query with the provided vector
            result = self.client.query.get(
                class_names, ["text", "chunk_number", "page_numbers", "filename", "customer_guid"]
            ).with_near_vector({
                "vector": query_vector,
                "certainty": alpha
            }).do()

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

    def delete_objects_by_customer_and_filename(self, customer_guid, filename):
        try:
            class_name = self.generate_weaviate_class_name(customer_guid)

            # Define the filter to find objects to delete
            where_filter = {
                "operator": "And",
                "operands": [
                    {"path": ["customer_guid"], "operator": "Equal", "valueText": customer_guid},
                    {"path": ["filename"], "operator": "Equal", "valueText": filename}
                ]
            }
            # Fetch the objects to delete
            objects_to_delete = self.client.query.get(
                class_name=class_name,
                properties=["_additional {id}"]
            ).with_where(where_filter).do()

            # Check if objects were found
            if "data" not in objects_to_delete or "Get" not in objects_to_delete["data"]:
                logger.info("No objects found to delete.")
                return

            # Delete each object
            for obj in objects_to_delete["data"]["Get"][class_name]:
                object_id = obj["_additional"]["id"]
                self.client.data_object.delete(
                    uuid=object_id,
                    class_name=class_name
                )

            logger.info(f"Successfully deleted all objects for customer_guid: {customer_guid} and filename: {filename}")

        except Exception as e:
            logger.error(
                f"Error executing batch deletion for customer_guid: {customer_guid} and filename: {filename} - {str(e)}")


if __name__ == "__main__":
    customer_guid = "837da906-13f0-48df-977a-ec20ad"
    file_path = "/home/kabilan-a/Downloads/0.4all-mpnet-base-v2/ast_sci_data_tables_sample.pdf.0.4.all-mpnet-base-v2.txt"
    weaviate_manager = WeaviateManager()
    weaviate_manager.insert_data(customer_guid, file_path)
    search_result = weaviate_manager.search_query(customer_guid, "Automobile Land Speed Records")
    logger.info(f"Search Result: {json.dumps(search_result, indent=4)}")
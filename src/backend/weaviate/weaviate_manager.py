import logging
import weaviate
from weaviate import Client
import os

#config logging
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeaviateManager:
    def __init__(self):

        try:
            weaviate_host = os.getenv('WEAVIATE_HOST')  # Get the Weaviate host from environment variable
            weaviate_port = os.getenv('WEAVIATE_PORT')  # Get the Weaviate port from environment variable

            if not weaviate_host or not weaviate_port:
                raise ValueError("WEAVIATE_HOST and WEAVIATE_PORT must be set")

            self.client = Client(f"http://{weaviate_host}:{weaviate_port}")
            logger.info("Successfully connected to Weaviate")
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate connection: {e}")
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
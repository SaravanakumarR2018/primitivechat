import logging
import weaviate
from weaviate import Client

#config logging
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeaviateManager:
    def __init__(self):

        try:
            self.client=weaviate.Client("http://weaviate:8080")
            logger.info("Successfully connected to Weaviate")
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate connection: {e}")
            raise e

    def add_weaviate_customer_class(self,customer_guid):
    #Add a new customer class in Weaviate using customer_guid
        valid_class_name=f"Customer_{customer_guid.replace('-','_')}"
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
        except weaviate.exceptions.WeaviateException as e:
            logger.error(f"Error creating Weaviate schema for '{valid_class_name}:{e}")
            return f"Error:{e}"
        except Exception as e:
            logger.error(f"Unexpected error:{e}")
            return f"Unexpected error:{e}"
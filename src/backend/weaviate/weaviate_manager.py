import logging
import weaviate
from weaviate import Client
import os
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from src.backend.embedding.lib.download_and_upload_file import LocalFileDownloadAndUpload
from src.backend.lib.singleton_class import Singleton

from src.backend.lib.logging_config import get_primitivechat_logger


#config logging
logger = get_primitivechat_logger(__name__)

class WeaviateManager(metaclass=Singleton):
    def __init__(self):

        try:
            weaviate_host = os.getenv('WEAVIATE_HOST')  # Get the Weaviate host from environment variable
            weaviate_port = os.getenv('WEAVIATE_PORT')  # Get the Weaviate port from environment variable

            if not weaviate_host or not weaviate_port:
                raise ValueError("WEAVIATE_HOST and WEAVIATE_PORT must be set")

            self.client = Client(f"http://{weaviate_host}:{weaviate_port}")
            logger.info("Successfully connected to Weaviate")
            self.model = self.load_model()
            self.download = LocalFileDownloadAndUpload()
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate connection: {e}")
            raise e

    def load_model(self):
        try:
            model_dir = os.getenv('MODEL_DIR')  # Get the model path from env variable
            logger.info(f"Loading model from {model_dir}...")
            return SentenceTransformer(model_dir)  # Load model from saved path
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise e

    def generate_weaviate_class_name(self,customer_guid):

        return f"Customer_{customer_guid.replace('-', '_')}"

    def add_weaviate_customer_class(self,customer_guid):
        try:
            class_name = self.generate_weaviate_class_name(customer_guid)
            
            # Check if the class exists using a Weaviate query
            class_exists = self.client.schema.exists(class_name)
            if not class_exists:
                schema_obj = {
                    "class": class_name,
                    "description": "Schema for storing semantic chunks of a customer" + customer_guid,
                    "properties":[
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
                            "indexFilterable": True
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
                return "schema already exists"
        except weaviate.exceptions.RequestError as e:
            logger.error(f"Error creating Weaviate schema for '{class_name}:{e}")
            return f"Error:{e}"
        except Exception as e:
            logger.error(f"Unexpected error:{e}")
            return f"Unexpected error:{e}"

    def insert_data(self, customer_guid: str, file_path: str):
        try:
            # Ensure the class schema is created before inserting data
            class_names = self.generate_weaviate_class_name(customer_guid)

            # Download and save file locally
            local_path = self.download.download_and_save_file(customer_guid, file_path)

            filename = os.path.basename(file_path).replace(".chunked.txt", "")

            # Remove embeddings for the file and start fresh embedding
            self.delete_objects_by_customer_and_filename(customer_guid, filename)

            # Read and validate data
            with open(local_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError("Invalid JSON format: Expected a list of objects.")

            batch_size = 100
            self.client.batch.configure(batch_size=batch_size)

            # Process data in batches
            for i in range(0, len(data), batch_size):
                batch_data = data[i:i + batch_size]

                # Extract texts for the current batch
                texts = [entry["text"].strip() for entry in batch_data if "text" in entry and "metadata" in entry]
                embeddings = self.model.encode(texts).tolist()

                with self.client.batch as batch:
                    for entry, embedding in zip(batch_data, embeddings):
                        metadata = entry["metadata"]
                        if not metadata.get("filename"):
                            raise ValueError(f"Missing filename in metadata for entry {i + batch_data.index(entry)}")

                        chunk_data = {
                            "text": entry["text"].strip(),
                            "customer_guid": customer_guid,
                            "filename": metadata["filename"],
                            "chunk_number": metadata["chunk_number"],
                            "page_numbers": metadata["page_numbers"]
                        }

                        # Add the current chunk to the Weaviate batch
                        batch.add_data_object(chunk_data, class_name=class_names, vector=embedding)

                logger.info(f"Processed batch {batch_size} for {class_names}")

            logger.info(f"Bulk data inserted for {class_names} successfully!")
        except Exception as e:
            logger.error(f"Unexpected error inserting data for {customer_guid}: {e}")
            raise e

    def search_query(self, customer_guid, question, alpha=0.5):
        try:
            # Get the query vector for the question
            query_vector = self.model.encode(question).tolist()

            class_names=self.generate_weaviate_class_name(customer_guid)

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

    def search_query_advanced(self, customer_guid: str, question: str, top_k: int = 3, alpha: float = 0.5):
        """Return extended context for a question using page level retrieval.

        This method performs a hybrid search in Weaviate to obtain candidate
        chunks, re-ranks them using cosine similarity with the loaded embedding
        model and then expands the highest ranked chunks to their full page
        context (including neighbouring pages).  The combined context for the
        top ranked chunks is returned in a JSON serialisable format.
        """
        try:
            logger.info(f"[ADVANCED SEARCH] Query: '{question}' | customer_guid: {customer_guid} | top_k: {top_k} | alpha: {alpha}")
            query_embedding = self.model.encode(question)
            query_vector = query_embedding.tolist()
            class_name = self.generate_weaviate_class_name(customer_guid)

            raw_result = (
                self.client.query.get(
                    class_name,
                    ["text", "chunk_number", "page_numbers", "filename", "customer_guid"],
                )
                .with_hybrid(query=question, alpha=alpha, vector=query_vector)
                .with_additional(["distance"])
                .with_limit(max(top_k * 2, 10))
                .do()
            )

            if not raw_result or "data" not in raw_result or "Get" not in raw_result["data"]:
                logger.error(f"[ADVANCED SEARCH] Unexpected search result format: {raw_result}")
                raise ValueError(f"Unexpected search result format: {raw_result}")

            if class_name not in raw_result["data"]["Get"]:
                logger.warning(f"[ADVANCED SEARCH] No results found for customer: {class_name}")
                raise ValueError(f"No results found for customer: {class_name}")

            candidates = raw_result["data"]["Get"][class_name]
            logger.info(f"[ADVANCED SEARCH] Retrieved {len(candidates)} candidate chunks from Weaviate.")

            for obj in candidates:
                if obj.get("customer_guid") != customer_guid:
                    logger.error("[ADVANCED SEARCH] Customer GUID mismatch detected!")
                    raise ValueError("Internal server error: Customer GUID mismatch detected!")

            candidate_texts = [c.get("text", "") for c in candidates]
            candidate_vectors = self.model.encode(candidate_texts)
            scores = cosine_similarity([query_embedding], candidate_vectors)[0]

            for cand, score in zip(candidates, scores):
                cand["relevance_score"] = float(score)

            ranked = sorted(candidates, key=lambda x: x["relevance_score"], reverse=True)[:top_k]
            logger.info(f"[ADVANCED SEARCH] Selected top {top_k} ranked candidates for context expansion.")

            def fetch_page_chunks(pages, filename):
                where_filter = {
                    "operator": "And",
                    "operands": [
                        {"path": ["filename"], "operator": "Equal", "valueText": filename},
                        {"path": ["page_numbers"], "operator": "ContainsAny", "valueInt": list(pages)},
                    ],
                }

                page_res = self.client.query.get(
                    class_name,
                    ["text", "chunk_number", "page_numbers", "filename"],
                ).with_where(where_filter).with_limit(100).do()

                logger.info(f"page_res: {page_res}")

                if not isinstance(page_res, dict):
                    logger.error("page_res is not a dict: %s", page_res)
                    return []

                get_data = page_res.get("data", {})
                if not isinstance(get_data, dict):
                    logger.error("get_data is not a dict: %s", get_data)
                    return []

                get_class = get_data.get("Get", {})
                if not isinstance(get_class, dict):
                    logger.error("get_class is not a dict: %s", get_class)
                    return []

                chunks = get_class.get(class_name, [])
                if chunks is None:
                    logger.error("Fetched page_chunks is None, returning empty list.")
                    return []

                logger.debug(f"[ADVANCED SEARCH] fetch_page_chunks for filename={filename}, pages={pages} -> {len(chunks)} chunks.")
                return chunks

            def safe_min_page(chunk):
                pages = chunk.get("page_numbers", [])
                return min(pages) if pages else 0

            final_results = []
            for idx, item in enumerate(ranked, start=1):
                pages = set(item.get("page_numbers", []))
                neighbours = set()
                for p in pages:
                    if p > 1:
                        neighbours.add(p - 1)
                    neighbours.add(p)
                    neighbours.add(p + 1)

                logger.debug(f"[ADVANCED SEARCH] Expanding context for result {idx}: filename={item['filename']}, pages={sorted(neighbours)}")

                page_chunks = fetch_page_chunks(sorted(neighbours), item["filename"])

                if not isinstance(page_chunks, list):
                    logger.warning(f"[ADVANCED SEARCH] page_chunks for result {idx} is not a list. Skipping.")
                    continue

                try:
                    page_chunks.sort(key=lambda c: (safe_min_page(c), c.get("chunk_number", 0)))
                except Exception as sort_error:
                    logger.error(f"Error sorting page_chunks: {sort_error}")
                    continue

                combined_text = " ".join(ch.get("text", "") for ch in page_chunks if ch.get("text"))

                final_results.append(
                    {
                        "rank": idx,
                        "relevance_score": item["relevance_score"],
                        "filename": item["filename"],
                        "page_numbers": sorted(neighbours),
                        "text": combined_text,
                    }
                )

                logger.info(f"[ADVANCED SEARCH] Final result {idx}: filename={item['filename']}, pages={sorted(neighbours)}, score={item['relevance_score']}")

            logger.info(f"Advanced search query successful for {customer_guid} with query '{question}'")
            return {"results": final_results}

        except Exception as e:
            logger.error(f"Unexpected error in advanced search query for {customer_guid}: {e}")
            raise e

    def delete_objects_by_customer_and_filename(self,customer_guid, filename):
        try:
            class_name=self.generate_weaviate_class_name(customer_guid)
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
    customer_guid = "c94fdd86-65ec-413e-b3d5-c2c17be8989k"
    file_path = "/home/kabilan-a/Downloads/0.4all-mpnet-base-v2/ast_sci_data_tables_sample.pdf.0.4.all-mpnet-base-v2.txt"
    weaviate_manager = WeaviateManager()
    weaviate_manager.insert_data(customer_guid,file_path)
    search_result=weaviate_manager.search_query(customer_guid, "Automobile Land Speed Records")
    logger.info(f"Search Result: {json.dumps(search_result, indent=4)}")
